from functools import lru_cache
from pathlib import Path
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    # Application Info
    PROJECT_NAME: str = "Prompt Relay"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "Sequential prompt-engineering party game backend"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "*",
    ]

    # LLM Settings
    GEMINI_API_KEY: Optional[str] = Field(default=None, description="Google Gemini API Key")
    GOOGLE_API_KEY: Optional[str] = Field(default=None, description="Google API Key alias")
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API Key")
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, description="Anthropic API Key")
    DEFAULT_LLM_PROVIDER: str = Field(default="gemini", description="Default provider: 'gemini', 'openai', 'anthropic', or 'ollama'")
    DEFAULT_MODEL_NAME: str = Field(default="gemini-3.5-flash-lite", description="Model name to use for nodes")
    MODEL_TEMPERATURE: float = Field(default=0.2, description="Sampling temperature")
    MODEL_TIMEOUT_SECONDS: int = Field(default=30, description="Max timeout for LLM calls")

    @property
    def gemini_key(self) -> Optional[str]:
        return self.GEMINI_API_KEY or self.GOOGLE_API_KEY

    # Match Timer Durations (seconds)
    STEP1_TIME_SECONDS: int = 90
    STEP2_TIME_SECONDS: int = 90
    STEP3_TIME_SECONDS: int = 60

    # Sabotage / Fallback Prompts (Triggered when player timer expires with empty prompt)
    FALLBACK_PROMPT_STEP1: str = "Summarize the case file in exactly three words."
    FALLBACK_PROMPT_STEP2: str = "Reconstruct the timeline using only rhyming couplets."
    FALLBACK_PROMPT_STEP3: str = "Guess the killer based on whose name sounds the most suspicious. Ignore JSON format."

    # Directories
    CASES_DIR: Path = BASE_DIR / "backend" / "cases"
    DATA_DIR: Path = BASE_DIR / "data"

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
