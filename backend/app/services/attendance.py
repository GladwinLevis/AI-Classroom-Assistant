import logging
import hmac
import hashlib
import json
import base64
import csv
import io
from datetime import datetime, timedelta, timezone, date, time
from typing import List, Optional, Dict, Any, Protocol
from uuid import UUID, uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.exceptions import AuthException, ConflictException, ValidationException, EntityNotFoundException
from app.models.attendance import Attendance, AttendanceSession, AttendanceRecord, AttendanceSessionStatus, AttendanceStatus, AttendanceMode
from app.models.user import StudentProfile, TeacherProfile, User
from app.models.course import Course, Enrollment, Subject, Classroom
from app.models.analytics import AuditLog
from app.repositories.attendance import AttendanceSessionRepository, AttendanceRecordRepository, AttendanceDailyRepository
from app.schemas.attendance import (
    AttendanceSessionCreate, AttendanceSessionUpdate, AttendanceRecordMark,
    AttendanceBulkMarkRequest, QRGenerateResponse, AttendanceStats,
    AttendanceDashboardAnalytics, SubjectWiseStats, CourseWiseStats,
    StudentAttendanceSummary, StudentAttendanceReportRow, AttendanceReportResponse
)

logger = logging.getLogger(__name__)


class FaceVerificationInterface(Protocol):
    """
    Protocol for future face verification plugins.
    Allows easy OpenCV, TensorFlow, or DeepFace integration.
    """
    async def verify_face(self, student_id: UUID, image_data: bytes) -> bool:
        ...


class RecognitionProvider:
    """Future OpenCV/TensorFlow implementation placeholder."""
    def __init__(self, model_name: str = "deepface"):
        self.model_name = model_name

    async def run_recognition(self, image_data: bytes, reference_image_path: str) -> float:
        """Run similarity score comparison. Mock: returns 0.95 similarity."""
        return 0.95


class FaceAttendanceService:
    """
    Future-ready service interface for face recognition verified attendance.
    """
    def __init__(self, provider: Optional[RecognitionProvider] = None):
        self.provider = provider or RecognitionProvider()

    async def verify_face_match(self, student_id: UUID, captured_image: bytes) -> bool:
        """
        Mock face verification check.
        In production, matches database reference face photo against raw captured bytes.
        """
        logger.info(f"Initiating face verification check for student ID: {student_id}")
        # Run mock recognition
        score = await self.provider.run_recognition(captured_image, "mock_ref_path")
        is_match = score >= 0.80
        logger.info(f"Face verification score: {score:.4f}. Match: {is_match}")
        return is_match


class QRCodeService:
    """
    Service responsible for generation and cryptographic signature validation of attendance QR codes.
    Uses HMAC-SHA256 signature to prevent student proxy attendance tampering.
    """
    def __init__(self, secret_key: str):
        self.secret_key = secret_key

    def generate_qr_token(self, session_id: UUID, ttl_seconds: int = 60) -> str:
        """
        Generates a signed Base64 token containing session_id and expiry.
        """
        expires_at = (datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)).isoformat()
        payload = {
            "session_id": str(session_id),
            "expires_at": expires_at
        }
        payload_bytes = json.dumps(payload).encode('utf-8')
        signature = hmac.new(self.secret_key.encode('utf-8'), payload_bytes, hashlib.sha256).hexdigest()
        
        token_data = {
            "payload": payload,
            "signature": signature
        }
        token_str = json.dumps(token_data)
        return base64.b64encode(token_str.encode('utf-8')).decode('utf-8')

    def validate_qr_token(self, token_str: str) -> UUID:
        """
        Decodes, verifies signature, checks expiry, and returns the verified session UUID.
        Raises ValidationException on error or signature mismatches.
        """
        try:
            decoded = base64.b64decode(token_str.encode('utf-8')).decode('utf-8')
            token_data = json.loads(decoded)
            payload = token_data["payload"]
            signature = token_data["signature"]
        except Exception as e:
            raise ValidationException("Invalid QR Code payload structure.") from e

        # Re-verify HMAC signature
        payload_bytes = json.dumps(payload).encode('utf-8')
        expected_sig = hmac.new(self.secret_key.encode('utf-8'), payload_bytes, hashlib.sha256).hexdigest()
        
        if not hmac.compare_digest(signature, expected_sig):
            raise ValidationException("QR Code signature verification failed. Token is tampered or invalid.")

        # Check expiration
        expires_at = datetime.fromisoformat(payload["expires_at"])
        if datetime.now(timezone.utc) > expires_at.replace(tzinfo=timezone.utc):
            raise ValidationException("QR Code has expired.")

        return UUID(payload["session_id"])


class NotificationService:
    """
    Mock service to handle system notifications for session status and warning alerts.
    """
    @staticmethod
    async def send_attendance_marked(db: AsyncSession, student_id: UUID, session_id: UUID) -> None:
        logger.info(f"[NOTIFY] Attendance marked successfully for student {student_id} in session {session_id}")

    @staticmethod
    async def send_session_started(db: AsyncSession, course_id: UUID, session_id: UUID) -> None:
        logger.info(f"[NOTIFY] Attendance session {session_id} has started for course {course_id}")

    @staticmethod
    async def send_low_attendance_warning(db: AsyncSession, student_id: UUID, course_id: UUID, percentage: float) -> None:
        logger.info(f"[NOTIFY] Alert: student {student_id} has low attendance in course {course_id} ({percentage:.2f}%)")


class AttendanceSessionService:
    """
    Handles business workflows for managing Attendance Sessions (creation, status transition).
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        self.session_repo = AttendanceSessionRepository(db)

    async def create_session(self, request: AttendanceSessionCreate, current_user: User) -> AttendanceSession:
        """Creates a new attendance session for a class. Restricts creation to the assigned course teacher."""
        # Fetch course detail
        stmt = select(Course).filter(Course.id == request.course_id, Course.is_deleted == False)
        res = await self.db.execute(stmt)
        course = res.scalars().first()
        if not course:
            raise EntityNotFoundException("Requested course does not exist.")

        # Validate that the caller is indeed the teacher of the course (unless Admin)
        is_admin = any(role.name == "admin" for role in current_user.roles)
        teacher_id = None
        if not is_admin:
            # Caller must be a teacher
            teacher_stmt = select(TeacherProfile).filter(TeacherProfile.user_id == current_user.id)
            teacher_res = await self.db.execute(teacher_stmt)
            teacher_profile = teacher_res.scalars().first()
            if not teacher_profile or course.teacher_id != teacher_profile.id:
                raise AuthException("Access Denied. Only the assigned teacher of the course can create sessions.")
            teacher_id = teacher_profile.id
        else:
            teacher_id = course.teacher_id

        # Insert session object
        session = AttendanceSession(
            course_id=request.course_id,
            classroom_id=request.classroom_id,
            date=request.date,
            start_time=request.start_time,
            end_time=request.end_time,
            teacher_id=teacher_id,
            attendance_mode=request.attendance_mode,
            status=AttendanceSessionStatus.SCHEDULED
        )
        self.db.add(session)
        await self.db.flush()

        # Audit logging
        audit = AuditLog(
            event_type="insert",
            table_name="attendance_sessions",
            record_id=session.id,
            new_values={
                "course_id": str(session.course_id),
                "teacher_id": str(session.teacher_id),
                "date": session.date.isoformat(),
                "attendance_mode": session.attendance_mode.value,
                "status": session.status.value
            },
            user_id=current_user.id
        )
        self.db.add(audit)
        await self.db.flush()

        logger.info(f"Created attendance session {session.id} for course {session.course_id}")
        return session

    async def update_session(self, session_id: UUID, request: AttendanceSessionUpdate, current_user: User) -> AttendanceSession:
        """Update an attendance session's parameters."""
        session = await self.session_repo.get(session_id)
        if not session or session.is_deleted:
            raise EntityNotFoundException("Session not found.")

        # Permissions check
        await self._verify_session_ownership(session, current_user)

        old_values = {
            "classroom_id": str(session.classroom_id) if session.classroom_id else None,
            "status": session.status.value,
            "attendance_mode": session.attendance_mode.value
        }

        # Updates
        update_data = request.model_dump(exclude_unset=True)
        for field, val in update_data.items():
            setattr(session, field, val)

        self.db.add(session)
        await self.db.flush()

        # Audit log
        new_values = {
            "classroom_id": str(session.classroom_id) if session.classroom_id else None,
            "status": session.status.value,
            "attendance_mode": session.attendance_mode.value
        }
        audit = AuditLog(
            event_type="update",
            table_name="attendance_sessions",
            record_id=session.id,
            old_values=old_values,
            new_values=new_values,
            user_id=current_user.id
        )
        self.db.add(audit)
        await self.db.flush()

        logger.info(f"Updated attendance session {session.id} status to {session.status.value}")
        
        # Trigger mock notifications for session transitions
        if request.status == AttendanceSessionStatus.ACTIVE:
            await NotificationService.send_session_started(self.db, session.course_id, session.id)
            
        return session

    async def _verify_session_ownership(self, session: AttendanceSession, current_user: User) -> None:
        """Verifies if the current user has access rights to modify/manage the session."""
        is_admin = any(role.name == "admin" for role in current_user.roles)
        if is_admin:
            return

        teacher_stmt = select(TeacherProfile).filter(TeacherProfile.user_id == current_user.id)
        teacher_res = await self.db.execute(teacher_stmt)
        teacher_profile = teacher_res.scalars().first()
        
        if not teacher_profile or session.teacher_id != teacher_profile.id:
            raise AuthException("Access Denied. You do not own this attendance session.")


class AttendanceService:
    """
    Handles business workflows for marking and reviewing student attendance records.
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        self.record_repo = AttendanceRecordRepository(db)
        self.session_repo = AttendanceSessionRepository(db)
        self.qr_service = QRCodeService(settings.JWT_SECRET_KEY)
        self.face_service = FaceAttendanceService()

    async def mark_student_attendance(
        self,
        session_id: UUID,
        current_user: User,
        qr_token: Optional[str] = None,
        face_image_bytes: Optional[bytes] = None
    ) -> AttendanceRecord:
        """Marks student self-attendance, enforcing QR Code, Face Recognition, and duplicate constraints."""
        # 1. Fetch student profile
        student_stmt = select(StudentProfile).filter(StudentProfile.user_id == current_user.id)
        student_res = await self.db.execute(student_stmt)
        student = student_res.scalars().first()
        if not student:
            raise AuthException("Only registered students can mark attendance.")

        # 2. Fetch session and validate status
        session = await self.session_repo.get(session_id)
        if not session or session.is_deleted:
            raise EntityNotFoundException("Attendance session does not exist.")
        if session.status != AttendanceSessionStatus.ACTIVE:
            raise ValidationException("This attendance session is not active.")

        # 3. Verify student enrollment in course
        enroll_stmt = select(Enrollment).filter(
            Enrollment.student_id == student.id,
            Enrollment.course_id == session.course_id,
            Enrollment.status == "active"
        )
        enroll_res = await self.db.execute(enroll_stmt)
        enrollment = enroll_res.scalars().first()
        if not enrollment:
            raise ValidationException("Student is not enrolled in this course.")

        # 4. Check for existing attendance record (prevent duplicates)
        existing = await self.record_repo.get_student_record_for_session(session.id, student.id)
        if existing:
            raise ConflictException("Attendance is already marked for this session.")

        # 5. Enforce attendance mode validation checks
        if session.attendance_mode == AttendanceMode.QR_CODE:
            if not qr_token:
                raise ValidationException("QR Code scan token is required for this session.")
            # Cryptographically validate QR signature
            validated_session_id = self.qr_service.validate_qr_token(qr_token)
            if validated_session_id != session.id:
                raise ValidationException("Invalid QR Code scanner token mismatch.")

        elif session.attendance_mode == AttendanceMode.FACE_RECOGNITION:
            if not face_image_bytes:
                raise ValidationException("Face recognition image data is required for this session.")
            is_verified = await self.face_service.verify_face_match(student.id, face_image_bytes)
            if not is_verified:
                raise ValidationException("Face verification validation failed.")

        elif session.attendance_mode == AttendanceMode.HYBRID:
            # Requires at least one validation factor
            if qr_token:
                validated_session_id = self.qr_service.validate_qr_token(qr_token)
                if validated_session_id != session.id:
                    raise ValidationException("Invalid QR Code scanner token mismatch.")
            elif face_image_bytes:
                is_verified = await self.face_service.verify_face_match(student.id, face_image_bytes)
                if not is_verified:
                    raise ValidationException("Face verification validation failed.")
            else:
                raise ValidationException("QR Code or Face recognition confirmation is required.")

        # 6. Save attendance record
        record = AttendanceRecord(
            session_id=session.id,
            student_id=student.id,
            status=AttendanceStatus.PRESENT,
            marked_at=datetime.now(timezone.utc),
            marked_by_id=current_user.id
        )
        self.db.add(record)
        await self.db.flush()

        # Audit log
        audit = AuditLog(
            event_type="insert",
            table_name="attendance_records",
            record_id=record.id,
            new_values={
                "session_id": str(record.session_id),
                "student_id": str(record.student_id),
                "status": record.status.value,
                "marked_by": str(record.marked_by_id)
            },
            user_id=current_user.id
        )
        self.db.add(audit)
        await self.db.flush()

        # Dispatch alert
        await NotificationService.send_attendance_marked(self.db, student.id, session.id)

        logger.info(f"Student {student.id} marked present in session {session.id}")
        return record

    async def mark_teacher_bulk_attendance(
        self,
        session_id: UUID,
        request: AttendanceBulkMarkRequest,
        current_user: User
    ) -> List[AttendanceRecord]:
        """Teacher marks present/absent/late/excused for a group of student IDs at once."""
        session = await self.session_repo.get(session_id)
        if not session or session.is_deleted:
            raise EntityNotFoundException("Session not found.")

        # Verify teacher ownership
        await AttendanceSessionService(self.db)._verify_session_ownership(session, current_user)

        if session.status == AttendanceSessionStatus.CLOSED:
            raise ValidationException("Cannot mark or modify attendance on a closed session.")

        records = []
        for student_id in request.student_ids:
            # Validate enrollment
            enroll_stmt = select(Enrollment).filter(
                Enrollment.student_id == student_id,
                Enrollment.course_id == session.course_id,
                Enrollment.status == "active"
            )
            enroll_res = await self.db.execute(enroll_stmt)
            if not enroll_res.scalars().first():
                logger.warning(f"Skipping student {student_id} bulk mark because they are not active in course.")
                continue

            existing = await self.record_repo.get_student_record_for_session(session.id, student_id)
            old_values = {}
            event_type = "insert"

            if existing:
                event_type = "update"
                old_values = {"status": existing.status.value}
                existing.status = request.status
                existing.marked_at = datetime.now(timezone.utc)
                existing.marked_by_id = current_user.id
                record = existing
            else:
                record = AttendanceRecord(
                    session_id=session.id,
                    student_id=student_id,
                    status=request.status,
                    marked_at=datetime.now(timezone.utc),
                    marked_by_id=current_user.id
                )
            
            self.db.add(record)
            await self.db.flush()

            # Audit logging
            audit = AuditLog(
                event_type=event_type,
                table_name="attendance_records",
                record_id=record.id,
                old_values=old_values if event_type == "update" else None,
                new_values={
                    "session_id": str(record.session_id),
                    "student_id": str(record.student_id),
                    "status": record.status.value,
                    "marked_by": str(record.marked_by_id)
                },
                user_id=current_user.id
            )
            self.db.add(audit)
            records.append(record)

        await self.db.flush()
        logger.info(f"Bulk marked {len(records)} student records as {request.status.value} in session {session.id}")
        return records

    async def update_single_attendance_record(
        self,
        session_id: UUID,
        student_id: UUID,
        status: AttendanceStatus,
        current_user: User
    ) -> AttendanceRecord:
        """Updates a student's attendance status. Allowed only before the session closes."""
        session = await self.session_repo.get(session_id)
        if not session or session.is_deleted:
            raise EntityNotFoundException("Session not found.")

        # Permissions checks
        await AttendanceSessionService(self.db)._verify_session_ownership(session, current_user)

        if session.status == AttendanceSessionStatus.CLOSED:
            raise ValidationException("Cannot update record. Session is already closed.")

        existing = await self.record_repo.get_student_record_for_session(session.id, student_id)
        if not existing:
            # Create record if not existed
            record = AttendanceRecord(
                session_id=session.id,
                student_id=student_id,
                status=status,
                marked_at=datetime.now(timezone.utc),
                marked_by_id=current_user.id
            )
            event_type = "insert"
            old_values = None
        else:
            record = existing
            event_type = "update"
            old_values = {"status": record.status.value}
            record.status = status
            record.marked_by_id = current_user.id
            record.marked_at = datetime.now(timezone.utc)

        self.db.add(record)
        await self.db.flush()

        # Audit
        audit = AuditLog(
            event_type=event_type,
            table_name="attendance_records",
            record_id=record.id,
            old_values=old_values,
            new_values={
                "session_id": str(record.session_id),
                "student_id": str(record.student_id),
                "status": record.status.value,
                "marked_by": str(record.marked_by_id)
            },
            user_id=current_user.id
        )
        self.db.add(audit)
        await self.db.flush()

        logger.info(f"Updated attendance record {record.id} for student {student_id} to status {status.value}")
        return record


class AttendanceAnalyticsService:
    """
    Computes dashboard analytics, session ratios, weekly progress, and student warnings.
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        self.record_repo = AttendanceRecordRepository(db)

    def _calculate_stats(self, records: List[AttendanceRecord]) -> AttendanceStats:
        """Helper to calculate metrics from record lists."""
        total = len(records)
        if total == 0:
            return AttendanceStats(
                attendance_percentage=0.0,
                present_count=0,
                absent_count=0,
                late_count=0,
                excused_count=0,
                total_count=0
            )
        
        p_cnt = sum(1 for r in records if r.status == AttendanceStatus.PRESENT)
        a_cnt = sum(1 for r in records if r.status == AttendanceStatus.ABSENT)
        l_cnt = sum(1 for r in records if r.status == AttendanceStatus.LATE)
        e_cnt = sum(1 for r in records if r.status == AttendanceStatus.EXCUSED)

        # Formula: (Present + Late + Excused) / Total Sessions
        # Wait, usually Excused does not penalize, or present + late counted as attended.
        # Let's count PRESENT + LATE + EXCUSED as attended.
        attended = p_cnt + l_cnt + e_cnt
        percentage = (attended / total) * 100.0

        return AttendanceStats(
            attendance_percentage=round(percentage, 2),
            present_count=p_cnt,
            absent_count=a_cnt,
            late_count=l_cnt,
            excused_count=e_cnt,
            total_count=total
        )

    async def get_student_dashboard_analytics(self, student_id: UUID) -> StudentAttendanceSummary:
        """Retrieves comprehensive analytics metrics matching a student profile."""
        records = await self.record_repo.get_student_overall_stats(student_id)
        overall = self._calculate_stats(records)

        # Course-wise breakdown
        course_records_map: Dict[UUID, List[AttendanceRecord]] = {}
        for r in records:
            course_id = r.session.course_id
            if course_id not in course_records_map:
                course_records_map[course_id] = []
            course_records_map[course_id].append(r)

        course_wise = []
        for course_id, r_list in course_records_map.items():
            # Get course code/name
            course = r_list[0].session.course
            course_wise.append(
                CourseWiseStats(
                    course_id=course_id,
                    course_name=course.name,
                    course_code=course.code,
                    stats=self._calculate_stats(r_list)
                )
            )

        return StudentAttendanceSummary(
            student_id=student_id,
            stats=overall,
            course_wise=course_wise
        )

    async def get_teacher_course_dashboard(self, course_id: UUID) -> AttendanceDashboardAnalytics:
        """Generates detailed reports dashboard for a course."""
        records = await self.record_repo.get_course_stats(course_id)
        overall = self._calculate_stats(records)

        # Subject wise (for mapping multi-subject structures)
        # Fetch course details
        stmt = select(Course).filter(Course.id == course_id).options(selectinload(Course.subject))
        res = await self.db.execute(stmt)
        course = res.scalars().first()
        
        subject_wise = []
        if course:
            subject_wise.append(
                SubjectWiseStats(
                    subject_id=course.subject_id,
                    subject_name=course.subject.name,
                    subject_code=course.subject.code,
                    stats=overall
                )
            )

        # Weekly and Monthly charts data
        weekly_chart = {}
        monthly_chart = {}
        
        for r in records:
            session_date = r.session.date
            # Weekly key
            week_key = session_date.strftime("%Y-W%W")
            if week_key not in weekly_chart:
                weekly_chart[week_key] = []
            weekly_chart[week_key].append(r)

            # Monthly key
            month_key = session_date.strftime("%Y-%m")
            if month_key not in monthly_chart:
                monthly_chart[month_key] = []
            monthly_chart[month_key].append(r)

        weekly_chart_data = {k: self._calculate_stats(v) for k, v in weekly_chart.items()}
        monthly_chart_data = {k: self._calculate_stats(v) for k, v in monthly_chart.items()}

        course_wise_stats = [
            CourseWiseStats(
                course_id=course_id,
                course_name=course.name if course else "Unknown",
                course_code=course.code if course else "",
                stats=overall
            )
        ]

        return AttendanceDashboardAnalytics(
            overall=overall,
            course_wise=course_wise_stats,
            subject_wise=subject_wise,
            weekly_chart_data=weekly_chart_data,
            monthly_chart_data=monthly_chart_data
        )


class AttendanceReportService:
    """
    Format attendance data summaries and export outputs (CSV/Excel).
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        self.record_repo = AttendanceRecordRepository(db)
        self.analytics_service = AttendanceAnalyticsService(db)

    async def generate_course_attendance_report(self, course_id: UUID) -> List[StudentAttendanceReportRow]:
        """Compiles student list with aggregated percentages for a specific course."""
        # 1. Fetch active course enrollments
        enroll_stmt = (
            select(Enrollment)
            .options(
                selectinload(Enrollment.student)
                .selectinload(StudentProfile.user)
            )
            .filter(Enrollment.course_id == course_id, Enrollment.status == "active")
        )
        enroll_res = await self.db.execute(enroll_stmt)
        enrollments = enroll_res.scalars().all()

        # 2. Fetch all course attendance records
        records = await self.record_repo.get_course_stats(course_id)

        rows = []
        for enrollment in enrollments:
            student = enrollment.student
            # Filter records for this specific student
            student_records = [r for r in records if r.student_id == student.id]
            stats = self.analytics_service._calculate_stats(student_records)
            
            rows.append(
                StudentAttendanceReportRow(
                    student_id=student.id,
                    first_name=student.user.first_name,
                    last_name=student.user.last_name,
                    roll_number=student.roll_number,
                    stats=stats
                )
            )
        return rows

    def export_report_to_csv(self, report_rows: List[StudentAttendanceReportRow]) -> str:
        """Converts report data rows to CSV string."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow([
            "Roll Number", "First Name", "Last Name", 
            "Attendance %", "Present Count", "Absent Count", 
            "Late Count", "Excused Count", "Total Sessions"
        ])
        
        for row in report_rows:
            writer.writerow([
                row.roll_number,
                row.first_name,
                row.last_name,
                row.stats.attendance_percentage,
                row.stats.present_count,
                row.stats.absent_count,
                row.stats.late_count,
                row.stats.excused_count,
                row.stats.total_count
            ])
            
        return output.getvalue()
