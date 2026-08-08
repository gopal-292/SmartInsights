from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(BASE_DIR / ".env"), extra="ignore")

    app_name: str = "SmartInsights API"
    secret_key: str = "smartinsights-dev-secret-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    database_url: str = f"sqlite:///{(BASE_DIR / 'data' / 'smartinsights.db').as_posix()}"
    cors_origins: str = "http://localhost:3000"
    openai_api_key: str = ""
    gemini_api_key: str = ""
    llm_provider: str = "rule-based"
    upload_dir: str = str(BASE_DIR / "uploads")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
(BASE_DIR / "data").mkdir(parents=True, exist_ok=True)
