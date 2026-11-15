import os
from typing import Any, List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application runtime configuration loaded from environment variables or .env file.
    """
    APP_NAME: str = "Resume Matching API"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api"

    # Database configuration - defaults to local SQLite file
    DATABASE_URL: str = "sqlite:///./resume_matcher.db"

    # CORS configuration - default allowed origins for frontend Vite dev server
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # File uploads
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 5

    # Optional LLM layer (Gemini via google-genai)
    USE_LLM: bool = False
    GEMINI_API_KEY: str = ""
    LLM_MODEL: str = "gemini-2.0-flash"
    LLM_TIMEOUT_SECONDS: int = 30
    LLM_MAX_CANDIDATES: int = 15
    LLM_MAX_CONCURRENCY: int = 3

    @field_validator("USE_LLM", mode="before")
    @classmethod
    def parse_use_llm_flag(cls, v: Any) -> bool:
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            val = v.strip().lower()
            return val in {"1", "true", "yes", "t", "on"}
        return bool(v)

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug_flag(cls, v: Any) -> bool:
        """
        Handle non-standard ambient environment values for DEBUG (such as Windows build tool flags like 'release').
        """
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            val = v.strip().lower()
            if val in {"1", "true", "yes", "t", "on", "dev", "development"}:
                return True
            if val in {"0", "false", "no", "f", "off", "prod", "production", "release"}:
                return False
        return True

    @property
    def allowed_origins_list(self) -> List[str]:
        """Convert comma-separated origin string into a list for CORS middleware."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    # Pydantic v2 settings config pointing to .env
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
