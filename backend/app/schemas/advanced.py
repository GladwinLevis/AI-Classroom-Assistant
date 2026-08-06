from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid


# 1. AI Explainability & Multi-Provider Schemas
class SourceReference(BaseModel):
    title: str
    content_snippet: str
    relevance_score: float = Field(..., ge=0.0, le=1.0)


class AIExplainableResponse(BaseModel):
    query: str
    response_text: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    reasoning_summary: str
    source_references: List[SourceReference] = []
    processing_time_ms: float
    token_usage: Dict[str, int]
    ai_model_used: str
    warnings: List[str] = []


# 2. Learning Recommendation Engine Schemas
class DailyStudyGoal(BaseModel):
    goal_id: str
    title: str
    target_minutes: int
    completed_minutes: int
    is_achieved: bool


class LearningPathStep(BaseModel):
    step_number: int
    topic: str
    resource_type: str  # notes, quiz, assignment
    resource_id: Optional[str] = None
    estimated_minutes: int
    is_completed: bool = False


class LearningRecommendationResponse(BaseModel):
    weak_concepts: List[str]
    recommended_topics: List[str]
    daily_goals: List[DailyStudyGoal]
    learning_path: List[LearningPathStep]
    revision_plan: List[Dict[str, Any]]


# 3. Gamification Schemas
class BadgeItem(BaseModel):
    badge_id: str
    name: str
    description: str
    icon: str
    unlocked_at: datetime


class AchievementItem(BaseModel):
    achievement_id: str
    title: str
    xp_reward: int
    progress_percentage: float


class UserGamificationResponse(BaseModel):
    user_id: uuid.UUID
    xp_points: int
    level: int
    current_streak: int
    longest_streak: int
    badges: List[BadgeItem] = []
    achievements: List[AchievementItem] = []


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: str
    name: str
    xp_points: int
    level: int
    avatar_url: Optional[str] = None


# 4. Academic Calendar & Reminders Schemas
class CalendarEventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    event_type: str = "study"  # study, assignment, quiz, exam_countdown, revision
    start_time: datetime
    end_time: Optional[datetime] = None


class CalendarEventResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str]
    event_type: str
    start_time: datetime
    end_time: Optional[datetime]
    is_completed: bool

    class Config:
        from_attributes = True


class SmartReminderCreate(BaseModel):
    title: str
    reminder_type: str = "study_goal"
    remind_at: datetime


class SmartReminderResponse(BaseModel):
    id: uuid.UUID
    title: str
    reminder_type: str
    remind_at: datetime
    is_triggered: bool

    class Config:
        from_attributes = True


# 5. Hybrid Search Schemas
class SearchResultItem(BaseModel):
    id: str
    entity_type: str
    title: str
    snippet: str
    score: float


class HybridSearchResponse(BaseModel):
    query: str
    results: List[SearchResultItem]
    total_count: int
    suggestions: List[str] = []


# 6. AI Insights & Drop Risk Schemas
class DropRiskPrediction(BaseModel):
    student_id: uuid.UUID
    student_name: str
    risk_level: str  # Low, Medium, High, Critical
    risk_score: float = Field(..., ge=0.0, le=100.0)
    contributing_factors: List[str]
    actionable_recommendations: List[str]


class StudentLearningInsights(BaseModel):
    learning_velocity: float
    retention_rate_pct: float
    study_habit_score: float
    predicted_final_grade: str
    drop_risk: DropRiskPrediction
