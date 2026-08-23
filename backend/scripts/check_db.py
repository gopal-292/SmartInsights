from sqlalchemy import text

from app.core.database import ACTIVE_DATABASE_URL, Base, engine, ensure_pgvector
from app import models  # noqa: F401

ensure_pgvector()
Base.metadata.create_all(bind=engine)
print("DB", ACTIVE_DATABASE_URL)
with engine.connect() as conn:
    print("ping", conn.execute(text("SELECT 1")).scalar())
    try:
        ext = conn.execute(text("SELECT extname FROM pg_extension WHERE extname='vector'")).scalar()
        print("vector_ext", ext)
    except Exception as exc:
        print("vector_check_failed", exc)
