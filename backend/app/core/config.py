from functools import lru_cache
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    PROJECT_NAME: str = "Prompt Relay V2"
    VERSION: str = "0.2.0"
    DESCRIPTION: str = "Sequential 3-Player Hotseat Prompt Engineering Competition"

    # LLM Settings
    GROQ_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    DEFAULT_MODEL_NAME: str = "qwen/qwen3.8-27b"
    DEFAULT_LLM_PROVIDER: str = "groq"
    MODEL_TEMPERATURE: float = 0.2
    MODEL_TIMEOUT_SECONDS: int = 15
    FALLBACK_TO_OFFLINE: bool = True

    # Database and Directories
    DATABASE_PATH: str = "data/matches.sqlite"
    CASES_DIR: Path = BASE_DIR / "backend" / "cases"
    SCENARIOS_DIR: Path = BASE_DIR / "backend" / "scenarios"

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    # Hard Prompt Length Limits per Player Turn
    MAX_PROMPT_WORDS_P1: int = 40
    MAX_PROMPT_WORDS_P2: int = 40
    MAX_PROMPT_WORDS_P3: int = 60

    MAX_PROMPT_CHARS_P1: int = 300
    MAX_PROMPT_CHARS_P2: int = 300
    MAX_PROMPT_CHARS_P3: int = 450

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def gemini_key(self) -> str:
        return self.GEMINI_API_KEY

    @property
    def groq_key(self) -> str:
        return self.GROQ_API_KEY


@lru_cache
def get_settings() -> Settings:
    return Settings()
