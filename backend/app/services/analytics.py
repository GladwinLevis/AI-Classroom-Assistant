import logging
from typing import List
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import Attendance, AttendanceStatus
from app.models.quiz import QuizAttempt
from app.models.assignment import AssignmentSubmission
from app.models.communication import ChatSession
from app.models.document import Notes
from app.schemas.dashboard import RechartsSeriesData

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Multi-dimensional Analytics Platform service producing Recharts-compatible data structures
    from real database aggregation queries.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_attendance_analytics(self) -> List[RechartsSeriesData]:
        """Calculates attendance trends from real attendance records, grouped by day of week."""
        day_names = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday", 4: "Friday", 5: "Saturday", 6: "Sunday"}
        stmt = select(Attendance).filter(Attendance.is_deleted == False)
        res = await self.db.execute(stmt)
        records = res.scalars().all()

        if not records:
            return []

        day_totals: dict = {}
        day_present: dict = {}
        for r in records:
            if r.date:
                dow = r.date.weekday()
                day_totals[dow] = day_totals.get(dow, 0) + 1
                if r.status == AttendanceStatus.PRESENT:
                    day_present[dow] = day_present.get(dow, 0) + 1

        result = []
        for dow in sorted(day_totals.keys()):
            total = day_totals[dow]
            present = day_present.get(dow, 0)
            pct = round((present / total * 100.0) if total > 0 else 0.0, 1)
            result.append(RechartsSeriesData(name=day_names.get(dow, f"Day {dow}"), value=pct))

        return result

    async def get_quiz_analytics(self) -> List[RechartsSeriesData]:
        """Calculates quiz score distribution from real quiz attempts."""
        stmt = select(QuizAttempt.score).filter(
            QuizAttempt.status == "evaluated",
            QuizAttempt.score.isnot(None)
        )
        res = await self.db.execute(stmt)
        scores = [row[0] for row in res.all()]

        if not scores:
            return []

        buckets = {"0-50%": 0, "51-70%": 0, "71-85%": 0, "86-100%": 0}
        for s in scores:
            if s <= 50:
                buckets["0-50%"] += 1
            elif s <= 70:
                buckets["51-70%"] += 1
            elif s <= 85:
                buckets["71-85%"] += 1
            else:
                buckets["86-100%"] += 1

        total = len(scores)
        return [
            RechartsSeriesData(name=k, value=round(v / total * 100.0, 1))
            for k, v in buckets.items()
        ]

    async def get_assignment_analytics(self) -> List[RechartsSeriesData]:
        """Calculates assignment submission rates from real submission records."""
        stmt = select(AssignmentSubmission.processing_status).filter(
            AssignmentSubmission.is_deleted == False
        )
        res = await self.db.execute(stmt)
        statuses = [row[0] for row in res.all()]

        if not statuses:
            return []

        total = len(statuses)
        completed = sum(1 for s in statuses if s == "completed")
        pending = sum(1 for s in statuses if s == "pending")
        processing = sum(1 for s in statuses if s == "processing")

        return [
            RechartsSeriesData(name="Completed", value=round(completed / total * 100.0, 1)),
            RechartsSeriesData(name="Pending", value=round(pending / total * 100.0, 1)),
            RechartsSeriesData(name="Processing", value=round(processing / total * 100.0, 1)),
        ]

    async def get_ai_usage_analytics(self) -> List[RechartsSeriesData]:
        """Calculates AI feature engagement from real usage records."""
        notes_count = (await self.db.execute(
            select(func.count(Notes.id)).filter(Notes.is_deleted == False)
        )).scalar() or 0

        chat_count = (await self.db.execute(
            select(func.count(ChatSession.id)).filter(ChatSession.is_archived == False)
        )).scalar() or 0

        eval_count = (await self.db.execute(
            select(func.count(AssignmentSubmission.id)).filter(
                AssignmentSubmission.is_deleted == False,
                AssignmentSubmission.processing_status == "completed"
            )
        )).scalar() or 0

        quiz_count = (await self.db.execute(
            select(func.count(QuizAttempt.id)).filter(QuizAttempt.status == "evaluated")
        )).scalar() or 0

        return [
            RechartsSeriesData(name="Notes Summarization", value=float(notes_count)),
            RechartsSeriesData(name="Doubt Chatbot RAG", value=float(chat_count)),
            RechartsSeriesData(name="Assignment Evaluation", value=float(eval_count)),
            RechartsSeriesData(name="Quiz Generation", value=float(quiz_count)),
        ]
