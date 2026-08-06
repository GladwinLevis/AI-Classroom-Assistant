import os
import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Path, Body, status
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ValidationException, EntityNotFoundException, AuthException
from app.core.security import get_current_active_user
from app.models.user import User, StudentProfile
from app.models.quiz import Quiz, QuizQuestion, QuizAttempt, QuizAnswer, QuestionBank
from app.schemas.quiz import (
    QuizGenerateRequest,
    QuizCreate,
    QuizUpdate,
    QuizResponse,
    QuizSubmitRequest,
    QuizSaveProgressRequest,
    QuizAttemptResponse,
    SubjectiveOverrideRequest,
    AdaptiveRecommendationResponse,
    LeaderboardEntry,
    QuizAnalyticsResponse,
    QuestionBankResponse
)
from app.services.quiz_service import (
    QuizGenerationService,
    EvaluationService,
    AdaptiveLearningService,
    AnalyticsService,
    LeaderboardService
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ------------------------------------------------------------------------------
# STATIC & SEARCH ENDPOINTS (MUST BE BEFORE /{id})
# ------------------------------------------------------------------------------

@router.get("", response_model=List[QuizResponse])
@router.get("/", response_model=List[QuizResponse])
async def list_quizzes(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Lists quizzes created by or available to the current user."""
    stmt = (
        select(Quiz)
        .options(selectinload(Quiz.questions))
        .filter(Quiz.is_deleted == False)
        .order_by(Quiz.created_at.desc())
    )
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("/adaptive-recommendations", response_model=AdaptiveRecommendationResponse)
async def get_adaptive_learning_recommendations(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns adaptive learning recommendations and weak area suggestions for current student."""
    s_stmt = select(StudentProfile).filter(StudentProfile.user_id == current_user.id)
    s_res = await db.execute(s_stmt)
    student = s_res.scalars().first()
    if not student:
        raise AuthException("Only students can fetch adaptive recommendations.")

    return await AdaptiveLearningService.get_adaptive_recommendations(student.id, db)


@router.get("/question-bank/search", response_model=List[QuestionBankResponse])
async def search_question_bank(
    topic: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    blooms_level: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Searches and filters global question bank."""
    stmt = select(QuestionBank).filter(QuestionBank.is_deleted == False)
    if topic:
        stmt = stmt.filter(QuestionBank.topic.ilike(f"%{topic}%"))
    if difficulty:
        stmt = stmt.filter(QuestionBank.difficulty == difficulty)
    if blooms_level:
        stmt = stmt.filter(QuestionBank.blooms_level == blooms_level)

    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("/course/{course_id}", response_model=List[QuizResponse])
async def list_course_quizzes(
    course_id: UUID = Path(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Lists all quizzes for a specific course."""
    stmt = (
        select(Quiz)
        .options(selectinload(Quiz.questions))
        .filter(Quiz.course_id == course_id, Quiz.is_deleted == False)
        .order_by(Quiz.created_at.desc())
    )
    res = await db.execute(stmt)
    return res.scalars().all()


# ------------------------------------------------------------------------------
# QUIZ GENERATION & CREATION ENDPOINTS
# ------------------------------------------------------------------------------

@router.post("/generate", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
async def generate_quiz_ai(
    payload: QuizGenerateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Triggers AI quiz generator from notes documents, AI summaries, or topics."""
    svc = QuizGenerationService(db)
    quiz = await svc.generate_quiz_from_source(
        creator_id=current_user.id,
        notes_id=payload.notes_id,
        topic=payload.topic,
        num_questions=payload.num_questions,
        difficulty=payload.difficulty,
        blooms_level=payload.blooms_level,
        question_types=payload.question_types,
        course_id=payload.course_id
    )

    stmt = select(Quiz).options(selectinload(Quiz.questions)).filter(Quiz.id == quiz.id)
    res = await db.execute(stmt)
    return res.scalars().first()


@router.post("/", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
async def create_quiz_manual(
    payload: QuizCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Manually creates a new quiz entity (Teacher/Admin)."""
    quiz = Quiz(
        title=payload.title,
        description=payload.description,
        duration_minutes=payload.duration_minutes,
        difficulty=payload.difficulty,
        blooms_level=payload.blooms_level,
        negative_marking=payload.negative_marking,
        passing_percentage=payload.passing_percentage,
        max_attempts=payload.max_attempts,
        randomize_questions=payload.randomize_questions,
        randomize_options=payload.randomize_options,
        topic=payload.topic,
        course_id=payload.course_id,
        creator_id=current_user.id,
        is_published=False
    )
    db.add(quiz)
    await db.flush()

    if payload.questions:
        for q in payload.questions:
            q_ent = QuizQuestion(
                quiz_id=quiz.id,
                question_text=q.question_text,
                question_type=q.question_type,
                options=q.options,
                correct_answer=q.correct_answer,
                explanation=q.explanation,
                points=q.points,
                difficulty=q.difficulty,
                blooms_level=q.blooms_level,
                topic=q.topic,
                estimated_time_seconds=q.estimated_time_seconds,
                related_concept=q.related_concept,
                recommended_revision_topic=q.recommended_revision_topic
            )
            db.add(q_ent)

    await db.commit()

    stmt = select(Quiz).options(selectinload(Quiz.questions)).filter(Quiz.id == quiz.id)
    res = await db.execute(stmt)
    return res.scalars().first()


# ------------------------------------------------------------------------------
# PARAMETERIZED QUIZ ID ENDPOINTS
# ------------------------------------------------------------------------------

@router.get("/{id}", response_model=QuizResponse)
async def get_quiz_details(
    id: UUID = Path(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves quiz details with questions."""
    stmt = select(Quiz).options(selectinload(Quiz.questions)).filter(Quiz.id == id, Quiz.is_deleted == False)
    res = await db.execute(stmt)
    quiz = res.scalars().first()
    if not quiz:
        raise EntityNotFoundException("Quiz not found.")
    return quiz


@router.put("/{id}", response_model=QuizResponse)
async def update_quiz(
    id: UUID = Path(...),
    payload: QuizUpdate = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Updates quiz configurations."""
    stmt = select(Quiz).options(selectinload(Quiz.questions)).filter(Quiz.id == id, Quiz.is_deleted == False)
    res = await db.execute(stmt)
    quiz = res.scalars().first()
    if not quiz:
        raise EntityNotFoundException("Quiz not found.")

    if payload.title is not None:
        quiz.title = payload.title
    if payload.description is not None:
        quiz.description = payload.description
    if payload.duration_minutes is not None:
        quiz.duration_minutes = payload.duration_minutes
    if payload.is_published is not None:
        quiz.is_published = payload.is_published
    if payload.difficulty is not None:
        quiz.difficulty = payload.difficulty
    if payload.passing_percentage is not None:
        quiz.passing_percentage = payload.passing_percentage

    db.add(quiz)
    await db.commit()
    
    stmt = select(Quiz).options(selectinload(Quiz.questions)).filter(Quiz.id == id)
    res = await db.execute(stmt)
    return res.scalars().first()


@router.post("/{id}/publish", response_model=QuizResponse)
async def publish_quiz(
    id: UUID = Path(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Publishes a quiz for students."""
    stmt = select(Quiz).options(selectinload(Quiz.questions)).filter(Quiz.id == id, Quiz.is_deleted == False)
    res = await db.execute(stmt)
    quiz = res.scalars().first()
    if not quiz:
        raise EntityNotFoundException("Quiz not found.")

    quiz.is_published = True
    db.add(quiz)
    await db.commit()
    
    stmt = select(Quiz).options(selectinload(Quiz.questions)).filter(Quiz.id == id)
    res = await db.execute(stmt)
    return res.scalars().first()


@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_quiz(
    id: UUID = Path(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Soft deletes a quiz."""
    stmt = select(Quiz).filter(Quiz.id == id, Quiz.is_deleted == False)
    res = await db.execute(stmt)
    quiz = res.scalars().first()
    if not quiz:
        raise EntityNotFoundException("Quiz not found.")

    quiz.is_deleted = True
    db.add(quiz)
    await db.commit()
    return {"success": True, "message": "Quiz deleted successfully."}


@router.get("/{id}/analytics", response_model=QuizAnalyticsResponse)
async def get_quiz_analytics(
    id: UUID = Path(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Computes quiz performance analytics."""
    return await AnalyticsService.get_quiz_analytics(id, db)


@router.get("/{id}/leaderboard", response_model=List[LeaderboardEntry])
async def get_quiz_leaderboard(
    id: UUID = Path(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns student score rankings for a quiz."""
    return await LeaderboardService.get_quiz_leaderboard(id, db)


# ------------------------------------------------------------------------------
# STUDENT ATTEMPT ENDPOINTS
# ------------------------------------------------------------------------------

@router.post("/{id}/start", response_model=QuizAttemptResponse, status_code=status.HTTP_201_CREATED)
async def start_quiz_attempt(
    id: UUID = Path(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Starts a new student quiz attempt."""
    s_stmt = select(StudentProfile).filter(StudentProfile.user_id == current_user.id)
    s_res = await db.execute(s_stmt)
    student = s_res.scalars().first()
    if not student:
        raise AuthException("Only enrolled students can attempt quizzes.")

    quiz_stmt = select(Quiz).filter(Quiz.id == id, Quiz.is_deleted == False)
    quiz_res = await db.execute(quiz_stmt)
    quiz = quiz_res.scalars().first()
    if not quiz:
        raise EntityNotFoundException("Quiz not found.")

    # Check max attempts limit
    count_stmt = select(func.count(QuizAttempt.id)).filter(QuizAttempt.quiz_id == id, QuizAttempt.student_id == student.id)
    count_res = await db.execute(count_stmt)
    attempt_count = count_res.scalar() or 0

    if attempt_count >= quiz.max_attempts:
        raise ValidationException(f"Maximum attempt limit ({quiz.max_attempts}) reached for this quiz.")

    attempt = QuizAttempt(
        quiz_id=id,
        student_id=student.id,
        status="in_progress"
    )
    db.add(attempt)
    await db.commit()
    
    stmt = select(QuizAttempt).options(selectinload(QuizAttempt.answers)).filter(QuizAttempt.id == attempt.id)
    res = await db.execute(stmt)
    return res.scalars().first()


@router.post("/attempt/{attempt_id}/save", response_model=QuizAttemptResponse)
async def save_quiz_progress(
    attempt_id: UUID = Path(...),
    payload: QuizSaveProgressRequest = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Auto-saves student quiz progress during active attempts."""
    stmt = select(QuizAttempt).options(selectinload(QuizAttempt.answers)).filter(QuizAttempt.id == attempt_id)
    res = await db.execute(stmt)
    attempt = res.scalars().first()
    if not attempt:
        raise EntityNotFoundException("Quiz attempt not found.")

    attempt.progress_data = payload.progress_data
    db.add(attempt)
    await db.commit()

    res = await db.execute(stmt)
    return res.scalars().first()


@router.post("/attempt/{attempt_id}/submit", response_model=QuizAttemptResponse)
async def submit_quiz_attempt(
    attempt_id: UUID = Path(...),
    payload: QuizSubmitRequest = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Submits student quiz attempt and triggers instant evaluation."""
    answers_dict = [a.dict() for a in payload.answers]
    eval_service = EvaluationService(db)
    attempt = await eval_service.evaluate_attempt(attempt_id, answers_dict)

    stmt = select(QuizAttempt).options(selectinload(QuizAttempt.answers)).filter(QuizAttempt.id == attempt.id)
    res = await db.execute(stmt)
    return res.scalars().first()


@router.get("/attempt/{attempt_id}/results", response_model=QuizAttemptResponse)
async def get_quiz_attempt_results(
    attempt_id: UUID = Path(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves detailed attempt results with explanations and feedback."""
    stmt = select(QuizAttempt).options(selectinload(QuizAttempt.answers)).filter(QuizAttempt.id == attempt_id)
    res = await db.execute(stmt)
    attempt = res.scalars().first()
    if not attempt:
        raise EntityNotFoundException("Quiz attempt not found.")
    return attempt


# ------------------------------------------------------------------------------
# TEACHER EVALUATION & OVERRIDE ENDPOINTS
# ------------------------------------------------------------------------------

@router.post("/attempt/{attempt_id}/evaluate-subjective", response_model=QuizAttemptResponse)
async def override_subjective_score(
    attempt_id: UUID = Path(...),
    payload: SubjectiveOverrideRequest = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Teacher reviews and overrides subjective question score."""
    is_staff = any(r.name in ["teacher", "admin"] for r in current_user.roles)
    if not is_staff:
        raise AuthException("Access denied. Only teachers can override scores.")

    ans_stmt = select(QuizAnswer).filter(QuizAnswer.attempt_id == attempt_id, QuizAnswer.question_id == payload.question_id)
    ans_res = await db.execute(ans_stmt)
    qa = ans_res.scalars().first()
    if not qa:
        raise EntityNotFoundException("Quiz answer record not found.")

    old_points = qa.points_awarded
    qa.teacher_override_score = payload.override_score
    qa.points_awarded = payload.override_score
    qa.evaluated_by_ai = False
    if payload.teacher_comments:
        qa.feedback_comments = payload.teacher_comments

    db.add(qa)

    # Recalculate total attempt score
    att_stmt = select(QuizAttempt).filter(QuizAttempt.id == attempt_id)
    att_res = await db.execute(att_stmt)
    attempt = att_res.scalars().first()
    if attempt:
        attempt.score = max(0.0, (attempt.score or 0.0) - old_points + payload.override_score)
        db.add(attempt)

    await db.commit()

    stmt = select(QuizAttempt).options(selectinload(QuizAttempt.answers)).filter(QuizAttempt.id == attempt_id)
    res = await db.execute(stmt)
    return res.scalars().first()
