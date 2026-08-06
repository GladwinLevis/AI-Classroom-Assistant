import asyncio
import logging
from uuid import UUID
from datetime import datetime, timezone
import json
from sqlalchemy import select

from app.core.celery import celery_app
from app.core.database import AsyncSessionLocal
from app.models.document import FileUpload, Document, Notes, Summary
from app.services.note_processing import DocumentParserService, ChunkingService, EmbeddingService, VectorStoreService, SummaryService

logger = logging.getLogger(__name__)


async def process_document_task_async(file_upload_id_str: str, notes_id_str: str, db=None) -> None:
    """
    Asynchronous implementation of the document ingestion pipeline.
    Optionally accepts a db session to reuse (e.g. for testing transactions).
    """
    file_upload_id = UUID(file_upload_id_str)
    notes_id = UUID(notes_id_str)
    
    logger.info(f"Starting background processing for file upload {file_upload_id} (Notes: {notes_id})")
    
    async def _run(session):
        # 1. Fetch file upload
        stmt = select(FileUpload).filter(FileUpload.id == file_upload_id)
        res = await session.execute(stmt)
        file_upload = res.scalars().first()
        if not file_upload:
            logger.error(f"FileUpload {file_upload_id} not found in database. Aborting.")
            return

        # 2. Extract text from file path
        try:
            raw_text = DocumentParserService.extract_text(file_upload.storage_path, file_upload.mime_type)
        except Exception as e:
            logger.error(f"Error parsing file text: {str(e)}")
            raise

        # 3. Create Document entry
        doc = Document(
            title=file_upload.filename,
            raw_text=raw_text,
            file_upload_id=file_upload_id,
            doc_metadata={"processed_at": datetime.now(timezone.utc).isoformat()}
        )
        session.add(doc)
        await session.flush()

        # Link Notes to this newly parsed document
        notes_stmt = select(Notes).filter(Notes.id == notes_id)
        notes_res = await session.execute(notes_stmt)
        note = notes_res.scalars().first()
        if note:
            note.document_id = doc.id
            note.content = raw_text[:2000]  # Store preview content
            session.add(note)

        # 4. Chunk text
        chunks = ChunkingService.chunk_document(raw_text)
        
        # 5. Embed chunks and save in local FAISS vector store
        if chunks:
            embed_service = EmbeddingService()
            texts = [c["text"] for c in chunks]
            embeddings = embed_service.get_embeddings(texts)
            
            vector_store = VectorStoreService()
            vector_store.save_vector_store(notes_id, chunks, embeddings)

        # 6. Generate Gemini comprehensive summary study package
        package = await SummaryService.generate_comprehensive_study_package(file_upload.filename, raw_text)
        
        # Save Summary in PostgreSQL
        if not isinstance(package, dict):
            package = {"short_summary": str(package), "bullet_points": []}

        summary = Summary(
            notes_id=notes_id,
            summary_text=json.dumps(package),
            key_points=package.get("bullet_points", []),
            generated_at=datetime.now(timezone.utc)
        )
        session.add(summary)

    if db is not None:
        await _run(db)
    else:
        async with AsyncSessionLocal() as session:
            try:
                await _run(session)
                await session.commit()
                logger.info(f"Ingestion pipeline completed successfully for notes {notes_id}")
            except Exception as e:
                logger.exception(f"Fatal error processing document {file_upload_id}: {str(e)}")
                await session.rollback()
                raise


@celery_app.task(name="app.tasks.note_tasks.process_document_task")
def process_document_task(file_upload_id_str: str, notes_id_str: str) -> None:
    """
    Celery task wrapper executing the async pipeline safely in a worker event loop.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(process_document_task_async(file_upload_id_str, notes_id_str))
            return
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    loop.run_until_complete(process_document_task_async(file_upload_id_str, notes_id_str))
