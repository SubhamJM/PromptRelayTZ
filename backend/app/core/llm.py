import logging
from typing import Optional
from langchain_core.language_models.chat_models import BaseChatModel

from backend.app.core.config import get_settings

logger = logging.getLogger(__name__)


def get_llm(
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
    temperature: Optional[float] = None,
) -> BaseChatModel:
    """
    Factory function to initialize and return the configured Chat Model.
    Defaults to Google Gemini (gemini-3.5-flash-lite).
    """
    settings = get_settings()
    chosen_provider = (provider or settings.DEFAULT_LLM_PROVIDER).lower()
    chosen_model = model_name or settings.DEFAULT_MODEL_NAME
    temp = temperature if temperature is not None else settings.MODEL_TEMPERATURE

    if chosen_provider in ("gemini", "google"):
        api_key = settings.gemini_key
        if not api_key or api_key == "your-gemini-api-key-here":
            logger.warning("No valid GEMINI_API_KEY found in environment or .env")
        
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=chosen_model,
            google_api_key=api_key,
            temperature=temp,
            timeout=settings.MODEL_TIMEOUT_SECONDS,
        )

    elif chosen_provider == "openai":
        api_key = settings.OPENAI_API_KEY
        if not api_key or api_key == "your-openai-api-key-here":
            logger.warning("No valid OPENAI_API_KEY found in environment or .env")

        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=chosen_model or "gpt-4o-mini",
            api_key=api_key,
            temperature=temp,
            timeout=settings.MODEL_TIMEOUT_SECONDS,
        )

    elif chosen_provider == "anthropic":
        api_key = settings.ANTHROPIC_API_KEY
        if not api_key:
            logger.warning("No valid ANTHROPIC_API_KEY found in environment or .env")

        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=chosen_model or "claude-3-5-haiku-20241022",
            api_key=api_key,
            temperature=temp,
            timeout=settings.MODEL_TIMEOUT_SECONDS,
        )

    else:
        raise ValueError(f"Unsupported LLM provider: {chosen_provider}. Supported: 'gemini', 'openai', 'anthropic'")
