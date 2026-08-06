import logging
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.attendance import Attendance, AttendanceStatus
from app.schemas.advanced import (
    StudentLearningInsights,
    DropRiskPrediction
)

logger = logging.getLogger(__name__)


class AIInsightsService:
    """
    AI Predictive Analytics Service generating student learning insights, drop-risk predictions,
    and class intelligence dynamically from database records.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_student_insights(self, student_id: uuid.UUID) -> StudentLearningInsights:
        """Computes predictive learning insights and drop-risk score for student."""
        # Query User
        u_stmt = select(User).filter(User.id == student_id)
        u_res = await self.db.execute(u_stmt)
        user = u_res.scalars().first()
        full_name = f"{user.first_name} {user.last_name}".strip() if user else "Student"

        # Query Attendance records
        att_stmt = select(Attendance).filter(Attendance.user_id == student_id)
        att_res = await self.db.execute(att_stmt)
        attendances = att_res.scalars().all()
        total_att = len(attendances)
        present_count = sum(1 for a in attendances if a.status == AttendanceStatus.PRESENT)
        att_pct = round((present_count / total_att * 100.0) if total_att > 0 else 100.0, 1)

        risk_level = "Low" if att_pct >= 85.0 else ("Medium" if att_pct >= 75.0 else "High")
        risk_score = round(max(0.0, 100.0 - att_pct), 1)

        risk = DropRiskPrediction(
            student_id=student_id,
            student_name=full_name,
            risk_level=risk_level,
            risk_score=risk_score,
            contributing_factors=[f"Attendance rate is {att_pct}%"],
            actionable_recommendations=[
                "Maintain consistent class attendance",
                "Complete assigned study modules regularly"
            ]
        )

        return StudentLearningInsights(
            learning_velocity=1.0,
            retention_rate_pct=att_pct,
            study_habit_score=att_pct,
            predicted_final_grade="A" if att_pct >= 85.0 else "B",
            drop_risk=risk
        )
