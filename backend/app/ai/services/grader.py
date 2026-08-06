import logging
from typing import Dict, Any
from app.ai.llm import get_llm

logger = logging.getLogger(__name__)


class AssignmentGrader:
    """
    AssignmentGrader uses the LLM to grade student assignment text or files
    against descriptions and guidelines.
    """
    def __init__(self):
        self.llm = get_llm()

    async def grade_submission(
        self,
        assignment_title: str,
        assignment_description: str,
        submission_text: str
    ) -> Dict[str, Any]:
        """
        Grades submitted text and generates feedback.
        Returns a dictionary with score, feedback remarks, and suggestions.
        """
        logger.info(f"Grading submission for assignment: {assignment_title}")
        
        prompt = (
            f"You are an expert educator. Grade the student's submission below based on the assignment description.\n\n"
            f"Assignment: {assignment_title}\n"
            f"Description: {assignment_description}\n"
            f"Student Submission:\n{submission_text}\n\n"
            f"Provide a structured evaluation in raw text format containing:\n"
            f"1. Score (out of 100)\n"
            f"2. Grammatical evaluation\n"
            f"3. Concrete constructive feedback points."
        )
        
        response = await self.llm.ainvoke(prompt)
        feedback_text = str(response.content)
        
        # Simple parser placeholder: real logic will structure JSON response
        # Here we return a skeleton dictionary mapping.
        return {
            "score": 85.0,  # Mock default score
            "feedback": feedback_text,
            "plagiarism_score": 0.05  # Mock plagiarism rating
        }
