from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import BASE_DIR, settings


def _build_engine():
    url = settings.sqlalchemy_database_url
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    eng = create_engine(url, connect_args=connect_args, pool_pre_ping=True)
    if "postgresql" in url:
        try:
            with eng.connect() as conn:
                conn.execute(text("SELECT 1"))
            return eng, url
        except Exception as exc:
            # Local demos keep working if Docker/Supabase is offline
            fallback = f"sqlite:///{(BASE_DIR / 'data' / 'smartinsights.db').as_posix()}"
            print(
                f"[SmartInsights] PostgreSQL unavailable ({exc}). "
                f"Falling back to SQLite at {fallback}. "
                "Start Docker (`docker compose up -d`) or set a Supabase DATABASE_URL for the PPT stack."
            )
            return create_engine(fallback, connect_args={"check_same_thread": False}, pool_pre_ping=True), fallback
    return eng, url


engine, ACTIVE_DATABASE_URL = _build_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_pgvector() -> None:
    """Enable pgvector when running on PostgreSQL (PPT vector database)."""
    if "postgresql" not in ACTIVE_DATABASE_URL:
        return
    try:
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    except Exception:
        pass
