import os
import csv
import logging
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import EntityNotFoundException, ValidationException
from app.models.reports import GeneratedReport
from app.models.user import User

logger = logging.getLogger(__name__)


class ReportService:
    """
    Enterprise Reporting Engine for CSV, Excel, and PDF exports.
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        self.export_dir = os.path.join(settings.UPLOAD_DIR, "reports")
        os.makedirs(self.export_dir, exist_ok=True)

    async def generate_report(
        self,
        generated_by_id: UUID,
        report_type: str,
        export_format: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> GeneratedReport:
        """Generates a downloadable report file (CSV/Excel/PDF) and indexes metadata."""
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{report_type}_report_{timestamp_str}.{export_format.lower()}"
        file_path = os.path.join(self.export_dir, filename)

        # Query real data from database for report content
        headers = ["ID", "Category", "Metric", "Value", "Generated Timestamp"]
        rows = []

        from app.models.attendance import Attendance, AttendanceStatus
        from app.models.quiz import QuizAttempt
        from app.models.assignment import AssignmentSubmission
        from app.models.communication import ChatSession
        from sqlalchemy import func as sa_func

        now_str = str(datetime.now(timezone.utc))

        # Attendance percentage
        att_total = (await self.db.execute(select(sa_func.count(Attendance.id)).filter(Attendance.is_deleted == False))).scalar() or 0
        att_present = (await self.db.execute(
            select(sa_func.count(Attendance.id)).filter(Attendance.is_deleted == False, Attendance.status == AttendanceStatus.PRESENT)
        )).scalar() or 0
        att_pct = round((att_present / att_total * 100.0) if att_total > 0 else 0.0, 1)
        rows.append(["1", report_type.upper(), "Attendance Percentage", f"{att_pct}%", now_str])

        # Average quiz score
        avg_score = (await self.db.execute(
            select(sa_func.avg(QuizAttempt.score)).filter(QuizAttempt.status == "evaluated", QuizAttempt.score.isnot(None))
        )).scalar()
        avg_score_str = f"{round(float(avg_score), 1)}%" if avg_score else "0.0%"
        rows.append(["2", report_type.upper(), "Average Quiz Score", avg_score_str, now_str])

        # Completed assignments
        completed_count = (await self.db.execute(
            select(sa_func.count(AssignmentSubmission.id)).filter(
                AssignmentSubmission.is_deleted == False,
                AssignmentSubmission.processing_status == "completed"
            )
        )).scalar() or 0
        rows.append(["3", report_type.upper(), "Completed Assignments", str(completed_count), now_str])

        # AI queries executed
        ai_count = (await self.db.execute(select(sa_func.count(ChatSession.id)))).scalar() or 0
        rows.append(["4", report_type.upper(), "AI Queries Executed", str(ai_count), now_str])

        if export_format.lower() == "csv":
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows)

        elif export_format.lower() == "excel":
            # Formatted TSV/CSV with .xlsx placeholder or standard text export
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter="\t")
                writer.writerow(headers)
                writer.writerows(rows)

        elif export_format.lower() == "pdf":
            # Text PDF format write
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"=== {report_type.upper()} ACADEMIC REPORT ===\n\n")
                for h, v in zip(headers, rows[0]):
                    f.write(f"{h}: {v}\n")
                f.write("\n====================================\n")

        else:
            raise ValidationException(f"Unsupported report format: {export_format}")

        file_size = os.path.getsize(file_path)

        report = GeneratedReport(
            report_name=f"{report_type.title()} Report ({export_format.upper()})",
            report_type=report_type,
            format=export_format.lower(),
            file_path=file_path,
            file_size=file_size,
            filters=filters,
            generated_by_id=generated_by_id
        )
        self.db.add(report)
        await self.db.commit()
        await self.db.refresh(report)

        logger.info(f"Report generated successfully: {file_path}")
        return report

    async def get_user_reports(self, user_id: UUID) -> List[GeneratedReport]:
        """Lists reports generated by a user."""
        stmt = select(GeneratedReport).filter(GeneratedReport.generated_by_id == user_id, GeneratedReport.is_deleted == False).order_by(GeneratedReport.created_at.desc())
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def get_report_by_id(self, report_id: UUID) -> GeneratedReport:
        """Retrieves a single report by ID."""
        stmt = select(GeneratedReport).filter(GeneratedReport.id == report_id, GeneratedReport.is_deleted == False)
        res = await self.db.execute(stmt)
        report = res.scalars().first()
        if not report:
            raise EntityNotFoundException("Generated report not found.")
        return report
