import json
import logging
from typing import List, Dict, Any
from app.ai.llm import get_llm

logger = logging.getLogger(__name__)


class QuizGenerator:
    """
    QuizGenerator uses the LLM to parse class notes/documents and generate structured
    multiple choice questions (MCQs) for student revision.
    """
    def __init__(self):
        self.llm = get_llm()

    async def generate_mcqs(
        self,
        notes_content: str,
        num_questions: int = 5,
        difficulty: str = "medium"
    ) -> List[Dict[str, Any]]:
        """
        Generates MCQs. Returns a list of question dictionaries with text, options, correct_answer.
        """
        logger.info(f"Generating {num_questions} {difficulty} questions from notes context.")
        
        prompt = (
            f"Based on the following notes, generate {num_questions} multiple choice questions (MCQs) "
            f"with a difficulty level of {difficulty}.\n\n"
            f"Notes Content:\n{notes_content[:6000]}\n\n"
            f"Output must be a valid JSON array of objects. Do not wrap in markdown syntax. "
            f"Each object MUST have the keys:\n"
            f"- 'question_text': string\n"
            f"- 'options': list of 4 string options\n"
            f"- 'correct_answer': string matching exactly one of the options\n"
            f"- 'explanation': string detailing why the option is correct"
        )
        
        response = await self.llm.ainvoke(prompt)
        content = str(response.content).strip()
        
        # Clean up any potential markdown wraps
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        try:
            questions = json.loads(content)
            if isinstance(questions, list):
                return questions
        except json.JSONDecodeError:
            logger.error("Failed to parse generated MCQ JSON. Returning fallback quiz structure.", exc_info=True)
            
        # Fallback question list
        return [
            {
                "question_text": "Sample MCQ generated from document context?",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_answer": "Option A",
                "explanation": "This is a placeholder explanation."
            }
        ]
