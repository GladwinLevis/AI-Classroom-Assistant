from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class RubricCriterion(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    max_score: float = Field(..., gt=0)
    description: Optional[str] = None


class AssignmentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    instructions: Optional[str] = None
    due_date: Optional[datetime] = None
    max_points: float = Field(100.0, gt=0)


class AssignmentCreate(AssignmentBase):
    course_id: UUID
    rubric: Optional[List[RubricCriterion]] = None
    reference_material_id: Optional[UUID] = None


class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    due_date: Optional[datetime] = None
    max_points: Optional[float] = None
    rubric: Optional[List[RubricCriterion]] = None


class AssignmentResponse(AssignmentBase):
    id: UUID
    course_id: UUID
    is_published: bool
    rubric: Optional[List[RubricCriterion]] = None
    reference_material_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AssignmentSubmissionBase(BaseModel):
    submitted_text: Optional[str] = None


class AssignmentSubmissionCreate(AssignmentSubmissionBase):
    pass


class AssignmentSubmissionResponse(AssignmentSubmissionBase):
    id: UUID
    assignment_id: UUID
    student_id: UUID
    file_upload_id: Optional[UUID] = None
    submitted_at: datetime
    status: str
    version: int
    is_final: bool
    processing_status: str
    created_at: datetime

    class Config:
        from_attributes = True


class CriterionEvaluation(BaseModel):
    criterion_name: str
    assigned_score: float
    max_score: float
    comments: str


class AssignmentFeedbackResponse(BaseModel):
    id: UUID
    submission_id: UUID
    grader_id: Optional[UUID] = None
    feedback_text: str
    grade_score: float
    ai_score: Optional[float] = None
    final_score: Optional[float] = None
    is_approved: bool
    status: str
    plagiarism_score: float
    rubric_evaluation: Optional[List[CriterionEvaluation]] = None
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    grammar_feedback: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = None
    similarity_report: Optional[Dict[str, Any]] = None
    generated_at: datetime

    class Config:
        from_attributes = True


class GradeApprovalRequest(BaseModel):
    approved_score: float = Field(..., ge=0)
    teacher_comments: Optional[str] = None


class GradeRejectionRequest(BaseModel):
    rejection_reason: str = Field(..., min_length=1)


class AssignmentAnalyticsResponse(BaseModel):
    assignment_id: UUID
    total_students: int
    submissions_count: int
    submission_rate: float
    average_score: Optional[float] = None
    highest_score: Optional[float] = None
    lowest_score: Optional[float] = None
    late_submissions_count: int
    pending_reviews_count: int
    rubric_performance: Dict[str, float] = {}
