import json
from typing import cast

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "KisanMitraAI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "supersecretkey12345"

    # FastAPI Host/Port
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    # Logging
    LOG_LEVEL: str = "info"

    # CORS Origins
    CORS_ORIGINS: list[str] | str = ["http://localhost:3000", "http://localhost:8000"]

    @field_validator("CORS_ORIGINS")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    return cast(list[str], json.loads(v))
                except Exception:
                    pass
            return [i.strip() for i in v.split(",")]
        return v

    @field_validator("DEBUG", mode="before")
    @classmethod
    def normalize_debug(cls, v: object) -> object:
        if isinstance(v, str):
            normalized = v.strip().lower()
            if normalized in {"release", "prod", "production"}:
                return False
        return v

    # PostgreSQL Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_NAME: str = "kisan_mitra_db"
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/kisan_mitra_db"

    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://localhost:6379/0"

    # Chroma Configuration
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000
    CHROMA_DB_PATH: str = "./data/vector_db"

    # LLM Config & Providers
    DEFAULT_LLM_PROVIDER: str = "gemini"  # Options: mock, gemini, openai, claude, ollama
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-pro"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    CLAUDE_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-3-5-sonnet-latest"
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    LLM_TEMPERATURE: float = 0.2

    # Voice Integration
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""

    # SMS Integration
    SMS_PROVIDER: str = "mock"  # Options: mock, twilio, plivo
    PLIVO_AUTH_ID: str = ""
    PLIVO_AUTH_TOKEN: str = ""
    PLIVO_PHONE_NUMBER: str = ""

    # External API Keys (Weather & Market)
    OPENWEATHER_API_KEY: str = ""
    TOMORROW_IO_API_KEY: str = ""
    AGMARKNET_API_KEY: str = ""
    ENAM_API_ENDPOINT: str = "https://enam.gov.in/NAMWSRetail/NAMWS/GetMandiPrice"

    # Cloud Storage (S3 / R2)
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    S3_BUCKET_NAME: str = ""

    # OCR Integration
    GOOGLE_VISION_API_KEY: str = ""

    # Feature Flags
    FEATURE_REASONING_ENABLED: bool = True
    FEATURE_WORKFLOW_ENABLED: bool = True
    FEATURE_POLICY_ENABLED: bool = True
    FEATURE_TELEMETRY_ENABLED: bool = True
    FEATURE_DASHBOARD_ENABLED: bool = True
    FEATURE_VOICE_ENABLED: bool = False
    FEATURE_SMS_ENABLED: bool = False
    FEATURE_IVR_ENABLED: bool = False
    FEATURE_LLM_ENABLED: bool = True
    FEATURE_DEBUG_ENABLED: bool = True
    FEATURE_INTEGRATIONS_ENABLED: bool = True

    # Logging format and directory
    LOG_FORMAT: str = "text"  # Options: text, json
    LOG_DIR: str = "logs"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

def validate_production_config(cfg: Settings) -> None:
    """
    Validates that credentials, API keys, and debug modes are secure for production environments.
    """
    if cfg.APP_ENV != "production":
        return

    errors = []

    # Validate database secrets
    if not cfg.DB_PASSWORD or cfg.DB_PASSWORD == "postgres":
        errors.append("DB_PASSWORD must be secure and cannot be empty or 'postgres'.")
    if not cfg.DB_USER or cfg.DB_USER == "postgres":
        errors.append("DB_USER must be secure and cannot be empty or 'postgres'.")
    if "postgres:postgres" in cfg.DATABASE_URL:
        errors.append("DATABASE_URL contains default username and password ('postgres:postgres').")

    # Validate LLM configs
    if cfg.FEATURE_LLM_ENABLED and cfg.DEFAULT_LLM_PROVIDER != "mock":
        if cfg.DEFAULT_LLM_PROVIDER == "gemini" and (not cfg.GEMINI_API_KEY or "api-key" in cfg.GEMINI_API_KEY.lower()):
            errors.append("DEFAULT_LLM_PROVIDER is set to 'gemini' but GEMINI_API_KEY is missing or invalid.")
        elif cfg.DEFAULT_LLM_PROVIDER == "openai" and (not cfg.OPENAI_API_KEY or "api-key" in cfg.OPENAI_API_KEY.lower()):
            errors.append("DEFAULT_LLM_PROVIDER is set to 'openai' but OPENAI_API_KEY is missing or invalid.")
        elif cfg.DEFAULT_LLM_PROVIDER == "claude" and (not cfg.CLAUDE_API_KEY or "api-key" in cfg.CLAUDE_API_KEY.lower()):
            errors.append("DEFAULT_LLM_PROVIDER is set to 'claude' but CLAUDE_API_KEY is missing or invalid.")

    # Validate integrations configs in production if enabled
    if cfg.FEATURE_INTEGRATIONS_ENABLED:
        if cfg.SMS_PROVIDER == "twilio" and not cfg.TWILIO_AUTH_TOKEN:
            errors.append("SMS_PROVIDER is 'twilio' but TWILIO_AUTH_TOKEN is missing.")
        if cfg.SMS_PROVIDER == "plivo" and not cfg.PLIVO_AUTH_TOKEN:
            errors.append("SMS_PROVIDER is 'plivo' but PLIVO_AUTH_TOKEN is missing.")

    # Warn or error on debug features
    if cfg.DEBUG:
        errors.append("DEBUG mode must be set to false in a production environment.")

    if errors:
        raise ValueError(
            "PRODUCTION SECURITY VIOLATION:\n" +
            "\n".join([f" - [CRITICAL] {err}" for err in errors])
        )
