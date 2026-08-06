import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import ForeignKey, String, Text, Integer, JSON, DateTime, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


class Quiz(BaseModel):
    """
    SQLAlchemy Model representing academic quizzes.
    """
    __tablename__ = "quizzes"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer(), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(30), default="mixed", nullable=False)  # easy, medium, hard, mixed
    blooms_level: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # List of selected Bloom's levels
    negative_marking: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    passing_percentage: Mapped[float] = mapped_column(Float, default=40.0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    randomize_questions: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    randomize_options: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    topic: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    course_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    creator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    source_notes_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("notes.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Relationships
    course: Mapped[Optional["Course"]] = relationship("Course", back_populates="quizzes")
    creator: Mapped["User"] = relationship("User", back_populates="quizzes")
    source_notes: Mapped[Optional["Notes"]] = relationship("Notes")
    questions: Mapped[List["QuizQuestion"]] = relationship(
        "QuizQuestion",
        back_populates="quiz",
        cascade="all, delete-orphan"
    )
    attempts: Mapped[List["QuizAttempt"]] = relationship(
        "QuizAttempt",
        back_populates="quiz",
        cascade="all, delete-orphan"
    )


class QuizQuestion(BaseModel):
    """
    SQLAlchemy Model representing individual questions within a quiz.
    """
    __tablename__ = "quiz_questions"

    question_text: Mapped[str] = mapped_column(Text(), nullable=False)
    question_type: Mapped[str] = mapped_column(String(30), default="mcq")  # mcq, true_false, fill_in_blank, matching, short_answer, descriptive, case_study
    options: Mapped[Optional[list]] = mapped_column(JSON(), nullable=True)  # List of string options or dicts
    correct_answer: Mapped[str] = mapped_column(String(255), nullable=False)
    explanation: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    points: Mapped[float] = mapped_column(Float(), default=1.0, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(30), default="medium", nullable=False)
    blooms_level: Mapped[str] = mapped_column(String(50), default="Remember", nullable=False)
    topic: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    estimated_time_seconds: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    related_concept: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    recommended_revision_topic: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)

    quiz_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Relationships
    quiz: Mapped[Quiz] = relationship(Quiz, back_populates="questions")
    answers: Mapped[List["QuizAnswer"]] = relationship(
        "QuizAnswer",
        back_populates="question",
        cascade="all, delete-orphan"
    )


class QuizAttempt(BaseModel):
    """
    SQLAlchemy Model representing student attempts on quizzes.
    """
    __tablename__ = "quiz_attempts"

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    score: Mapped[Optional[float]] = mapped_column(Float(), nullable=True)
    total_points: Mapped[float] = mapped_column(Float(), default=0.0, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="in_progress", nullable=False)  # in_progress, submitted, evaluated
    progress_data: Mapped[Optional[dict]] = mapped_column(JSON(), nullable=True)  # Auto-save progress
    
    quiz_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Relationships
    quiz: Mapped[Quiz] = relationship(Quiz, back_populates="attempts")
    student: Mapped["StudentProfile"] = relationship("StudentProfile", back_populates="quiz_attempts")
    answers: Mapped[List["QuizAnswer"]] = relationship(
        "QuizAnswer",
        back_populates="attempt",
        cascade="all, delete-orphan"
    )


class QuizAnswer(BaseModel):
    """
    SQLAlchemy Model representing individual answers submitted for each question in an attempt.
    """
    __tablename__ = "quiz_answers"

    selected_option: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    provided_answer: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    is_correct: Mapped[bool] = mapped_column(default=False, nullable=False)
    points_awarded: Mapped[float] = mapped_column(Float(), default=0.0, nullable=False)
    feedback_comments: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    teacher_override_score: Mapped[Optional[float]] = mapped_column(Float(), nullable=True)
    evaluated_by_ai: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    attempt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quiz_attempts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quiz_questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Relationships
    attempt: Mapped[QuizAttempt] = relationship(QuizAttempt, back_populates="answers")
    question: Mapped[QuizQuestion] = relationship(QuizQuestion, back_populates="answers")


class QuestionBank(BaseModel):
    """
    SQLAlchemy Model representing global question bank for searching and reusing questions.
    """
    __tablename__ = "question_bank"

    question_text: Mapped[str] = mapped_column(Text(), nullable=False)
    question_type: Mapped[str] = mapped_column(String(30), default="mcq", nullable=False)
    options: Mapped[Optional[list]] = mapped_column(JSON(), nullable=True)
    correct_answer: Mapped[str] = mapped_column(String(255), nullable=False)
    explanation: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    points: Mapped[float] = mapped_column(Float(), default=1.0, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(30), default="medium", nullable=False)
    blooms_level: Mapped[str] = mapped_column(String(50), default="Remember", nullable=False)
    subject: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    topic: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    creator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
