from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(BASE_DIR / ".env"), extra="ignore")

    app_name: str = "SmartInsights API"
    secret_key: str = "smartinsights-dev-secret-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    # PPT stack default: PostgreSQL (local Docker / Supabase)
    database_url: str = "postgresql+psycopg2://smartinsights:smartinsights@localhost:5433/smartinsights"
    cors_origins: str = "http://localhost:3000"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"
    llm_provider: str = "openai"  # openai | rule-based
    upload_dir: str = str(BASE_DIR / "uploads")
    # Used by LangChain PGVector collection naming
    rag_collection: str = "smartinsights_docs"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def openai_enabled(self) -> bool:
        return bool(self.openai_api_key.strip()) and self.llm_provider.lower() == "openai"

    @property
    def sqlalchemy_database_url(self) -> str:
        url = self.database_url.strip()
        # Allow plain postgres:// from Supabase dashboard
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+psycopg2://", 1)
        if url.startswith("postgresql://") and "+psycopg2" not in url:
            return url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return url


settings = Settings()
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
(BASE_DIR / "data").mkdir(parents=True, exist_ok=True)
