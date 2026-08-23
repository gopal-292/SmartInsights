from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine, ensure_pgvector
from app.routers import ai, analytics, auth, business, ml, upload

ensure_pgvector()
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    description=(
        "SmartInsights API — FastAPI + SQLAlchemy + PostgreSQL/Supabase + "
        "Pandas + Scikit-learn + LangChain/pgVector + OpenAI"
    ),
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list or ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(business.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(ml.router, prefix="/api")
app.include_router(ai.router, prefix="/api")


@app.get("/")
def root():
    return {
        "name": "SmartInsights",
        "status": "ok",
        "docs": "/docs",
        "version": "0.2.0",
        "stack": {
            "backend": "FastAPI",
            "orm": "SQLAlchemy",
            "database": "PostgreSQL (Supabase-compatible)",
            "vector": "pgVector",
            "rag": "LangChain",
            "llm": "OpenAI API",
            "ml": "Scikit-learn",
            "data": "Pandas",
            "auth_bridge": "Better Auth (Next.js) + API JWT",
        },
        "llm_provider": settings.llm_provider,
        "openai_configured": settings.openai_enabled,
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
