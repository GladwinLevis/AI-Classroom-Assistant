from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class QuizGenerateRequest(BaseModel):
    notes_id: Optional[UUID] = None
    topic: Optional[str] = None
    num_questions: int = Field(5, ge=1, le=50)
    difficulty: str = "mixed"  # easy, medium, hard, mixed
    blooms_level: Optional[List[str]] = Field(default_factory=lambda: ["Remember", "Understand"])
    question_types: Optional[List[str]] = Field(default_factory=lambda: ["mcq", "true_false", "short_answer"])
    course_id: Optional[UUID] = None


class QuestionBase(BaseModel):
    question_text: str = Field(..., min_length=1)
    question_type: str = "mcq"  # mcq, true_false, fill_in_blank, matching, short_answer, descriptive, case_study
    options: Optional[Any] = None
    correct_answer: str
    explanation: Optional[str] = None
    points: float = Field(1.0, gt=0)
    difficulty: str = "medium"
    blooms_level: str = "Remember"
    topic: Optional[str] = None
    estimated_time_seconds: int = 60
    related_concept: Optional[str] = None
    recommended_revision_topic: Optional[str] = None


class QuestionCreate(QuestionBase):
    pass


class QuestionResponse(QuestionBase):
    id: UUID
    quiz_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QuizBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    difficulty: str = "mixed"
    blooms_level: Optional[List[str]] = None
    negative_marking: float = 0.0
    passing_percentage: float = 40.0
    max_attempts: int = 1
    randomize_questions: bool = False
    randomize_options: bool = False
    topic: Optional[str] = None


class QuizCreate(QuizBase):
    course_id: Optional[UUID] = None
    questions: Optional[List[QuestionCreate]] = None


class QuizUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    is_published: Optional[bool] = None
    difficulty: Optional[str] = None
    passing_percentage: Optional[float] = None


class QuizResponse(QuizBase):
    id: UUID
    course_id: Optional[UUID] = None
    creator_id: UUID
    is_published: bool
    questions: List[QuestionResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SingleAnswerSubmit(BaseModel):
    question_id: UUID
    selected_option: Optional[str] = None
    provided_answer: Optional[str] = None


class QuizSubmitRequest(BaseModel):
    answers: List[SingleAnswerSubmit]


class QuizSaveProgressRequest(BaseModel):
    progress_data: Dict[str, Any]


class QuizAnswerResponse(BaseModel):
    id: UUID
    question_id: UUID
    selected_option: Optional[str] = None
    provided_answer: Optional[str] = None
    is_correct: bool
    points_awarded: float
    feedback_comments: Optional[str] = None
    teacher_override_score: Optional[float] = None
    evaluated_by_ai: bool

    class Config:
        from_attributes = True


class QuizAttemptResponse(BaseModel):
    id: UUID
    quiz_id: UUID
    student_id: UUID
    started_at: datetime
    completed_at: Optional[datetime] = None
    score: Optional[float] = None
    total_points: float
    passed: bool
    status: str
    answers: List[QuizAnswerResponse] = []

    class Config:
        from_attributes = True


class SubjectiveOverrideRequest(BaseModel):
    question_id: UUID
    override_score: float = Field(..., ge=0)
    teacher_comments: Optional[str] = None


class AdaptiveRecommendationResponse(BaseModel):
    weak_topics: List[str]
    strong_topics: List[str]
    accuracy_percentage: float
    suggested_difficulty: str
    recommended_revision_notes: List[Dict[str, Any]] = []


class LeaderboardEntry(BaseModel):
    rank: int
    student_name: str
    student_id: UUID
    score: float
    accuracy: float
    completed_at: Optional[datetime] = None


class QuizAnalyticsResponse(BaseModel):
    quiz_id: UUID
    total_attempts: int
    average_score: float
    highest_score: float
    lowest_score: float
    pass_rate: float
    difficulty_distribution: Dict[str, float] = {}
    blooms_distribution: Dict[str, float] = {}
    most_incorrect_questions: List[Dict[str, Any]] = []


class QuestionBankResponse(QuestionBase):
    id: UUID
    creator_id: UUID
    subject: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
