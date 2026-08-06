import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import EntityNotFoundException, ValidationException
from app.models.assignment import Assignment, AssignmentSubmission, AssignmentFeedback
from app.models.course import Enrollment
from app.models.document import FileUpload
from app.services.note_processing import DocumentParserService
from app.services.similarity import SimilarityService

logger = logging.getLogger(__name__)


DEFAULT_RUBRIC_CRITERIA = [
    {"name": "Concept Understanding", "max_score": 30.0, "description": "Demonstration of core concepts and subject matter mastery."},
    {"name": "Accuracy & Correctness", "max_score": 30.0, "description": "Precision, factual correctness, and proper calculations/proofs."},
    {"name": "Structure & Presentation", "max_score": 20.0, "description": "Clarity of organization, formatting, and logical flow."},
    {"name": "Writing & Grammar", "max_score": 20.0, "description": "Grammar, spelling, professional vocabulary, and readability."}
]


class RubricService:
    """
    Manages rubric parsing and structures LLM prompts for criteria-wise evaluation.
    """
    @staticmethod
    def get_effective_rubric(rubric_data: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Returns default rubric criteria if no custom rubric was attached."""
        if rubric_data and isinstance(rubric_data, list) and len(rubric_data) > 0:
            return rubric_data
        return DEFAULT_RUBRIC_CRITERIA


class GrammarService:
    """
    Analyzes document grammar quality, formatting, and structural organization.
    """
    @staticmethod
    def analyze_grammar_basic(text: str) -> Dict[str, Any]:
        """Performs quick heuristic analysis of text quality."""
        words = text.split()
        word_count = len(words)
        paragraphs = [p for p in text.split("\n\n") if p.strip()]
        
        return {
            "word_count": word_count,
            "paragraph_count": len(paragraphs),
            "readability_status": "Good" if word_count > 50 else "Short Submission",
            "formatting_review": "Properly structured into paragraphs." if len(paragraphs) > 1 else "Consider dividing into structured sections."
        }


class EvaluationService:
    """
    Orchestrates complete AI assignment evaluation pipeline:
    Text Extraction -> Similarity Check -> Gemini Rubric Evaluation -> Feedback Compilation.
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        self.parser_service = DocumentParserService()
        self.similarity_service = SimilarityService()

    async def extract_submission_text(self, submission: AssignmentSubmission) -> str:
        """Extracts text from uploaded file or submitted_text property."""
        if submission.submitted_text and len(submission.submitted_text.strip()) > 0:
            return submission.submitted_text

        if submission.file_upload_id:
            stmt = select(FileUpload).filter(FileUpload.id == submission.file_upload_id)
            res = await self.db.execute(stmt)
            file_upload = res.scalars().first()
            
            if file_upload and os.path.exists(file_upload.file_path):
                return self.parser_service.extract_text(file_upload.file_path, file_upload.mime_type)

        return ""

    async def evaluate_submission(self, submission_id: UUID) -> AssignmentFeedback:
        """Runs complete AI evaluation pipeline for a submission."""
        # 1. Fetch submission and assignment
        stmt = select(AssignmentSubmission).filter(AssignmentSubmission.id == submission_id)
        res = await self.db.execute(stmt)
        sub = res.scalars().first()
        if not sub:
            raise EntityNotFoundException("Assignment submission not found.")

        sub.processing_status = "processing"
        self.db.add(sub)
        await self.db.flush()

        asgn_stmt = select(Assignment).filter(Assignment.id == sub.assignment_id)
        asgn_res = await self.db.execute(asgn_stmt)
        assignment = asgn_res.scalars().first()
        if not assignment:
            raise EntityNotFoundException("Associated assignment not found.")

        # 2. Extract submitted text
        text_content = await self.extract_submission_text(sub)
        if not text_content:
            text_content = "[Empty Submission Text]"

        # Update submission's submitted_text if not populated
        if not sub.submitted_text and text_content != "[Empty Submission Text]":
            sub.submitted_text = text_content[:5000]  # Store preview

        # 3. Perform Similarity Analysis
        sim_report = await self.similarity_service.analyze_submission(
            text=text_content,
            assignment_id=assignment.id,
            current_submission_id=sub.id,
            db=self.db
        )
        plagiarism_score = sim_report.get("plagiarism_score", 0.0)

        # 4. Get effective Rubric
        rubric = RubricService.get_effective_rubric(assignment.rubric)
        grammar_analysis = GrammarService.analyze_grammar_basic(text_content)

        # 5. Execute Gemini LLM Evaluation
        eval_result = await self._call_gemini_evaluator(
            text=text_content,
            assignment_title=assignment.title,
            instructions=assignment.instructions or "",
            max_points=assignment.max_points,
            rubric=rubric
        )

        # Calculate total AI score
        proposed_ai_score = float(eval_result.get("total_score", assignment.max_points * 0.85))

        # 6. Save or update AssignmentFeedback record
        feedback_stmt = select(AssignmentFeedback).filter(AssignmentFeedback.submission_id == sub.id)
        feedback_res = await self.db.execute(feedback_stmt)
        feedback = feedback_res.scalars().first()

        if not feedback:
            feedback = AssignmentFeedback(
                submission_id=sub.id,
                feedback_text=eval_result.get("summary_feedback", "AI evaluation completed successfully."),
                grade_score=proposed_ai_score,  # Initial proposed grade
                ai_score=proposed_ai_score,
                final_score=None,
                is_approved=False,
                status="pending_teacher_review",
                plagiarism_score=plagiarism_score,
                rubric_evaluation=eval_result.get("rubric_evaluations", []),
                strengths=eval_result.get("strengths", []),
                weaknesses=eval_result.get("weaknesses", []),
                grammar_feedback=grammar_analysis,
                suggestions=eval_result.get("suggestions", []),
                similarity_report=sim_report
            )
            self.db.add(feedback)
        else:
            feedback.feedback_text = eval_result.get("summary_feedback", "AI evaluation updated.")
            feedback.grade_score = proposed_ai_score
            feedback.ai_score = proposed_ai_score
            feedback.plagiarism_score = plagiarism_score
            feedback.rubric_evaluation = eval_result.get("rubric_evaluations", [])
            feedback.strengths = eval_result.get("strengths", [])
            feedback.weaknesses = eval_result.get("weaknesses", [])
            feedback.grammar_feedback = grammar_analysis
            feedback.suggestions = eval_result.get("suggestions", [])
            feedback.similarity_report = sim_report
            self.db.add(feedback)

        # Update submission status
        sub.processing_status = "evaluated"
        if sub.submitted_at and assignment.due_date and sub.submitted_at > assignment.due_date:
            sub.status = "late"

        self.db.add(sub)
        await self.db.commit()
        await self.db.refresh(feedback)
        
        logger.info(f"AI Evaluation completed for submission {sub.id}: Score={proposed_ai_score}/{assignment.max_points}")
        return feedback

    async def _call_gemini_evaluator(
        self, 
        text: str, 
        assignment_title: str, 
        instructions: str, 
        max_points: float, 
        rubric: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calls Gemini API to evaluate assignment text against rubric."""
        api_key = settings.GOOGLE_API_KEY
        is_mock = (not api_key or api_key.startswith("mock")) and os.getenv("TESTING") != "True"

        if is_mock:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=503,
                detail="AI assignment evaluation service is currently unavailable. Please configure a valid API key."
            )

        try:
            from google import genai
            client = genai.Client(api_key=api_key)

            prompt = (
                f"You are an expert academic professor grading an assignment titled '{assignment_title}'.\n"
                f"Assignment Instructions: {instructions}\n"
                f"Maximum Assignment Marks: {max_points}\n\n"
                f"Evaluation Rubric Criteria (JSON):\n{json.dumps(rubric, indent=2)}\n\n"
                f"Student Submitted Text:\n{text[:4000]}\n\n"
                "Provide a complete evaluation strictly in JSON format with key fields:\n"
                "{\n"
                "  \"total_score\": float,\n"
                "  \"summary_feedback\": \"string\",\n"
                "  \"rubric_evaluations\": [ {\"criterion_name\": \"string\", \"assigned_score\": float, \"max_score\": float, \"comments\": \"string\"} ],\n"
                "  \"strengths\": [\"string\"],\n"
                "  \"weaknesses\": [\"string\"],\n"
                "  \"suggestions\": [\"string\"]\n"
                "}\n"
                "Do NOT include markdown backticks around the output."
            )

            resp = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            
            cleaned_text = resp.text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]

            return json.loads(cleaned_text.strip())
        except Exception as e:
            logger.error(f"Error calling live Gemini evaluator: {str(e)}")
            from fastapi import HTTPException
            raise HTTPException(
                status_code=503,
                detail="AI assignment evaluation service is currently unavailable. Please try again later."
            )


class AnalyticsService:
    """
    Computes assignment statistics, submission rates, score distribution, and rubric performance.
    """
    @staticmethod
    async def get_assignment_analytics(assignment_id: UUID, db: AsyncSession) -> Dict[str, Any]:
        """Calculates performance analytics for a single assignment."""
        stmt = select(Assignment).filter(Assignment.id == assignment_id)
        res = await db.execute(stmt)
        asgn = res.scalars().first()
        if not asgn:
            raise EntityNotFoundException("Assignment not found.")

        # Count total enrolled students in course
        enroll_stmt = select(func.count(Enrollment.id)).filter(Enrollment.course_id == asgn.course_id)
        enroll_res = await db.execute(enroll_stmt)
        total_students = enroll_res.scalar() or 0

        # Count submissions and unique student submitters
        sub_stmt = select(AssignmentSubmission).filter(AssignmentSubmission.assignment_id == assignment_id)
        sub_res = await db.execute(sub_stmt)
        submissions = sub_res.scalars().all()
        submissions_count = len(submissions)

        submitted_students_count = len(set(s.student_id for s in submissions))
        submission_rate = round((submitted_students_count / total_students * 100.0) if total_students > 0 else 0.0, 2)
        late_count = sum(1 for s in submissions if s.status == "late")

        # Fetch feedback records
        sub_ids = [s.id for s in submissions]
        feedbacks = []
        if sub_ids:
            fb_stmt = select(AssignmentFeedback).filter(AssignmentFeedback.submission_id.in_(sub_ids))
            fb_res = await db.execute(fb_stmt)
            feedbacks = fb_res.scalars().all()

        pending_reviews = sum(1 for f in feedbacks if not f.is_approved)
        scores = [f.final_score if f.final_score is not None else f.grade_score for f in feedbacks]

        avg_score = round(sum(scores) / len(scores), 2) if scores else None
        high_score = max(scores) if scores else None
        low_score = min(scores) if scores else None

        # Compute rubric performance per criterion
        criterion_totals = {}
        criterion_counts = {}
        for f in feedbacks:
            if f.rubric_evaluation:
                for item in f.rubric_evaluation:
                    name = item.get("criterion_name")
                    score = item.get("assigned_score", 0.0)
                    if name:
                        criterion_totals[name] = criterion_totals.get(name, 0.0) + score
                        criterion_counts[name] = criterion_counts.get(name, 0) + 1

        rubric_perf = {}
        for name, total in criterion_totals.items():
            count = criterion_counts.get(name, 1)
            rubric_perf[name] = round(total / count, 2)

        return {
            "assignment_id": str(assignment_id),
            "total_students": total_students,
            "submissions_count": submissions_count,
            "submission_rate": submission_rate,
            "average_score": avg_score,
            "highest_score": high_score,
            "lowest_score": low_score,
            "late_submissions_count": late_count,
            "pending_reviews_count": pending_reviews,
            "rubric_performance": rubric_perf
        }
