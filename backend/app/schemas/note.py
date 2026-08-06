from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class NoteBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: Optional[str] = None


class NoteCreate(NoteBase):
    pass


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None


class NoteResponse(NoteBase):
    id: UUID
    user_id: UUID
    file_path: Optional[str] = None
    summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FileUploadResponse(BaseModel):
    id: UUID
    filename: str
    mime_type: str
    size_bytes: int
    url: Optional[str] = None
    uploaded_by_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    id: UUID
    title: str
    file_upload_id: Optional[UUID] = None
    doc_metadata: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


from typing import List, Dict

class FlashcardItem(BaseModel):
    question: str
    answer: str
    explanation: Optional[str] = None


class FlashcardsResponse(BaseModel):
    notes_id: UUID
    flashcards: List[FlashcardItem]


class SummaryPayloadResponse(BaseModel):
    short_summary: str
    detailed_summary: str
    bullet_points: List[str] = []
    chapter_wise: Optional[str] = None
    key_concepts: List[str] = []
    definitions: List[Dict[str, str]] = []
    formulas: List[str] = []
    dates: List[str] = []
    names: List[str] = []
    advantages: Optional[str] = None
    disadvantages: Optional[str] = None
    examples: List[str] = []
    faqs: List[Dict[str, str]] = []
    flashcards: List[FlashcardItem] = []


class SummaryResponse(BaseModel):
    notes_id: UUID
    summary_text: str
    key_points: Optional[List[str]] = None
    generated_at: datetime
    structured_payload: Optional[SummaryPayloadResponse] = None

    class Config:
        from_attributes = True


class SemanticSearchRequest(BaseModel):
    query: str
    limit: Optional[int] = Field(5, ge=1, le=20)


class SearchHighlight(BaseModel):
    snippet: str
    page: Optional[int] = None
    score: float


class SemanticSearchResponse(BaseModel):
    notes_id: UUID
    query: str
    ai_answer: Optional[str] = None
    matches: List[SearchHighlight] = []


class StudyNotesResponse(BaseModel):
    notes_id: UUID
    exam_notes: str
    revision_notes: str
    one_page_revision: str
    cheat_sheet: str
    mind_map: dict

