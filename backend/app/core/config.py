from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Autonomous AI QA Platform"
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    frontend_url: str = "http://localhost:3000"

    redis_url: str | None = "redis://redis:6379/0"
    queue_name: str = "qa-runs"
    worker_concurrency: int = 4
    worker_job_timeout_seconds: int = 900

    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    ollama_base_url: str | None = "http://localhost:11434"
    ollama_model: str = "llama3.1"
    ai_provider_primary: str = "groq"
    ai_provider_fallback: str = "ollama"

    supabase_url: str | None = None
    supabase_service_role_key: str | None = None
    supabase_db_url: str | None = None
    supabase_storage_bucket_uploads: str = "qa-uploads"
    supabase_storage_bucket_reports: str = "qa-reports"

    chroma_host: str = "localhost"
    chroma_port: int = 8001
    chroma_collection_prefix: str = "qa_platform"
    chroma_api_key: str | None = None
    chroma_tenant: str | None = None
    chroma_database: str | None = None
    chroma_cloud_host: str = "api.trychroma.com"
    chroma_cloud_port: int = 443
    chroma_cloud_ssl: bool = True

    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = None
    twilio_sms_from: str | None = None
    twilio_whatsapp_from: str | None = None
    default_alert_to: str | None = None

    clerk_jwks_url: str | None = None
    clerk_webhook_secret: str | None = None
    auth_dev_mode: bool = True

    max_autonomous_retries: int = 3
    self_heal_min_similarity: float = 0.7
    self_heal_max_strategies: int = 3
    approval_validation_threshold: int = 70
    approval_hallucination_threshold: int = 50
    websocket_heartbeat_seconds: int = 3

    data_dir: Path = Field(default_factory=lambda: BASE_DIR / "storage")

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return settings
