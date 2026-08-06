import logging
from typing import Dict, Any, List
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, StudentProfile, TeacherProfile
from app.models.course import Course, Subject
from app.models.assignment import Assignment
from app.models.quiz import Quiz
from app.models.document import FileUpload
from app.models.communication import Announcement

logger = logging.getLogger(__name__)


class SearchService:
    """
    Enterprise Global Search Service indexing students, teachers, assignments, quizzes, documents, courses, and announcements.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def global_search(self, query: str) -> Dict[str, List[Dict[str, Any]]]:
        """Executes multi-entity search across the platform."""
        q_pattern = f"%{query}%"

        # 1. Search Users (Students & Teachers)
        u_stmt = select(User).filter(
            User.is_deleted == False,
            or_(User.first_name.ilike(q_pattern), User.last_name.ilike(q_pattern), User.email.ilike(q_pattern))
        ).limit(10)
        u_res = await self.db.execute(u_stmt)
        users = u_res.scalars().all()

        students = [{"id": str(u.id), "name": f"{u.first_name} {u.last_name}", "email": u.email} for u in users]
        teachers = [{"id": str(u.id), "name": f"{u.first_name} {u.last_name}", "email": u.email} for u in users]

        # 2. Search Assignments
        asgn_stmt = select(Assignment).filter(Assignment.is_deleted == False, Assignment.title.ilike(q_pattern)).limit(10)
        asgn_res = await self.db.execute(asgn_stmt)
        assignments = [{"id": str(a.id), "title": a.title, "due_date": a.due_date} for a in asgn_res.scalars().all()]

        # 3. Search Quizzes
        quiz_stmt = select(Quiz).filter(Quiz.is_deleted == False, Quiz.title.ilike(q_pattern)).limit(10)
        quiz_res = await self.db.execute(quiz_stmt)
        quizzes = [{"id": str(q.id), "title": q.title, "difficulty": q.difficulty} for q in quiz_res.scalars().all()]

        # 4. Search Documents
        doc_stmt = select(FileUpload).filter(FileUpload.is_deleted == False, FileUpload.filename.ilike(q_pattern)).limit(10)
        doc_res = await self.db.execute(doc_stmt)
        documents = [{"id": str(d.id), "filename": d.filename, "size": d.size_bytes} for d in doc_res.scalars().all()]

        # 5. Search Courses
        c_stmt = select(Course).filter(Course.is_deleted == False, Course.name.ilike(q_pattern)).limit(10)
        c_res = await self.db.execute(c_stmt)
        courses = [{"id": str(c.id), "name": c.name, "code": c.code} for c in c_res.scalars().all()]

        # 6. Search Announcements
        anc_stmt = select(Announcement).filter(Announcement.is_deleted == False, Announcement.title.ilike(q_pattern)).limit(10)
        anc_res = await self.db.execute(anc_stmt)
        announcements = [{"id": str(a.id), "title": a.title, "content": a.content[:100]} for a in anc_res.scalars().all()]

        return {
            "students": students,
            "teachers": teachers,
            "assignments": assignments,
            "quizzes": quizzes,
            "documents": documents,
            "courses": courses,
            "announcements": announcements
        }
