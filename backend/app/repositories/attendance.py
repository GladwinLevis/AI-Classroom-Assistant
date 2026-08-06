from typing import List, Optional
from uuid import UUID
from datetime import date
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from app.models.attendance import Attendance, AttendanceSession, AttendanceRecord, AttendanceSessionStatus, AttendanceStatus
from app.repositories.base import BaseRepository


class AttendanceSessionRepository(BaseRepository[AttendanceSession]):
    """
    Repository class encapsulating queries for Attendance Sessions.
    """
    def __init__(self, db):
        super().__init__(AttendanceSession, db)

    async def get_by_id_with_relations(self, session_id: UUID) -> Optional[AttendanceSession]:
        """Fetch a session by ID with preloaded course and classroom relations."""
        result = await self.db.execute(
            select(self.model)
            .options(
                selectinload(self.model.course),
                selectinload(self.model.classroom)
            )
            .filter(self.model.id == session_id, self.model.is_deleted == False)
        )
        return result.scalars().first()

    async def get_sessions_by_course(
        self, course_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[AttendanceSession]:
        """Fetch all sessions belonging to a specific course."""
        result = await self.db.execute(
            select(self.model)
            .filter(self.model.course_id == course_id, self.model.is_deleted == False)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_sessions_by_teacher(
        self, teacher_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[AttendanceSession]:
        """Fetch all sessions managed by a specific teacher."""
        result = await self.db.execute(
            select(self.model)
            .filter(self.model.teacher_id == teacher_id, self.model.is_deleted == False)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_sessions_by_filter(
        self,
        teacher_id: Optional[UUID] = None,
        course_id: Optional[UUID] = None,
        classroom_id: Optional[UUID] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        status: Optional[AttendanceSessionStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[AttendanceSession]:
        """Fetch sessions satisfying query criteria."""
        conditions = [self.model.is_deleted == False]
        if teacher_id:
            conditions.append(self.model.teacher_id == teacher_id)
        if course_id:
            conditions.append(self.model.course_id == course_id)
        if classroom_id:
            conditions.append(self.model.classroom_id == classroom_id)
        if date_from:
            conditions.append(self.model.date >= date_from)
        if date_to:
            conditions.append(self.model.date <= date_to)
        if status:
            conditions.append(self.model.status == status)

        result = await self.db.execute(
            select(self.model)
            .options(
                selectinload(self.model.course),
                selectinload(self.model.classroom)
            )
            .filter(and_(*conditions))
            .order_by(self.model.date.desc(), self.model.start_time.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_active_sessions_for_student(self, student_id: UUID) -> List[AttendanceSession]:
        """Fetch all open/active attendance sessions for courses where the student is enrolled."""
        from app.models.user import StudentProfile
        from app.models.course import Enrollment

        # Subquery finding courses student is enrolled in
        enrolled_courses_stmt = (
            select(Enrollment.course_id)
            .filter(Enrollment.student_id == student_id, Enrollment.status == "active")
        )
        enrolled_course_ids = (await self.db.execute(enrolled_courses_stmt)).scalars().all()

        if not enrolled_course_ids:
            return []

        result = await self.db.execute(
            select(self.model)
            .options(
                selectinload(self.model.course),
                selectinload(self.model.classroom)
            )
            .filter(
                self.model.course_id.in_(enrolled_course_ids),
                self.model.status == AttendanceSessionStatus.ACTIVE,
                self.model.is_deleted == False
            )
        )
        return list(result.scalars().all())


class AttendanceRecordRepository(BaseRepository[AttendanceRecord]):
    """
    Repository class encapsulating queries for Attendance Records.
    """
    def __init__(self, db):
        super().__init__(AttendanceRecord, db)

    async def get_records_by_session(self, session_id: UUID) -> List[AttendanceRecord]:
        """Fetch all student records for a session."""
        result = await self.db.execute(
            select(self.model)
            .options(selectinload(self.model.student))
            .filter(self.model.session_id == session_id, self.model.is_deleted == False)
        )
        return list(result.scalars().all())

    async def get_student_record_for_session(self, session_id: UUID, student_id: UUID) -> Optional[AttendanceRecord]:
        """Fetch specific student's record for a session."""
        result = await self.db.execute(
            select(self.model)
            .filter(
                self.model.session_id == session_id,
                self.model.student_id == student_id,
                self.model.is_deleted == False
            )
        )
        return result.scalars().first()

    async def get_student_history(
        self,
        student_id: UUID,
        course_id: Optional[UUID] = None,
        subject_id: Optional[UUID] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[AttendanceRecord]:
        """Fetch student's personal attendance history with filters."""
        from app.models.course import Course

        conditions = [
            self.model.student_id == student_id,
            self.model.is_deleted == False,
            AttendanceSession.is_deleted == False
        ]
        
        if course_id:
            conditions.append(AttendanceSession.course_id == course_id)
        if subject_id:
            conditions.append(Course.subject_id == subject_id)
        if date_from:
            conditions.append(AttendanceSession.date >= date_from)
        if date_to:
            conditions.append(AttendanceSession.date <= date_to)

        stmt = (
            select(self.model)
            .join(AttendanceSession, self.model.session_id == AttendanceSession.id)
            .join(Course, AttendanceSession.course_id == Course.id)
            .options(
                selectinload(self.model.session).selectinload(AttendanceSession.course),
                selectinload(self.model.session).selectinload(AttendanceSession.classroom)
            )
            .filter(and_(*conditions))
            .order_by(AttendanceSession.date.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_student_overall_stats(self, student_id: UUID) -> List[AttendanceRecord]:
        """Retrieve all active records for a student to calculate metrics."""
        result = await self.db.execute(
            select(self.model)
            .join(AttendanceSession, self.model.session_id == AttendanceSession.id)
            .options(
                selectinload(self.model.session).selectinload(AttendanceSession.course)
            )
            .filter(
                self.model.student_id == student_id,
                self.model.is_deleted == False,
                AttendanceSession.is_deleted == False
            )
        )
        return list(result.scalars().all())

    async def get_course_stats(self, course_id: UUID) -> List[AttendanceRecord]:
        """Retrieve all records belonging to a course's sessions."""
        result = await self.db.execute(
            select(self.model)
            .join(AttendanceSession, self.model.session_id == AttendanceSession.id)
            .options(
                selectinload(self.model.session).selectinload(AttendanceSession.course)
            )
            .filter(
                AttendanceSession.course_id == course_id,
                self.model.is_deleted == False,
                AttendanceSession.is_deleted == False
            )
        )
        return list(result.scalars().all())


class AttendanceDailyRepository(BaseRepository[Attendance]):
    """
    Repository class encapsulating daily school-wide general attendance.
    """
    def __init__(self, db):
        super().__init__(Attendance, db)

    async def get_user_daily_record(self, user_id: UUID, record_date: date) -> Optional[Attendance]:
        """Fetch general school daily attendance record for a user."""
        result = await self.db.execute(
            select(self.model)
            .filter(
                self.model.user_id == user_id,
                self.model.date == record_date,
                self.model.is_deleted == False
            )
        )
        return result.scalars().first()
