from fastapi import APIRouter
from backend.app.core.config import get_settings

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    settings = get_settings()
    return {
        "status": "ok",
        "service": "Prompt Relay",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "llm": {
            "default_provider": settings.DEFAULT_LLM_PROVIDER,
            "default_model": settings.DEFAULT_MODEL_NAME,
            "has_gemini_key": bool(settings.GEMINI_API_KEY),
        },
    }
