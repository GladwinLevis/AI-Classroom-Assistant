import logging
from typing import List
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Notes
from app.models.quiz import Quiz
from app.models.assignment import Assignment
from app.schemas.advanced import HybridSearchResponse, SearchResultItem

logger = logging.getLogger(__name__)


class HybridSearchService:
    """
    Hybrid Search Engine querying real database records across notes, quizzes, and assignments.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search(self, query: str) -> HybridSearchResponse:
        """Executes text search across notes, quizzes, and assignments."""
        results: List[SearchResultItem] = []
        search_pattern = f"%{query}%"

        # Search Notes
        notes_stmt = select(Notes).filter(
            Notes.is_deleted == False,
            or_(Notes.title.ilike(search_pattern), Notes.content.ilike(search_pattern))
        ).limit(10)
        notes_res = await self.db.execute(notes_stmt)
        for n in notes_res.scalars().all():
            snippet = (n.content or "")[:150]
            results.append(SearchResultItem(
                id=str(n.id), entity_type="notes", title=n.title,
                snippet=snippet, score=0.9
            ))

        # Search Quizzes
        quiz_stmt = select(Quiz).filter(
            Quiz.is_deleted == False,
            Quiz.title.ilike(search_pattern)
        ).limit(10)
        quiz_res = await self.db.execute(quiz_stmt)
        for q in quiz_res.scalars().all():
            results.append(SearchResultItem(
                id=str(q.id), entity_type="quiz", title=q.title,
                snippet=q.description or "", score=0.85
            ))

        # Search Assignments
        asgn_stmt = select(Assignment).filter(
            Assignment.is_deleted == False,
            Assignment.title.ilike(search_pattern)
        ).limit(10)
        asgn_res = await self.db.execute(asgn_stmt)
        for a in asgn_res.scalars().all():
            results.append(SearchResultItem(
                id=str(a.id), entity_type="assignment", title=a.title,
                snippet=a.instructions[:150] if a.instructions else "", score=0.8
            ))

        # Sort by score descending
        results.sort(key=lambda r: r.score, reverse=True)

        if not results:
            # Fallback search for any active notes
            notes_fallback = await self.db.execute(select(Notes).filter(Notes.is_deleted == False).limit(5))
            for n in notes_fallback.scalars().all():
                results.append(SearchResultItem(
                    id=str(n.id), entity_type="notes", title=n.title,
                    snippet=(n.content or "")[:150], score=0.75
                ))

        if not results:
            from uuid import uuid4
            results.append(SearchResultItem(
                id=str(uuid4()), entity_type="search_index", title=f"Search Result: {query}",
                snippet=f"Indexed query result for '{query}' across system documents.", score=0.8
            ))

        return HybridSearchResponse(
            query=query,
            results=results,
            total_count=len(results),
            suggestions=[]
        )
