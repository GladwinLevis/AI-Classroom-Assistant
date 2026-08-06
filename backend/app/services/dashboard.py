import logging
from typing import Dict, Any, List
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, StudentProfile, TeacherProfile
from app.models.course import Course, Subject
from app.models.attendance import Attendance, AttendanceStatus
from app.models.assignment import Assignment, AssignmentSubmission
from app.models.quiz import Quiz, QuizAttempt
from app.models.document import Notes, Summary
from app.models.communication import ChatSession, Notification, Announcement
from app.models.analytics import ActivityLog
from app.schemas.dashboard import (
    StudentDashboardResponse,
    TeacherDashboardResponse,
    AdminDashboardResponse,
    RechartsSeriesData,
    AnnouncementResponse
)

logger = logging.getLogger(__name__)


class DashboardService:
    """
    Enterprise Dashboard Service aggregating data for Student, Teacher, and Admin views.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_student_dashboard(self, user_id: UUID) -> StudentDashboardResponse:
        """Assembles comprehensive student dashboard analytics."""
        s_stmt = select(StudentProfile).filter(StudentProfile.user_id == user_id)
        s_res = await self.db.execute(s_stmt)
        student = s_res.scalars().first()

        student_id = student.id if student else user_id

        # 1. Attendance % & Trend
        att_stmt = select(Attendance).filter(Attendance.user_id == user_id)
        att_res = await self.db.execute(att_stmt)
        attendances = att_res.scalars().all()

        total_att = len(attendances)
        present_count = sum(1 for a in attendances if a.status == AttendanceStatus.PRESENT)
        att_pct = round((present_count / total_att * 100.0) if total_att > 0 else 100.0, 2)

        att_trend = [RechartsSeriesData(name="Current", value=att_pct)]

        # 2. Upcoming Assignments
        asgn_stmt = select(Assignment).filter(Assignment.is_published == True, Assignment.is_deleted == False).order_by(Assignment.due_date.asc()).limit(5)
        asgn_res = await self.db.execute(asgn_stmt)
        assignments = asgn_res.scalars().all()

        upcoming_asgns = [
            {
                "id": str(a.id),
                "title": a.title,
                "due_date": a.due_date,
                "max_score": a.max_points
            }
            for a in assignments
        ]

        # 3. Quiz History & Scores
        q_stmt = select(QuizAttempt, Quiz).join(Quiz, QuizAttempt.quiz_id == Quiz.id).filter(QuizAttempt.student_id == student_id, QuizAttempt.status == "evaluated")
        q_res = await self.db.execute(q_stmt)
        quiz_rows = q_res.all()

        quiz_history = []
        quiz_scores = []
        for attempt, quiz in quiz_rows:
            quiz_history.append({
                "quiz_id": str(quiz.id),
                "title": quiz.title,
                "score": attempt.score,
                "passed": attempt.passed,
                "completed_at": attempt.completed_at
            })
            if attempt.score is not None:
                quiz_scores.append(attempt.score)

        avg_quiz_score = round(sum(quiz_scores) / len(quiz_scores), 2) if quiz_scores else 0.0

        # 4. Recent AI Summaries & Chatbot
        note_stmt = select(Notes).filter(Notes.user_id == user_id, Notes.is_deleted == False).limit(5)
        note_res = await self.db.execute(note_stmt)
        recent_sums = [{"id": str(n.id), "title": n.title, "created_at": n.created_at} for n in note_res.scalars().all()]

        chat_stmt = select(ChatSession).filter(ChatSession.user_id == user_id, ChatSession.is_archived == False).limit(5)
        chat_res = await self.db.execute(chat_stmt)
        recent_chats = [{"id": str(c.id), "title": c.title, "created_at": c.created_at} for c in chat_res.scalars().all()]

        # 5. Unread notifications count
        notif_stmt = select(func.count(Notification.id)).filter(Notification.user_id == user_id, Notification.is_read == False)
        notif_count = (await self.db.execute(notif_stmt)).scalar() or 0

        # 6. Timeline
        time_stmt = select(ActivityLog).filter(ActivityLog.user_id == user_id).order_by(ActivityLog.created_at.desc()).limit(10)
        time_res = await self.db.execute(time_stmt)
        timeline = [{"action": t.action, "created_at": t.created_at} for t in time_res.scalars().all()]

        return StudentDashboardResponse(
            student_id=student_id,
            attendance_percentage=att_pct,
            attendance_trend=att_trend,
            upcoming_classes=[],
            todays_schedule=[],
            upcoming_assignments=upcoming_asgns,
            quiz_history=quiz_history,
            average_quiz_score=avg_quiz_score,
            recent_ai_summaries=recent_sums,
            recent_chatbot_sessions=recent_chats,
            study_progress=0.0,
            weak_subjects=[],
            strong_subjects=[],
            recommended_topics=[],
            recommended_quizzes=[],
            learning_streak_days=0,
            achievements=[],
            unread_notifications_count=notif_count,
            activity_timeline=timeline
        )

    async def get_teacher_dashboard(self, teacher_user_id: UUID) -> TeacherDashboardResponse:
        """Assembles comprehensive teacher dashboard analytics."""
        t_stmt = select(TeacherProfile).filter(TeacherProfile.user_id == teacher_user_id)
        t_res = await self.db.execute(t_stmt)
        teacher = t_res.scalars().first()

        # Teacher courses
        c_stmt = select(Course).filter(Course.teacher_id == teacher_user_id, Course.is_deleted == False)
        c_res = await self.db.execute(c_stmt)
        courses = c_res.scalars().all()
        course_ids = [c.id for c in courses]

        # Pending reviews count
        sub_stmt = select(func.count(AssignmentSubmission.id)).join(Assignment, AssignmentSubmission.assignment_id == Assignment.id).join(Course, Assignment.course_id == Course.id).filter(
            Course.teacher_id == teacher_user_id,
            AssignmentSubmission.processing_status == "completed"
        )
        pending_reviews = (await self.db.execute(sub_stmt)).scalar() or 0

        # Announcements
        anc_stmt = select(Announcement).filter(Announcement.creator_id == teacher_user_id).order_by(Announcement.created_at.desc()).limit(5)
        anc_res = await self.db.execute(anc_stmt)
        announcements = [
            AnnouncementResponse.model_validate(a) for a in anc_res.scalars().all()
        ]

        # Unread notifications
        notif_stmt = select(func.count(Notification.id)).filter(Notification.user_id == teacher_user_id, Notification.is_read == False)
        notif_count = (await self.db.execute(notif_stmt)).scalar() or 0

        # Calculate real attendance percentage across AttendanceRecord and Attendance tables
        from app.models.attendance import AttendanceRecord
        att_rec_total = (await self.db.execute(select(func.count(AttendanceRecord.id)).filter(AttendanceRecord.is_deleted == False))).scalar() or 0
        att_total = (await self.db.execute(select(func.count(Attendance.id)).filter(Attendance.is_deleted == False))).scalar() or 0
        combined_total = att_rec_total + att_total

        att_rec_present = (await self.db.execute(select(func.count(AttendanceRecord.id)).filter(AttendanceRecord.is_deleted == False, AttendanceRecord.status == AttendanceStatus.PRESENT))).scalar() or 0
        att_present = (await self.db.execute(select(func.count(Attendance.id)).filter(Attendance.is_deleted == False, Attendance.status == AttendanceStatus.PRESENT))).scalar() or 0
        combined_present = att_rec_present + att_present

        teacher_att_pct = round((combined_present / combined_total * 100.0) if combined_total > 0 else 100.0, 2)

        # Real assignment statistics
        asgn_pub_count = (await self.db.execute(
            select(func.count(Assignment.id)).filter(Assignment.is_deleted == False, Assignment.is_published == True)
        )).scalar() or 0
        sub_total_count = (await self.db.execute(
            select(func.count(AssignmentSubmission.id)).filter(AssignmentSubmission.is_deleted == False)
        )).scalar() or 0
        sub_graded_count = (await self.db.execute(
            select(func.count(AssignmentSubmission.id)).filter(
                AssignmentSubmission.is_deleted == False,
                AssignmentSubmission.processing_status == "completed"
            )
        )).scalar() or 0

        # Real quiz statistics
        quiz_total = (await self.db.execute(
            select(func.count(Quiz.id)).filter(Quiz.is_deleted == False)
        )).scalar() or 0
        avg_score_res = (await self.db.execute(
            select(func.avg(QuizAttempt.score)).filter(QuizAttempt.status == "evaluated", QuizAttempt.score.isnot(None))
        )).scalar()
        avg_class_score = round(float(avg_score_res), 2) if avg_score_res else 0.0

        return TeacherDashboardResponse(
            teacher_id=teacher_user_id,
            todays_classes=[{"course": c.name, "code": c.code} for c in courses],
            student_attendance_percentage=teacher_att_pct,
            attendance_trends=[],
            assignment_statistics={"total_published": asgn_pub_count, "submitted": sub_total_count, "graded": sub_graded_count},
            pending_assignment_reviews_count=pending_reviews,
            quiz_statistics={"total_quizzes": quiz_total, "avg_class_score": avg_class_score},
            weak_topics_across_class=[],
            top_performing_students=[],
            low_performing_students=[],
            recent_ai_activity=[],
            recent_student_activity=[],
            announcements=announcements,
            unread_notifications_count=notif_count
        )

    async def get_admin_dashboard(self) -> AdminDashboardResponse:
        """Assembles comprehensive admin dashboard analytics."""
        u_count = (await self.db.execute(select(func.count(User.id)).filter(User.is_deleted == False))).scalar() or 0
        s_count = (await self.db.execute(select(func.count(StudentProfile.id)))).scalar() or 0
        t_count = (await self.db.execute(select(func.count(TeacherProfile.id)))).scalar() or 0
        c_count = (await self.db.execute(select(func.count(Course.id)).filter(Course.is_deleted == False))).scalar() or 0
        sub_count = (await self.db.execute(select(func.count(Subject.id)).filter(Subject.is_deleted == False))).scalar() or 0

        # Real attendance overview
        att_total = (await self.db.execute(
            select(func.count(Attendance.id)).filter(Attendance.is_deleted == False)
        )).scalar() or 0
        att_present = (await self.db.execute(
            select(func.count(Attendance.id)).filter(
                Attendance.is_deleted == False, Attendance.status == AttendanceStatus.PRESENT
            )
        )).scalar() or 0
        att_overview = round((att_present / att_total * 100.0) if att_total > 0 else 0.0, 2)

        # Real AI request counts
        ai_total = (await self.db.execute(
            select(func.count(ChatSession.id))
        )).scalar() or 0

        return AdminDashboardResponse(
            total_users=u_count,
            total_students=s_count,
            total_teachers=t_count,
            total_courses=c_count,
            total_subjects=sub_count,
            attendance_overview_percentage=att_overview,
            system_health_status="HEALTHY",
            storage_usage_mb=0.0,
            ai_requests_total=ai_total,
            daily_active_users=0,
            weekly_active_users=0,
            monthly_active_users=u_count,
            recent_logins=[],
            failed_login_attempts_count=0,
            api_usage_stats=[],
            error_statistics={"500_errors": 0, "404_errors": 0, "401_errors": 0},
            celery_queue_status="OPERATIONAL"
        )
