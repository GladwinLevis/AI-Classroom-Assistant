from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import List, Optional, Dict, Any


class ChatSessionCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)


class ChatSessionRename(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)


class ChatSessionResponse(BaseModel):
    id: UUID
    title: str
    user_id: UUID
    is_archived: bool
    is_pinned: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CitationItem(BaseModel):
    document_name: str
    page_number: Optional[int] = None
    section: Optional[str] = None
    score: float
    text_chunk: str


class ChatMessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    sender: str
    message_text: str
    tokens_prompt: Optional[int] = None
    tokens_response: Optional[int] = None
    latency_ms: Optional[int] = None
    citations: Optional[List[CitationItem]] = None
    is_bookmarked: bool
    feedback: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatMessageCreate(BaseModel):
    message_text: str = Field(..., min_length=1)
    notes_id: Optional[UUID] = None


class MessageBookmarkRequest(BaseModel):
    is_bookmarked: bool


class MessageFeedbackRequest(BaseModel):
    feedback: str = Field(..., min_length=1, max_length=1000)


class SuggestedQuestionsResponse(BaseModel):
    session_id: UUID
    suggestions: List[str] = []
