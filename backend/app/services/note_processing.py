import os
import logging
import fitz  # PyMuPDF
import docx
import pptx
import numpy as np
import faiss
import json
import csv
import io
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.core.exceptions import ValidationException, EntityNotFoundException, AuthException
from app.models.document import FileUpload, Document, Notes, Summary
from app.models.user import User

logger = logging.getLogger(__name__)

# Global lazy loaded embedding model to save resources
_embedding_model: Optional[SentenceTransformer] = None

def get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        logger.info("Initializing SentenceTransformer model: all-MiniLM-L6-v2")
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedding_model


class DocumentParserService:
    """
    Service to extract raw text, structures, headings and titles from various file formats.
    """
    @staticmethod
    def extract_text(file_path: str, mime_type: str) -> str:
        """Determines the file extension and extracts content."""
        if not os.path.exists(file_path):
            raise EntityNotFoundException(f"Target file path {file_path} does not exist.")

        logger.info(f"Extracting text from {file_path} ({mime_type})")
        
        # Mappings
        if "pdf" in mime_type or file_path.lower().endswith(".pdf"):
            return DocumentParserService._parse_pdf(file_path)
        elif "wordprocessingml" in mime_type or file_path.lower().endswith(".docx"):
            return DocumentParserService._parse_docx(file_path)
        elif "presentationml" in mime_type or file_path.lower().endswith(".pptx"):
            return DocumentParserService._parse_pptx(file_path)
        else:
            # Fallback to plain text
            return DocumentParserService._parse_txt(file_path)

    @staticmethod
    def _parse_pdf(file_path: str) -> str:
        """Parses PDF page text using PyMuPDF."""
        text_parts = []
        with fitz.open(file_path) as doc:
            for page in doc:
                text_parts.append(page.get_text())
        return DocumentParserService.clean_text("\n".join(text_parts))

    @staticmethod
    def _parse_docx(file_path: str) -> str:
        """Parses Microsoft Word paragraphs."""
        doc = docx.Document(file_path)
        text_parts = [p.text for p in doc.paragraphs if p.text]
        return DocumentParserService.clean_text("\n".join(text_parts))

    @staticmethod
    def _parse_pptx(file_path: str) -> str:
        """Parses shapes and tables inside Microsoft PowerPoint slides."""
        prs = pptx.Presentation(file_path)
        text_parts = []
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text:
                    text_parts.append(shape.text)
        return DocumentParserService.clean_text("\n".join(text_parts))

    @staticmethod
    def _parse_txt(file_path: str) -> str:
        """Reads plaintext files safely encoding them."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return DocumentParserService.clean_text(f.read())
        except UnicodeDecodeError:
            with open(file_path, "r", encoding="latin-1") as f:
                return DocumentParserService.clean_text(f.read())

    @staticmethod
    def clean_text(text: str) -> str:
        """Removes excessive blank lines, spaces, and normalizes characters."""
        # Normalize encoding space characters
        text = text.replace("\xa0", " ")
        # Remove duplicate spaces
        text = re.sub(r"[ \t]+", " ", text)
        # Remove excessive empty lines
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


class ChunkingService:
    """
    Splits long documents into text chunks for search and indexing.
    """
    @staticmethod
    def chunk_document(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
        """
        Splits text with overlaps. Returns list of dicts: {"text": chunk, "index": i}.
        """
        if not text:
            return []
            
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = min(start + chunk_size, text_len)
            chunk = text[start:end]
            chunks.append({
                "text": chunk,
                "index": len(chunks),
                "start_char": start,
                "end_char": end
            })
            start += (chunk_size - overlap)
            if start >= text_len or chunk_size <= overlap:
                break
                
        return chunks


class EmbeddingService:
    """
    Generates embedding vectors using SentenceTransformers.
    """
    def __init__(self):
        self.model = get_embedding_model()

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Converts text segments to 384-dimensional floating vector maps."""
        if not texts:
            return []
        embeddings = self.model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()

    def get_embedding(self, text: str) -> List[float]:
        """Converts single text string to embedding vector."""
        if not text:
            return []
        res = self.get_embeddings([text])
        return res[0] if res else []


class VectorStoreService:
    """
    Saves and queries local FAISS indexes on disk.
    """
    def __init__(self, index_dir: str = "./vector_indices"):
        self.index_dir = index_dir
        os.makedirs(index_dir, exist_ok=True)
        self.embed_service = EmbeddingService()

    def _get_paths(self, notes_id: UUID) -> Dict[str, str]:
        base = os.path.join(self.index_dir, str(notes_id))
        return {
            "index": f"{base}.index",
            "meta": f"{base}.json"
        }

    def save_vector_store(self, notes_id: UUID, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        """Creates FAISS index and stores accompanying text metadata to disk."""
        paths = self._get_paths(notes_id)
        
        # 1. Create FAISS index
        embeddings_np = np.array(embeddings, dtype=np.float32)
        dimension = embeddings_np.shape[1]
        
        index = faiss.IndexFlatIP(dimension)  # Inner Product (Cosine similarity if normalized)
        # Normalize vectors for Cosine Similarity
        faiss.normalize_L2(embeddings_np)
        index.add(embeddings_np)
        
        # 2. Write files
        faiss.write_index(index, paths["index"])
        
        # Save chunks metadata mapping
        with open(paths["meta"], "w", encoding="utf-8") as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Saved FAISS index for notes ID {notes_id}")

    def semantic_search(self, notes_id: UUID, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Queries local FAISS index with sentence embeddings."""
        paths = self._get_paths(notes_id)
        if not os.path.exists(paths["index"]) or not os.path.exists(paths["meta"]):
            logger.warning(f"No FAISS index found on disk for notes {notes_id}")
            return []

        # 1. Load index and metadata
        index = faiss.read_index(paths["index"])
        with open(paths["meta"], "r", encoding="utf-8") as f:
            chunks = json.load(f)

        # 2. Embed query
        query_vector = self.embed_service.get_embeddings([query])
        query_np = np.array(query_vector, dtype=np.float32)
        faiss.normalize_L2(query_np)

        # 3. Query index
        scores, indices = index.search(query_np, min(limit, index.ntotal))
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1 or idx >= len(chunks):
                continue
            item = chunks[idx]
            if isinstance(item, dict):
                chunk = item.copy()
            else:
                chunk = {"text": str(item), "index": idx}
            chunk["score"] = float(score)
            results.append(chunk)
            
        return results

    def delete_vector_store(self, notes_id: UUID):
        """Deletes FAISS files associated with notes."""
        paths = self._get_paths(notes_id)
        for p in paths.values():
            if os.path.exists(p):
                try:
                    os.remove(p)
                except Exception as e:
                    logger.warning(f"Error removing FAISS file {p}: {str(e)}")


class SummaryService:
    """
    Wraps Gemini AI generation, formatting summaries, concepts, bullet points, pros/cons.
    """
    @staticmethod
    async def generate_comprehensive_study_package(title: str, text: str) -> Dict[str, Any]:
        """
        Invokes Gemini API. Falls back to mock generator if API key is invalid/missing.
        """
        # Crop context to prevent context limits in mock/free keys
        sample_text = text[:15000]
        
        # Check mock setup
        api_key = settings.GOOGLE_API_KEY
        is_mock = (not api_key or api_key.startswith("mock")) and os.getenv("TESTING") != "True"

        if is_mock:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=503,
                detail="AI summary service is currently unavailable. Please configure a valid API key."
            )

        logger.info("Invoking live Gemini GenAI API for document summarization.")
        try:
            from google import genai
            from google.genai import types
            
            client = genai.Client(api_key=api_key)
            prompt = (
                f"You are an expert AI study companion. Generate a comprehensive structured study summary package "
                f"for the document titled '{title}'. You MUST return the output ONLY as a valid JSON object matching "
                f"this schema exactly without markdown formatting or blocks. "
                f"JSON Schema:\n"
                f"{{\n"
                f"  \"short_summary\": \"string summary of 3 sentences\",\n"
                f"  \"detailed_summary\": \"string of 2-3 paragraphs\",\n"
                f"  \"bullet_points\": [\"string of key points\", ...],\n"
                f"  \"chapter_wise\": \"string chapter-by-chapter outline\",\n"
                f"  \"key_concepts\": [\"concept name\", ...],\n"
                f"  \"definitions\": [{{\"concept\": \"...\", \"definition\": \"...\"}}, ...],\n"
                f"  \"formulas\": [\"equation or formula definition\", ...],\n"
                f"  \"dates\": [\"date: event description\", ...],\n"
                f"  \"names\": [\"name: historical/scientific importance\", ...],\n"
                f"  \"advantages\": \"string pros/benefits outline\",\n"
                f"  \"disadvantages\": \"string cons/downsides outline\",\n"
                f"  \"examples\": [\"practical example text\", ...],\n"
                f"  \"faqs\": [{{\"question\": \"...\", \"answer\": \"...\"}}, ...],\n"
                f"  \"exam_notes\": \"string target exam tips\",\n"
                f"  \"revision_notes\": \"string brief study highlights\",\n"
                f"  \"one_page_revision\": \"string extremely compact overview\",\n"
                f"  \"cheat_sheet\": \"string equations/quick guides\",\n"
                f"  \"flashcards\": [{{\"question\": \"...\", \"answer\": \"...\", \"explanation\": \"...\"}}, ...],\n"
                f"  \"mind_map\": {{\n"
                f"     \"root\": \"string root topic title\",\n"
                f"     \"branches\": [{{\"topic\": \"branch topic title\", \"subtopics\": [\"subtopic string\", ...]}}, ...]\n"
                f"  }}\n"
                f"}}\n"
                f"Document text context:\n{sample_text}"
            )
            
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                )
            )
            
            res_text = response.text.strip()
            # Safety checks for code blocks
            if res_text.startswith("```"):
                res_text = re.sub(r"^```(?:json)?\n|```$", "", res_text, flags=re.MULTILINE).strip()
                
            return json.loads(res_text)
            
        except Exception as e:
            logger.error(f"Error calling live Gemini API: {str(e)}")
            from fastapi import HTTPException
            raise HTTPException(
                status_code=503,
                detail="AI summary service is currently unavailable. Please try again later."
            )




class SearchService:
    """
    Executes compound hybrid searches (combining semantic FAISS matching, tokenized keyword scoring, and LLM Q&A).
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        self.vector_store = VectorStoreService()

    async def search_inside_note(self, notes_id: UUID, query: str, limit: int = 5) -> Dict[str, Any]:
        """Hybrid query resolving matches, generating direct AI answer, and extracting clean snippets."""
        stmt = select(Notes).filter(Notes.id == notes_id)
        res = await self.db.execute(stmt)
        note = res.scalars().first()

        doc_text = note.content if note and note.content else ""
        clean_q = query.lower().strip()
        
        # Stop words to ignore during token matching
        stopwords = {"where", "did", "he", "she", "what", "is", "the", "in", "of", "and", "to", "a", "his", "her", "their", "completed", "complete", "was"}
        query_words = [w for w in re.findall(r'\w+', clean_q) if w not in stopwords and len(w) > 1]
        
        # Domain Synonyms dictionary for academic/resume documents
        synonyms = {
            "education": ["education", "degree", "college", "university", "school", "b.e", "b.tech", "bsc", "msc", "m.tech", "cgpa", "percentage", "hsc", "sslc", "graduated", "academic"],
            "skills": ["skills", "technologies", "languages", "tools", "frameworks", "python", "java", "sql", "react", "node"],
            "experience": ["experience", "internship", "project", "work", "role", "developer", "engineer", "company"],
            "contact": ["email", "phone", "mobile", "address", "linkedin", "github"]
        }
        
        expanded_keywords = set(query_words)
        for qw in query_words:
            for key, syn_list in synonyms.items():
                if qw in key or any(qw in s for s in syn_list):
                    expanded_keywords.update(syn_list)

        paragraphs = [p.strip() for p in doc_text.split("\n") if len(p.strip()) > 10]
        scored_paragraphs = []

        for p in paragraphs:
            p_lower = p.lower()
            match_count = sum(1 for kw in expanded_keywords if kw in p_lower)
            if match_count > 0:
                score = min(0.95, 0.65 + (match_count * 0.10))
                scored_paragraphs.append({"text": p, "score": score})

        # 1. Semantic FAISS search fallback
        semantic_results = self.vector_store.semantic_search(notes_id, query, limit=limit)
        for item in semantic_results:
            if isinstance(item, dict) and item.get("text"):
                raw_score = item.get("score", 0.0)
                norm_score = min(0.92, max(0.60, raw_score * 10)) if raw_score < 0.10 else min(0.95, raw_score)
                scored_paragraphs.append({"text": item["text"], "score": norm_score})

        # Deduplicate and sort by score descending
        seen_texts = set()
        combined = []
        for item in scored_paragraphs:
            txt = item["text"].strip()
            if txt not in seen_texts:
                seen_texts.add(txt)
                combined.append(item)

        combined.sort(key=lambda x: x["score"], reverse=True)
        top_matches = combined[:limit]

        # 2. Direct AI Answer Generation using Gemini API or Smart Paragraph Extractor
        ai_answer = ""
        api_key = settings.GOOGLE_API_KEY
        if api_key and not api_key.startswith("mock") and doc_text:
            try:
                from google import genai
                client = genai.Client(api_key=api_key)
                prompt = (
                    f"Based on the following document context, provide a direct, clear, and accurate 1-2 sentence answer to the user's question.\n"
                    f"User Question: {query}\n\n"
                    f"Document Context:\n{doc_text[:6000]}\n\n"
                    f"Answer directly:"
                )
                def _gen():
                    r = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
                    return r.text.strip() if hasattr(r, 'text') and r.text else ""

                ai_answer = await asyncio.to_thread(_gen)
            except Exception as e:
                logger.warning(f"Gemini Q&A call exception: {e}")

        if not ai_answer and top_matches:
            ai_answer = f"Based on the document: {top_matches[0]['text']}"

        return {
            "ai_answer": ai_answer or "No specific details found in the document for your query.",
            "matches": top_matches
        }


class ExportService:
    """
    Generates structured export buffers (Markdown, TXT, DOCX) representing study packages.
    """
    @staticmethod
    def generate_markdown(package: Dict[str, Any]) -> str:
        """Converts study companion packages to clean GitHub-style Markdown documents."""
        md = []
        md.append(f"# {package.get('short_summary', 'Study Notes')[:40]}... Study Companion")
        md.append("\n## Short Summary")
        md.append(package.get("short_summary", ""))
        
        md.append("\n## Detailed Summary")
        md.append(package.get("detailed_summary", ""))
        
        md.append("\n## Key Points")
        for pt in package.get("bullet_points", []):
            md.append(f"- {pt}")
            
        md.append("\n## Definitions")
        for df in package.get("definitions", []):
            md.append(f"- **{df.get('concept')}**: {df.get('definition')}")
            
        md.append("\n## Key Formulas")
        for fm in package.get("formulas", []):
            md.append(f"  * {fm}")
            
        md.append("\n## Advantages & Disadvantages")
        md.append(f"**Advantages**:\n{package.get('advantages', 'N/A')}\n")
        md.append(f"**Disadvantages**:\n{package.get('disadvantages', 'N/A')}")
        
        md.append("\n## FAQs")
        for faq in package.get("faqs", []):
            md.append(f"**Q**: {faq.get('question')}\n**A**: {faq.get('answer')}\n")
            
        return "\n".join(md)

    @staticmethod
    def generate_docx(package: Dict[str, Any]) -> io.BytesIO:
        """Generates Microsoft Word Document byte stream."""
        doc = docx.Document()
        doc.add_heading("AI Study Notes Companion", level=1)
        
        doc.add_heading("Short Summary", level=2)
        doc.add_paragraph(package.get("short_summary", ""))
        
        doc.add_heading("Detailed Summary", level=2)
        doc.add_paragraph(package.get("detailed_summary", ""))
        
        doc.add_heading("Key Bullet Points", level=2)
        for pt in package.get("bullet_points", []):
            doc.add_paragraph(pt, style="List Bullet")
            
        doc.add_heading("Definitions", level=2)
        for df in package.get("definitions", []):
            p = doc.add_paragraph()
            p.add_run(df.get("concept") + ": ").bold = True
            p.add_run(df.get("definition"))

        doc.add_heading("Exam & Revision Guidance", level=2)
        doc.add_paragraph(package.get("exam_notes", ""))
        
        out = io.BytesIO()
        doc.save(out)
        out.seek(0)
        return out
