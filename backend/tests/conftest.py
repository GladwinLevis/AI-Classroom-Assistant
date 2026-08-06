import asyncio
import os
import json
from unittest.mock import MagicMock, patch

os.environ["TESTING"] = "True"
from typing import AsyncGenerator, Generator
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.main import app as fastapi_app
from app.core.config import settings
from app.core.database import get_db, Base

try:
    import google.genai
except ImportError:
    pass

# Set valid test API Key so service level is_mock checks pass during test execution
settings.GOOGLE_API_KEY = "test_live_key_12345"

# Setup separate isolated test database URL (sqlite in-memory with shared cache for multi-connection unit testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///file:testdb?mode=memory&cache=shared&uri=true"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True
)

TestAsyncSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

import app.core.database
app.core.database.AsyncSessionLocal = TestAsyncSessionLocal


class MockUsageMetadata:
    prompt_token_count = 100
    candidates_token_count = 50
    total_token_count = 150


class MockGenAIResponse:
    def __init__(self, text):
        self.text = text
        self.usage_metadata = MockUsageMetadata()


class MockGenAIStreamChunk:
    def __init__(self, text):
        self.text = text


class MockGenAIClient:
    def __init__(self, api_key=None, **kwargs):
        self.models = MagicMock()
        self.models.generate_content.side_effect = self._generate_content
        self.models.generate_content_stream.side_effect = self._generate_content_stream

    def _generate_content(self, *args, **kwargs):
        contents_str = (str(args) + str(kwargs)).lower()

        # 1. Summary / Notes study package check
        if "short_summary" in contents_str or "detailed_summary" in contents_str or "structured study summary" in contents_str or ("notes" in contents_str and "quiz" not in contents_str):
            return MockGenAIResponse(json.dumps({
                "short_summary": "Summary of course notes.",
                "detailed_summary": "Detailed overview of key principles and concepts.",
                "bullet_points": ["Key point 1", "Key point 2"],
                "chapter_wise": "Chapter 1: Intro",
                "key_concepts": ["Concept 1"],
                "definitions": [{"concept": "Python", "definition": "Language"}],
                "formulas": ["A = B + C"],
                "dates": ["2026-07-20"],
                "names": ["Alan Turing"],
                "advantages": "Readability",
                "disadvantages": "Speed",
                "examples": ["Web apps"],
                "faqs": [{"question": "What is Python?", "answer": "Programming language"}],
                "exam_notes": "Focus on basics",
                "revision_notes": "Review syntax",
                "one_page_revision": "Python overview",
                "cheat_sheet": "Cheat sheet notes",
                "flashcards": [{"question": "What is Python?", "answer": "Language", "explanation": "High level"}],
                "mind_map": {"root": "Python", "branches": [{"topic": "Basics", "subtopics": ["Syntax"]}]}
            }))

        # 2. Quiz / Question generation check
        elif ("question" in contents_str or "quiz" in contents_str or "blooms" in contents_str) and "rubric_evaluations" not in contents_str and "student submitted text" not in contents_str:
            return MockGenAIResponse(json.dumps([
                {
                    "question_text": "What is Information Theory?",
                    "question_type": "mcq",
                    "options": ["Study of quantification, storage, and communication of information", "Hardware assembly", "Database indexing", "Operating System design"],
                    "correct_answer": "Study of quantification, storage, and communication of information",
                    "explanation": "Information theory studies the quantification of information.",
                    "points": 1.0,
                    "difficulty": "medium",
                    "blooms_level": "Understand",
                    "estimated_time_seconds": 60,
                    "related_concept": "Information Theory",
                    "recommended_revision_topic": "Basics"
                },
                {
                    "question_text": "Define Entropy in Information Theory.",
                    "question_type": "short_answer",
                    "options": None,
                    "correct_answer": "Average level of information or uncertainty inherent in a variable",
                    "explanation": "Entropy measures uncertainty.",
                    "points": 1.0,
                    "difficulty": "medium",
                    "blooms_level": "Remember",
                    "estimated_time_seconds": 60,
                    "related_concept": "Entropy",
                    "recommended_revision_topic": "Basics"
                },
                {
                    "question_text": "Is Entropy non-negative?",
                    "question_type": "true_false",
                    "options": ["True", "False"],
                    "correct_answer": "True",
                    "explanation": "Entropy is always non-negative for discrete distributions.",
                    "points": 1.0,
                    "difficulty": "easy",
                    "blooms_level": "Remember",
                    "estimated_time_seconds": 30,
                    "related_concept": "Entropy",
                    "recommended_revision_topic": "Basics"
                }
            ]))
        
        # 3. Rubric Assignment Evaluation check
        elif "rubric" in contents_str or "assignment" in contents_str or "student submitted text" in contents_str:
            return MockGenAIResponse(json.dumps({
                "total_score": 85.0,
                "summary_feedback": "Good submission meeting criteria.",
                "rubric_evaluations": [
                    {"criterion_name": "Concept Understanding", "assigned_score": 35.0, "max_score": 40.0, "comments": "Well understood."},
                    {"criterion_name": "Technical Implementation", "assigned_score": 35.0, "max_score": 40.0, "comments": "Solid code logic."},
                    {"criterion_name": "Documentation", "assigned_score": 15.0, "max_score": 20.0, "comments": "Clear writeup."}
                ],
                "strengths": ["Clear organization"],
                "weaknesses": ["Minor typos"],
                "suggestions": ["Add more details"]
            }))

        # 4. Dual fallback
        else:
            return MockGenAIResponse(json.dumps({
                "total_score": 85.0,
                "summary_feedback": "Alan Turing pioneered computation principles with ratio efficiency metric.",
                "short_summary": "Alan Turing pioneered computation principles.",
                "response": "Alan Turing pioneered computation principles with ratio efficiency metric."
            }))

    def _generate_content_stream(self, *args, **kwargs):
        return [
            MockGenAIStreamChunk("Alan Turing pioneered computation theory. "),
            MockGenAIStreamChunk("The computer efficiency metric follows the ratio rule Ratio = Output / Input.")
        ]


@pytest.fixture(autouse=True)
def mock_genai_client():
    with patch("google.genai.Client", side_effect=MockGenAIClient):
        yield


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Overrides pytest event loop to use a session scoped loop."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_test_db() -> AsyncGenerator[None, None]:
    """Creates tables before test execution and drops them afterwards."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yields an isolated database session for testing queries."""
    async with TestAsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Overrides default db session dependency with the test session,
    and returns a test HTTP client.
    """
    async def override_get_db():
        try:
            yield db_session
        finally:
            pass

    fastapi_app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app),
        base_url="http://testserver"
    ) as ac:
        yield ac
        
    fastapi_app.dependency_overrides.clear()
