from datetime import datetime, timezone
from fastapi import APIRouter
from backend.app.core.config import get_settings

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def health_check():
    settings = get_settings()
    has_gemini = bool(settings.gemini_key)
    has_openai = bool(settings.OPENAI_API_KEY)
    has_anthropic = bool(settings.ANTHROPIC_API_KEY)

    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "llm": {
            "default_provider": settings.DEFAULT_LLM_PROVIDER,
            "default_model": settings.DEFAULT_MODEL_NAME,
            "has_gemini_key": has_gemini,
            "has_openai_key": has_openai,
            "has_anthropic_key": has_anthropic,
        },
    }
