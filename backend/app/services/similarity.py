import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import AssignmentSubmission
from app.services.note_processing import EmbeddingService

logger = logging.getLogger(__name__)


class PlagiarismProvider(ABC):
    """
    Abstract interface for plagiarism and similarity checking engines.
    Allows pluggable integration with Turnitin, Copyleaks, or local embedding engines.
    """
    @abstractmethod
    async def check_similarity(
        self, 
        text: str, 
        assignment_id: UUID, 
        current_submission_id: UUID, 
        db: AsyncSession
    ) -> Dict[str, Any]:
        pass


class LocalEmbeddingPlagiarismProvider(PlagiarismProvider):
    """
    Local embedding similarity comparison using SentenceTransformers and cosine similarity.
    Compares the submitted work against all previous submissions for the same assignment.
    """
    def __init__(self):
        self.embedding_service = EmbeddingService()

    async def check_similarity(
        self, 
        text: str, 
        assignment_id: UUID, 
        current_submission_id: UUID, 
        db: AsyncSession
    ) -> Dict[str, Any]:
        if not text or len(text.strip()) < 20:
            return {
                "plagiarism_score": 0.0,
                "highest_match_submission_id": None,
                "provider": "LocalEmbedding",
                "details": "Submitted text too short for similarity comparison."
            }

        # Query past submissions for the same assignment
        stmt = select(AssignmentSubmission).filter(
            AssignmentSubmission.assignment_id == assignment_id,
            AssignmentSubmission.id != current_submission_id,
            AssignmentSubmission.submitted_text.isnot(None)
        )
        res = await db.execute(stmt)
        past_submissions = res.scalars().all()

        if not past_submissions:
            return {
                "plagiarism_score": 0.0,
                "highest_match_submission_id": None,
                "provider": "LocalEmbedding",
                "details": "No prior submissions found for comparison."
            }

        # Embed target text
        query_vec = self.embedding_service.get_embedding(text)

        highest_score = 0.0
        match_id = None

        import numpy as np

        for sub in past_submissions:
            if not sub.submitted_text:
                continue
            sub_vec = self.embedding_service.get_embedding(sub.submitted_text)
            
            # Compute cosine similarity
            norm_q = np.linalg.norm(query_vec)
            norm_s = np.linalg.norm(sub_vec)
            if norm_q > 0 and norm_s > 0:
                sim = float(np.dot(query_vec, sub_vec) / (norm_q * norm_s))
                if sim > highest_score:
                    highest_score = sim
                    match_id = sub.id

        # Clamp between 0.0 and 1.0
        final_score = round(max(0.0, min(1.0, highest_score)), 4)

        logger.info(
            f"Similarity analysis complete for submission {current_submission_id}: "
            f"Plagiarism Score = {final_score * 100:.1f}%"
        )

        return {
            "plagiarism_score": final_score,
            "highest_match_submission_id": str(match_id) if match_id else None,
            "provider": "LocalEmbedding",
            "details": f"Compared against {len(past_submissions)} prior submissions."
        }



class SimilarityService:
    """
    Service layer for similarity analysis using injectable PlagiarismProvider implementations.
    """
    def __init__(self, provider: Optional[PlagiarismProvider] = None):
        self.provider = provider or LocalEmbeddingPlagiarismProvider()

    async def analyze_submission(
        self, 
        text: str, 
        assignment_id: UUID, 
        current_submission_id: UUID, 
        db: AsyncSession
    ) -> Dict[str, Any]:
        try:
            return await self.provider.check_similarity(text, assignment_id, current_submission_id, db)
        except Exception as e:
            logger.error(f"Error executing similarity check: {str(e)}")
            from fastapi import HTTPException
            raise HTTPException(
                status_code=503,
                detail="Plagiarism check service is currently unavailable. Please try again later."
            )

