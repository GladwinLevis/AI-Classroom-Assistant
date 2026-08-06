import logging
import fitz  # PyMuPDF
from docx import Document
from pptx import Presentation
from app.ai.llm import get_llm

logger = logging.getLogger(__name__)


class DocumentSummarizer:
    """
    DocumentSummarizer extracts text content from PDF, DOCX, and PPTX files
    and calls the LLM service to produce bulleted summaries.
    """
    def __init__(self):
        self.llm = get_llm()

    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extracts plain text from PDF file using PyMuPDF."""
        text = ""
        try:
            with fitz.open(file_path) as doc:
                for page in doc:
                    text += page.get_text()
        except Exception as e:
            logger.error(f"Error extracting PDF text: {str(e)}", exc_info=True)
            raise e
        return text

    def extract_text_from_docx(self, file_path: str) -> str:
        """Extracts plain text from DOCX file using python-docx."""
        try:
            doc = Document(file_path)
            return "\n".join([p.text for p in doc.paragraphs])
        except Exception as e:
            logger.error(f"Error extracting DOCX text: {str(e)}", exc_info=True)
            raise e

    def extract_text_from_pptx(self, file_path: str) -> str:
        """Extracts plain text from PPTX slide presentations using python-pptx."""
        text = []
        try:
            prs = Presentation(file_path)
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text:
                        text.append(shape.text)
        except Exception as e:
            logger.error(f"Error extracting PPTX text: {str(e)}", exc_info=True)
            raise e
        return "\n".join(text)

    async def summarize_document(self, file_path: str, extension: str) -> str:
        """
        Coordinates text extraction and triggers LLM summarization prompt execution.
        """
        logger.info(f"Extracting and summarizing document: {file_path} (.{extension})")
        
        # Determine extraction strategy
        ext = extension.lower().strip(".")
        if ext == "pdf":
            text = self.extract_text_from_pdf(file_path)
        elif ext in ["docx", "doc"]:
            text = self.extract_text_from_docx(file_path)
        elif ext in ["pptx", "ppt"]:
            text = self.extract_text_from_pptx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

        # Limit token length for standard summarize prompt placeholder
        truncated_text = text[:10000]
        
        # Invoke LLM to summarize
        prompt = (
            f"Provide a concise, professional summary with bullet points highlighting key concepts, "
            f"formulations, and definitions from the study material below:\n\n{truncated_text}"
        )
        
        response = await self.llm.ainvoke(prompt)
        return str(response.content)
