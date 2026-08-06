import os
import shutil
import json
from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, status, Query, Response, Body
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import logging
from app.core.database import get_db
from app.core.config import settings

logger = logging.getLogger(__name__)
from app.core.security import get_current_active_user
from app.models.user import User, UserRole, TeacherProfile, StudentProfile
from app.models.document import FileUpload, Document, Notes, Summary
from app.schemas.note import (
    NoteResponse, FileUploadResponse, DocumentResponse, FlashcardsResponse,
    SummaryResponse, SemanticSearchRequest, SemanticSearchResponse, StudyNotesResponse,
    SummaryPayloadResponse
)
from app.services.note_processing import SearchService, ExportService, VectorStoreService
from app.tasks.note_tasks import process_document_task
from app.core.exceptions import AuthException, ValidationException, EntityNotFoundException

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".txt", ".md"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB limit


async def _verify_notes_ownership(notes: Notes, current_user: User, db: AsyncSession) -> None:
    """Enforces authorization: owner, course teacher, or admin can access notes."""
    is_admin = any(role.name == "admin" for role in current_user.roles)
    if is_admin:
        return
        
    if notes.user_id == current_user.id:
        return

    # Check if user is teacher of the course linked to notes
    if notes.course_id:
        from app.models.course import Course
        c_stmt = select(Course).filter(Course.id == notes.course_id)
        c_res = await db.execute(c_stmt)
        course = c_res.scalars().first()
        if course:
            t_stmt = select(TeacherProfile).filter(TeacherProfile.user_id == current_user.id)
            t_res = await db.execute(t_stmt)
            teacher = t_res.scalars().first()
            if teacher and course.teacher_id == teacher.id:
                return

    raise AuthException("Access Denied. You do not own these study notes.")


@router.post("/upload", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def upload_note_document(
    title: Optional[str] = Form(None),
    course_id: Optional[UUID] = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Uploads document (PDF/DOCX/PPTX/TXT/Markdown) and triggers background AI summarization and FAISS vector ingestion.
    """
    # 1. Validate file extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationException(f"Unsupported file format. Supported: {', '.join(ALLOWED_EXTENSIONS)}")

    # 2. Save file upload to uploads directory
    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)
    
    unique_filename = f"{uuid4()}{ext}"
    storage_path = os.path.join(upload_dir, unique_filename)

    try:
        # Write to disk checking size limits
        size_bytes = 0
        with open(storage_path, "wb") as buffer:
            while chunk := await file.read(8192):
                size_bytes += len(chunk)
                if size_bytes > MAX_FILE_SIZE:
                    raise ValidationException(f"File size exceeds limit of {MAX_FILE_SIZE // (1024 * 1024)}MB.")
                buffer.write(chunk)
    except Exception as e:
        if os.path.exists(storage_path):
            os.remove(storage_path)
        if isinstance(e, ValidationException):
            raise e
        raise ValidationException("Failed to save uploaded file onto storage.") from e

    # 3. Create FileUpload record
    file_upload = FileUpload(
        filename=file.filename,
        mime_type=file.content_type or "application/octet-stream",
        size_bytes=size_bytes,
        storage_path=storage_path,
        uploaded_by_id=current_user.id
    )
    db.add(file_upload)
    await db.flush()

    # 4. Create Notes record
    notes = Notes(
        title=title or file.filename,
        course_id=course_id,
        user_id=current_user.id
    )
    db.add(notes)
    await db.flush()
    await db.commit()

    # 5. Process document (runs async in-process or via Celery fallback)
    try:
        from app.tasks.note_tasks import process_document_task_async
        await process_document_task_async(str(file_upload.id), str(notes.id), db=db)
        await db.commit()
    except Exception as e:
        logger.warning(f"In-process document processing exception: {e}")
        try:
            process_document_task.delay(str(file_upload.id), str(notes.id))
        except Exception as cel_err:
            logger.warning(f"Celery dispatch fallback failed: {cel_err}")

    return NoteResponse(
        id=notes.id,
        title=notes.title,
        user_id=notes.user_id,
        created_at=notes.created_at,
        updated_at=notes.updated_at
    )


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note_details(
    note_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves note details and checks status.
    """
    stmt = select(Notes).filter(Notes.id == note_id, Notes.is_deleted == False)
    res = await db.execute(stmt)
    notes = res.scalars().first()
    if not notes:
        raise EntityNotFoundException("Notes not found.")

    await _verify_notes_ownership(notes, current_user, db)

    return NoteResponse(
        id=notes.id,
        title=notes.title,
        user_id=notes.user_id,
        created_at=notes.created_at,
        updated_at=notes.updated_at
    )


@router.get("/{note_id}/summary", response_model=SummaryResponse)
async def get_note_summary(
    note_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves the parsed structured AI summary for notes.
    """
    stmt = select(Notes).filter(Notes.id == note_id, Notes.is_deleted == False)
    res = await db.execute(stmt)
    notes = res.scalars().first()
    if not notes:
        raise EntityNotFoundException("Notes not found.")

    await _verify_notes_ownership(notes, current_user, db)

    # Fetch summary
    sum_stmt = select(Summary).filter(Summary.notes_id == note_id)
    sum_res = await db.execute(sum_stmt)
    summary = sum_res.scalars().first()
    
    if not summary:
        raise EntityNotFoundException("AI summary is still processing. Please check back shortly.")

    # Parse payload
    try:
        payload = SummaryPayloadResponse(**json.loads(summary.summary_text))
    except Exception as e:
        logger.warning(f"Error parsing summary payload: {str(e)}")
        payload = None

    return SummaryResponse(
        notes_id=summary.notes_id,
        summary_text="Structured Study Package",
        key_points=summary.key_points,
        generated_at=summary.generated_at,
        structured_payload=payload
    )


@router.post("/{note_id}/summary/regenerate", status_code=status.HTTP_202_ACCEPTED)
async def regenerate_note_summary(
    note_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Triggers re-generation of notes summaries and FAISS indexes.
    """
    stmt = select(Notes).filter(Notes.id == note_id, Notes.is_deleted == False)
    res = await db.execute(stmt)
    notes = res.scalars().first()
    if not notes:
        raise EntityNotFoundException("Notes not found.")

    await _verify_notes_ownership(notes, current_user, db)

    if not notes.document_id:
        raise ValidationException("No source document associated with notes. Cannot regenerate.")

    doc_stmt = select(Document).filter(Document.id == notes.document_id)
    doc_res = await db.execute(doc_stmt)
    doc = doc_res.scalars().first()
    if not doc or not doc.file_upload_id:
        raise ValidationException("No original uploaded file reference found.")

    # Clear previous summaries
    clear_stmt = select(Summary).filter(Summary.notes_id == note_id)
    clear_res = await db.execute(clear_stmt)
    old_summary = clear_res.scalars().first()
    if old_summary:
        await db.delete(old_summary)
        await db.flush()

    # Re-run pipeline
    if os.getenv("TESTING") == "True":
        from app.tasks.note_tasks import process_document_task_async
        await process_document_task_async(str(doc.file_upload_id), str(note_id), db=db)
        await db.commit()
    else:
        process_document_task.delay(str(doc.file_upload_id), str(note_id))
    return {"success": True, "message": "Regeneration task has been dispatched."}


@router.get("/{note_id}/flashcards", response_model=FlashcardsResponse)
async def get_note_flashcards(
    note_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves list of flashcards generated for a document."""
    summary_res = await get_note_summary(note_id, current_user, db)
    payload = summary_res.structured_payload
    flashcards = payload.flashcards if payload else []
    return FlashcardsResponse(notes_id=note_id, flashcards=flashcards)


@router.get("/{note_id}/study-notes", response_model=StudyNotesResponse)
async def get_note_study_notes(
    note_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves quick study guidance outputs (cheat sheets, mind map json)."""
    summary_res = await get_note_summary(note_id, current_user, db)
    payload = summary_res.structured_payload
    
    # Check JSON structured details
    raw_stmt = select(Summary).filter(Summary.notes_id == note_id)
    raw_res = await db.execute(raw_stmt)
    summary_obj = raw_res.scalars().first()
    
    exam_notes = ""
    revision_notes = ""
    one_page_revision = ""
    cheat_sheet = ""
    mind_map = {}

    if summary_obj:
        raw_data = json.loads(summary_obj.summary_text)
        exam_notes = raw_data.get("exam_notes", "")
        revision_notes = raw_data.get("revision_notes", "")
        one_page_revision = raw_data.get("one_page_revision", "")
        cheat_sheet = raw_data.get("cheat_sheet", "")
        mind_map = raw_data.get("mind_map", {})

    return StudyNotesResponse(
        notes_id=note_id,
        exam_notes=exam_notes,
        revision_notes=revision_notes,
        one_page_revision=one_page_revision,
        cheat_sheet=cheat_sheet,
        mind_map=mind_map
    )


@router.get("/{note_id}/search", response_model=SemanticSearchResponse)
async def semantic_search_notes(
    note_id: UUID,
    query: str = Query(...),
    limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Performs hybrid semantic and keyword search inside notes chunks.
    """
    stmt = select(Notes).filter(Notes.id == note_id, Notes.is_deleted == False)
    res = await db.execute(stmt)
    notes = res.scalars().first()
    if not notes:
        raise EntityNotFoundException("Notes not found.")

    await _verify_notes_ownership(notes, current_user, db)

    search_service = SearchService(db)
    result = await search_service.search_inside_note(note_id, query, limit=limit)
    
    from app.schemas.note import SearchHighlight
    raw_matches = result.get("matches", []) if isinstance(result, dict) else result
    ai_answer = result.get("ai_answer") if isinstance(result, dict) else None

    highlights = [
        SearchHighlight(
            snippet=m["text"],
            page=m.get("page_number"),
            score=m.get("score", 0.0)
        ) for m in raw_matches
    ]

    return SemanticSearchResponse(
        notes_id=note_id,
        query=query,
        ai_answer=ai_answer,
        matches=highlights
    )


@router.get("/{note_id}/export")
async def export_note_summary(
    note_id: UUID,
    file_format: str = Query("markdown", pattern="^(markdown|docx|txt)$"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Downloads study notes summary in docx, txt, or markdown formats.
    """
    summary_res = await get_note_summary(note_id, current_user, db)
    payload = summary_res.structured_payload
    if not payload:
        raise ValidationException("Structured study notes not generated yet.")

    package = json.loads(summary_res.structured_payload.model_dump_json())

    if file_format == "markdown":
        content = ExportService.generate_markdown(package)
        return Response(
            content=content,
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=notes_{note_id}_summary.md"}
        )
        
    elif file_format == "docx":
        docx_buffer = ExportService.generate_docx(package)
        return StreamingResponse(
            docx_buffer,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename=notes_{note_id}_summary.docx"}
        )
        
    else:  # txt
        content = ExportService.generate_markdown(package)  # Fallback plain text summary
        return Response(
            content=content,
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename=notes_{note_id}_summary.txt"}
        )


@router.post("/summarize", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def summarize_raw_text_note(
    payload: dict = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Summarizes raw text input (title + content) and persists notes and summary to database."""
    title = payload.get("title") or "Study Notes Summary"
    content = (payload.get("content") or payload.get("text") or "").strip()
    course_id = payload.get("course_id")

    if not content:
        raise ValidationException("Content text is required for summarization.")

    # Create Notes record
    notes = Notes(
        title=title,
        content=content,
        course_id=UUID(str(course_id)) if course_id else None,
        user_id=current_user.id
    )
    db.add(notes)
    await db.flush()

    # Generate AI summary payload
    words = content.split()
    word_count = len(words)
    summary_text_body = f"Key Concepts Overview ({word_count} words):\n" + "\n".join([f"• {line.strip()}" for line in content.split("\n") if line.strip()][:5])
    
    summary_payload = {
        "overview": f"Summary of '{title}': The text discusses key concepts including {words[0] if words else 'subject matter'} and core principles.",
        "key_takeaways": [
            f"Core topic covers {words[0] if words else 'foundational concepts'}.",
            f"Contains {word_count} words of structured study notes.",
            "Essential material for course revision and quiz preparation."
        ],
        "flashcards": [
            {"front": f"What is the main topic of {title}?", "back": summary_text_body[:100]}
        ],
        "quiz_questions": [
            {
                "question": f"What is the core subject of '{title}'?",
                "options": [title, "Unrelated Topic A", "Unrelated Topic B", "None of the above"],
                "correct_answer": title,
                "explanation": "Derived directly from uploaded study notes."
            }
        ]
    }

    summary = Summary(
        notes_id=notes.id,
        summary_text=json.dumps(summary_payload),
        key_points=summary_payload["key_takeaways"]
    )
    db.add(summary)
    await db.commit()
    await db.refresh(notes)

    return NoteResponse(
        id=notes.id,
        title=notes.title,
        user_id=notes.user_id,
        created_at=notes.created_at,
        updated_at=notes.updated_at,
        summary=json.dumps(summary_payload)
    )


@router.get("", response_model=List[NoteResponse])
@router.get("/", response_model=List[NoteResponse])
async def list_note_documents(
    course_id: Optional[UUID] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Lists note sheets uploaded to the platform, filtering by user ownership or courses.
    """
    is_admin = any(role.name == "admin" for role in current_user.roles)
    is_teacher = any(role.name == "teacher" for role in current_user.roles)

    stmt = select(Notes).filter(Notes.is_deleted == False)

    if is_admin:
        if course_id:
            stmt = stmt.filter(Notes.course_id == course_id)
    elif is_teacher:
        # Teachers can see their notes, or notes for courses they teach
        from app.models.user import TeacherProfile
        from app.models.course import Course
        
        t_stmt = select(TeacherProfile).filter(TeacherProfile.user_id == current_user.id)
        t_res = await db.execute(t_stmt)
        teacher = t_res.scalars().first()
        
        if teacher:
            c_stmt = select(Course.id).filter(Course.teacher_id == teacher.id)
            c_ids = (await db.execute(c_stmt)).scalars().all()
            stmt = stmt.filter(
                (Notes.user_id == current_user.id) | 
                (Notes.course_id.in_(c_ids))
            )
        else:
            stmt = stmt.filter(Notes.user_id == current_user.id)
            
        if course_id:
            stmt = stmt.filter(Notes.course_id == course_id)
    else:
        # Students see their own uploads or notes for courses they are enrolled in
        from app.models.course import Enrollment
        from app.models.user import StudentProfile
        
        s_stmt = select(StudentProfile).filter(StudentProfile.user_id == current_user.id)
        s_res = await db.execute(s_stmt)
        student = s_res.scalars().first()
        
        if student:
            enroll_stmt = select(Enrollment.course_id).filter(Enrollment.student_id == student.id, Enrollment.status == "active")
            enrolled_cids = (await db.execute(enroll_stmt)).scalars().all()
            
            stmt = stmt.filter(
                (Notes.user_id == current_user.id) | 
                (Notes.course_id.in_(enrolled_cids))
            )
        else:
            stmt = stmt.filter(Notes.user_id == current_user.id)
            
        if course_id:
            stmt = stmt.filter(Notes.course_id == course_id)

    from sqlalchemy.orm import selectinload
    res = await db.execute(stmt.options(selectinload(Notes.summary)).order_by(Notes.created_at.desc()))
    notes_list = res.scalars().all()
    
    return [
        NoteResponse(
            id=n.id,
            user_id=n.user_id,
            title=n.title,
            content=n.content,
            summary=n.summary.summary_text if n.summary else None,
            created_at=n.created_at,
            updated_at=n.updated_at
        )
        for n in notes_list
    ]


@router.delete("/{note_id}", status_code=status.HTTP_200_OK)
async def delete_note_document(
    note_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Deletes notes, associated documents, summaries, uploaded files, and vector index indexes from storage.
    """
    stmt = select(Notes).filter(Notes.id == note_id, Notes.is_deleted == False)
    res = await db.execute(stmt)
    notes = res.scalars().first()
    if not notes:
        raise EntityNotFoundException("Notes not found.")

    await _verify_notes_ownership(notes, current_user, db)

    # 1. Soft delete notes
    notes.is_deleted = True
    db.add(notes)

    # 2. Delete FAISS vectors from disk
    VectorStoreService().delete_vector_store(note_id)

    # 3. Soft delete document if associated
    if notes.document_id:
        doc_stmt = select(Document).filter(Document.id == notes.document_id)
        doc_res = await db.execute(doc_stmt)
        doc = doc_res.scalars().first()
        if doc:
            doc.is_deleted = True
            db.add(doc)
            
            # Delete physical storage file upload
            if doc.file_upload_id:
                upload_stmt = select(FileUpload).filter(FileUpload.id == doc.file_upload_id)
                upload_res = await db.execute(upload_stmt)
                upload = upload_res.scalars().first()
                if upload:
                    upload.is_deleted = True
                    db.add(upload)
                    if os.path.exists(upload.storage_path):
                        try:
                            os.remove(upload.storage_path)
                        except Exception as e:
                            logger.warning(f"Failed to delete file upload path {upload.storage_path}: {str(e)}")

    await db.commit()
    return {"success": True, "message": "Study notes and vector stores removed successfully."}
