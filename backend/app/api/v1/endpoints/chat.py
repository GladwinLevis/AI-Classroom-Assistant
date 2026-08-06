import logging
from typing import List, Optional
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, Query, Path, Body, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ValidationException, EntityNotFoundException, AuthException
from app.models.user import User
from app.models.communication import ChatSession, ChatMessage
from app.schemas.chat import (
    ChatSessionCreate,
    ChatSessionRename,
    ChatSessionResponse,
    ChatMessageResponse,
    ChatMessageCreate,
    MessageBookmarkRequest,
    MessageFeedbackRequest,
    SuggestedQuestionsResponse
)
from app.core.security import get_current_active_user
from app.services.chat_bot import ChatService, ChatExportService, SuggestionService, PromptBuilderService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/create", response_model=ChatSessionResponse, status_code=201)
@router.post("/sessions", response_model=ChatSessionResponse, status_code=201)
@router.post("", response_model=ChatSessionResponse, status_code=201)
@router.post("/", response_model=ChatSessionResponse, status_code=201)
async def create_chat_session(
    payload: ChatSessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Initializes a new chatbot conversation session."""
    chat_service = ChatService(db)
    session = await chat_service.get_or_create_session(
        user_id=current_user.id,
        title=payload.title
    )
    return session


async def _process_chat_message(
    session_id: Optional[UUID],
    notes_id: Optional[UUID],
    payload: Optional[dict],
    current_user: User,
    db: AsyncSession
):
    message_text = ""
    if payload:
        message_text = payload.get("message_text") or payload.get("message") or payload.get("content") or ""
    
    if message_text:
        PromptBuilderService.sanitize_input(message_text)

    chat_service = ChatService(db)
    
    target_session_id = session_id or (payload.get("session_id") if payload else None)
    if not target_session_id:
        sess = await chat_service.get_or_create_session(user_id=current_user.id, title=message_text[:30] or "New Chat")
        target_session_id = sess.id
    else:
        if isinstance(target_session_id, str):
            target_session_id = UUID(target_session_id)

    response_tokens = []
    async for chunk in chat_service.process_user_message(
        user_id=current_user.id,
        session_id=target_session_id,
        message_text=message_text,
        notes_id=notes_id
    ):
        response_tokens.append(chunk)

    full_response = "".join(response_tokens).replace("data: ", "").replace("\n\n", " ").strip()
    return {
        "id": str(uuid4()),
        "session_id": str(target_session_id),
        "response": full_response,
        "message": full_response,
        "ai_message": full_response,
        "content": full_response
    }


@router.post("/send")
@router.post("/message")
async def send_chat_message_query(
    session_id: Optional[UUID] = Query(None),
    notes_id: Optional[UUID] = Query(None),
    payload: Optional[dict] = Body(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Sends message to chat session and returns AI response."""
    return await _process_chat_message(
        session_id=session_id,
        notes_id=notes_id,
        payload=payload,
        current_user=current_user,
        db=db
    )


@router.post("/sessions/{session_id}/messages")
async def send_chat_message_path(
    session_id: UUID = Path(...),
    notes_id: Optional[UUID] = Query(None),
    payload: Optional[dict] = Body(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Sends message to chat session via path parameter."""
    return await _process_chat_message(
        session_id=session_id,
        notes_id=notes_id,
        payload=payload,
        current_user=current_user,
        db=db
    )


@router.get("/sessions", response_model=List[ChatSessionResponse])
@router.get("/history", response_model=List[ChatSessionResponse])
async def get_chat_history(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Lists all active chat sessions for the authenticated user."""
    stmt = (
        select(ChatSession)
        .filter(ChatSession.user_id == current_user.id, ChatSession.is_deleted == False)
        .order_by(ChatSession.is_pinned.desc(), ChatSession.updated_at.desc())
    )
    res = await db.execute(stmt)
    sessions = res.scalars().all()
    return sessions


@router.get("/session/{id}", response_model=List[ChatMessageResponse])
async def get_chat_session_details(
    id: UUID = Path(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves full conversation history for a single chat session."""
    # Verify ownership
    stmt = select(ChatSession).filter(ChatSession.id == id, ChatSession.is_deleted == False)
    res = await db.execute(stmt)
    sess = res.scalars().first()
    if not sess:
        raise EntityNotFoundException("Chat session not found.")
    if sess.user_id != current_user.id:
        raise AuthException("Access denied. You do not own this chat session.")

    msg_stmt = (
        select(ChatMessage)
        .filter(ChatMessage.session_id == id)
        .order_by(ChatMessage.created_at.asc())
    )
    msg_res = await db.execute(msg_stmt)
    messages = msg_res.scalars().all()
    
    # Parse citations JSON to pydantic list format
    response_list = []
    for m in messages:
        cits = None
        if m.citations and "citations" in m.citations:
            cits = m.citations["citations"]
        
        response_list.append(
            ChatMessageResponse(
                id=m.id,
                session_id=m.session_id,
                sender=m.sender,
                message_text=m.message_text,
                tokens_prompt=m.tokens_prompt,
                tokens_response=m.tokens_response,
                latency_ms=m.latency_ms,
                citations=cits,
                is_bookmarked=m.is_bookmarked,
                feedback=m.feedback,
                created_at=m.created_at
            )
        )
    return response_list


@router.put("/rename", response_model=ChatSessionResponse)
async def rename_chat_session(
    session_id: UUID = Query(...),
    payload: ChatSessionRename = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Renames an existing chat session."""
    stmt = select(ChatSession).filter(ChatSession.id == session_id, ChatSession.is_deleted == False)
    res = await db.execute(stmt)
    sess = res.scalars().first()
    if not sess:
        raise EntityNotFoundException("Chat session not found.")
    if sess.user_id != current_user.id:
        raise AuthException("Access denied. You do not own this chat session.")

    sess.title = payload.title
    db.add(sess)
    await db.commit()
    await db.refresh(sess)
    return sess


@router.delete("/session/{id}", status_code=200)
async def delete_chat_session(
    id: UUID = Path(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Soft deletes a chat session and all its associated logs."""
    stmt = select(ChatSession).filter(ChatSession.id == id, ChatSession.is_deleted == False)
    res = await db.execute(stmt)
    sess = res.scalars().first()
    if not sess:
        raise EntityNotFoundException("Chat session not found.")
    if sess.user_id != current_user.id:
        raise AuthException("Access denied. You do not own this chat session.")

    sess.is_deleted = True
    db.add(sess)
    await db.commit()
    return {"success": True, "message": "Chat session deleted successfully."}


@router.post("/export")
async def export_chat_history(
    session_id: UUID = Query(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Exports full conversation logs of a session as a downloadable Markdown stream."""
    stmt = select(ChatSession).filter(ChatSession.id == session_id, ChatSession.is_deleted == False)
    res = await db.execute(stmt)
    sess = res.scalars().first()
    if not sess:
        raise EntityNotFoundException("Chat session not found.")
    if sess.user_id != current_user.id:
        raise AuthException("Access denied. You do not own this chat session.")

    # Eager load messages
    msg_stmt = select(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc())
    msg_res = await db.execute(msg_stmt)
    messages = list(msg_res.scalars().all())

    md_content = ChatExportService.export_as_markdown(sess, messages)
    
    return StreamingResponse(
        iter([md_content]),
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=chat_{session_id}.md"}
    )


@router.post("/bookmark/{message_id}", response_model=ChatMessageResponse)
async def toggle_message_bookmark(
    message_id: UUID = Path(...),
    payload: MessageBookmarkRequest = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Bookmarks or unbookmarks an individual message in a chat history."""
    stmt = select(ChatMessage).filter(ChatMessage.id == message_id)
    res = await db.execute(stmt)
    msg = res.scalars().first()
    if not msg:
        raise EntityNotFoundException("Chat message not found.")
    
    # Check session ownership
    sess_stmt = select(ChatSession).filter(ChatSession.id == msg.session_id)
    sess_res = await db.execute(sess_stmt)
    sess = sess_res.scalars().first()
    if not sess or sess.user_id != current_user.id:
        raise AuthException("Access denied. You do not own this message log.")

    msg.is_bookmarked = payload.is_bookmarked
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    
    cits = None
    if msg.citations and "citations" in msg.citations:
        cits = msg.citations["citations"]

    return ChatMessageResponse(
        id=msg.id,
        session_id=msg.session_id,
        sender=msg.sender,
        message_text=msg.message_text,
        tokens_prompt=msg.tokens_prompt,
        tokens_response=msg.tokens_response,
        latency_ms=msg.latency_ms,
        citations=cits,
        is_bookmarked=msg.is_bookmarked,
        feedback=msg.feedback,
        created_at=msg.created_at
    )


@router.post("/feedback/{message_id}", response_model=ChatMessageResponse)
async def submit_message_feedback(
    message_id: UUID = Path(...),
    payload: MessageFeedbackRequest = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Submits educational rating feedback for an individual AI chatbot response."""
    stmt = select(ChatMessage).filter(ChatMessage.id == message_id)
    res = await db.execute(stmt)
    msg = res.scalars().first()
    if not msg:
        raise EntityNotFoundException("Chat message not found.")
        
    sess_stmt = select(ChatSession).filter(ChatSession.id == msg.session_id)
    sess_res = await db.execute(sess_stmt)
    sess = sess_res.scalars().first()
    if not sess or sess.user_id != current_user.id:
        raise AuthException("Access denied. You do not own this message log.")

    msg.feedback = payload.feedback
    db.add(msg)
    await db.commit()
    await db.refresh(msg)

    cits = None
    if msg.citations and "citations" in msg.citations:
        cits = msg.citations["citations"]

    return ChatMessageResponse(
        id=msg.id,
        session_id=msg.session_id,
        sender=msg.sender,
        message_text=msg.message_text,
        tokens_prompt=msg.tokens_prompt,
        tokens_response=msg.tokens_response,
        latency_ms=msg.latency_ms,
        citations=cits,
        is_bookmarked=msg.is_bookmarked,
        feedback=msg.feedback,
        created_at=msg.created_at
    )


@router.get("/suggestions/{session_id}", response_model=SuggestedQuestionsResponse)
async def get_study_suggestions(
    session_id: UUID = Path(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Generates study revision queries based on conversation history."""
    stmt = select(ChatSession).filter(ChatSession.id == session_id, ChatSession.is_deleted == False)
    res = await db.execute(stmt)
    sess = res.scalars().first()
    if not sess:
        raise EntityNotFoundException("Chat session not found.")
    if sess.user_id != current_user.id:
        raise AuthException("Access denied.")

    # Get last message to formulate recommendations
    msg_stmt = (
        select(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(1)
    )
    msg_res = await db.execute(msg_stmt)
    last_msg = msg_res.scalars().first()
    
    query = ""
    ans = ""
    if last_msg:
        if last_msg.sender == "assistant":
            ans = last_msg.message_text
        else:
            query = last_msg.message_text

    suggestions = SuggestionService.generate_suggestions(query, ans)
    return SuggestedQuestionsResponse(
        session_id=session_id,
        suggestions=suggestions
    )
