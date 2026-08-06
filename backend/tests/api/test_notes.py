import os
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.security import create_access_token, get_password_hash
from app.models.security import Role
from app.models.user import User, UserRole, StudentProfile
from app.models.document import FileUpload, Document, Notes, Summary
from app.services.note_processing import VectorStoreService


@pytest_asyncio.fixture
async def seed_user(db_session: AsyncSession):
    """Seeds a student user and matching profile."""
    stmt = select(Role).filter(Role.name == UserRole.STUDENT.value)
    res = await db_session.execute(stmt)
    role = res.scalars().first()
    if not role:
        role = Role(name=UserRole.STUDENT.value, description="Student role")
        db_session.add(role)
        await db_session.flush()

    student_user = User(
        email="notes_student@example.com",
        hashed_password=get_password_hash("Password123!"),
        first_name="Alice",
        last_name="Green",
        is_active=True,
        is_verified=True,
        roles=[role]
    )
    db_session.add(student_user)
    await db_session.flush()

    student_profile = StudentProfile(
        user_id=student_user.id,
        roll_number="CS-NOTES-01",
        academic_year="2026"
    )
    db_session.add(student_profile)
    await db_session.flush()
    await db_session.commit()

    return student_user


def get_headers(user_id: UUID) -> dict:
    token = create_access_token(data={"sub": str(user_id), "role": UserRole.STUDENT.value})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_notes_full_processing_and_search_flow(client: AsyncClient, seed_user: User, db_session: AsyncSession):
    """
    Tests uploading a notes text file, running the ingestion, retrieving summaries, flashcards, semantic search, exports, and deletion.
    """
    headers = get_headers(seed_user.id)

    # 1. Upload file
    file_content = (
        "Introduction to Python Programming.\n\n"
        "Python is a high-level, interpreted programming language. It is known for its readability and clean syntax.\n\n"
        "Formula representation of efficiency is Ratio = Output / Input. Alan Turing pioneered computing principles.\n\n"
        "Scalability is the ability of a system to grow handling more workload cleanly."
    )
    file_tuple = ("test_notes.txt", file_content.encode("utf-8"), "text/plain")

    form_data = {
        "title": "Python Programming Overview"
    }

    response = await client.post(
        "/api/v1/notes/upload",
        data=form_data,
        files={"file": file_tuple},
        headers=headers
    )
    assert response.status_code == 201
    notes_data = response.json()
    notes_id = UUID(notes_data["id"])
    assert notes_data["title"] == "Python Programming Overview"

    # Verify background data creation in DB (Celery task is run synchronously in eager mode)
    db_session.expire_all()
    stmt = select(Notes).filter(Notes.id == notes_id)
    res = await db_session.execute(stmt)
    note = res.scalars().first()
    assert note is not None
    assert note.document_id is not None

    doc_stmt = select(Document).filter(Document.id == note.document_id)
    doc_res = await db_session.execute(doc_stmt)
    doc = doc_res.scalars().first()
    assert doc is not None
    assert "Python is a high-level" in doc.raw_text

    # 2. Retrieve summary payload
    sum_res = await client.get(f"/api/v1/notes/{notes_id}/summary", headers=headers)
    assert sum_res.status_code == 200
    summary_data = sum_res.json()
    assert summary_data["structured_payload"] is not None
    assert "short_summary" in summary_data["structured_payload"]
    assert len(summary_data["key_points"]) > 0

    # 3. Retrieve flashcards
    fc_res = await client.get(f"/api/v1/notes/{notes_id}/flashcards", headers=headers)
    assert fc_res.status_code == 200
    fc_data = fc_res.json()
    assert len(fc_data["flashcards"]) > 0
    assert "question" in fc_data["flashcards"][0]

    # 4. Retrieve study notes (cheat sheets, mind map json)
    sn_res = await client.get(f"/api/v1/notes/{notes_id}/study-notes", headers=headers)
    assert sn_res.status_code == 200
    sn_data = sn_res.json()
    assert sn_data["cheat_sheet"] != ""
    assert "root" in sn_data["mind_map"]

    # 5. Semantic & hybrid search inside uploaded notes
    search_res = await client.get(f"/api/v1/notes/{notes_id}/search?query=scalability&limit=2", headers=headers)
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert len(search_data["matches"]) > 0
    assert "score" in search_data["matches"][0]

    # 6. Export summaries (Markdown)
    export_res = await client.get(f"/api/v1/notes/{notes_id}/export?file_format=markdown", headers=headers)
    assert export_res.status_code == 200
    assert "# " in export_res.text
    assert "Short Summary" in export_res.text

    # Export summaries (Docx)
    export_docx = await client.get(f"/api/v1/notes/{notes_id}/export?file_format=docx", headers=headers)
    assert export_docx.status_code == 200
    assert len(export_docx.content) > 100  # valid docx file bytes

    # 7. Delete notes (verify FAISS cleaned up, soft deleted database records)
    del_res = await client.delete(f"/api/v1/notes/{notes_id}", headers=headers)
    assert del_res.status_code == 200

    # Verify soft deleted in DB
    db_session.expire_all()
    note_check = (await db_session.execute(select(Notes).filter(Notes.id == notes_id))).scalars().first()
    assert note_check.is_deleted is True

    # Verify FAISS files cleaned up
    paths = VectorStoreService()._get_paths(notes_id)
    assert not os.path.exists(paths["index"])
    assert not os.path.exists(paths["meta"])
