import logging
from typing import Any, Optional
from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from app.core.config import settings
from app.ai.config import DEFAULT_GEMINI_MODEL, DEFAULT_OPENAI_MODEL

logger = logging.getLogger(__name__)


def get_llm(
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
    temperature: float = 0.2,
    **kwargs: Any
) -> BaseChatModel:
    """
    Factory function returning a LangChain compatible LLM instance.
    Supports 'google' (Gemini) and 'openai' (or compatible local endpoints like Ollama).
    """
    # Fallback to configured environments if parameter not specified
    if not provider:
        provider = "google" if settings.GOOGLE_API_KEY and settings.GOOGLE_API_KEY != "mock_gemini_api_key" else "openai"

    if provider.lower() == "google":
        model = model_name or DEFAULT_GEMINI_MODEL
        logger.info(f"Initializing LangChain Google Gemini: {model}")
        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=temperature,
            **kwargs
        )
    elif provider.lower() == "openai":
        model = model_name or DEFAULT_OPENAI_MODEL
        logger.info(f"Initializing OpenAI compatible client: {model}")
        return ChatOpenAI(
            model=model,
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE,
            temperature=temperature,
            **kwargs
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
