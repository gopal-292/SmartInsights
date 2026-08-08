from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.entities import User
from app.models.schemas import ChatRequest, ChatResponse
from app.services.ai_engine import (
    answer_business_question,
    build_report_payload,
    generate_insights,
    generate_recommendations,
)
from app.services.data_store import load_user_frames
from app.services.rag import load_user_documents, rag_answer

router = APIRouter(prefix="/ai", tags=["AI"])


@router.get("/insights")
def insights(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return generate_insights(load_user_frames(db, current_user.id))


@router.get("/recommendations")
def recommendations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return generate_recommendations(load_user_frames(db, current_user.id))


@router.post("/assistant", response_model=ChatResponse)
def assistant(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    frames = load_user_frames(db, current_user.id)
    base = answer_business_question(frames, payload.question)
    docs = load_user_documents(settings.upload_dir, current_user.id)
    enriched = rag_answer(payload.question, docs, base["answer"])
    return ChatResponse(answer=enriched["answer"], sources=[str(s)[:180] for s in enriched["sources"]])


@router.get("/report")
def report(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    payload = build_report_payload(load_user_frames(db, current_user.id))
    return JSONResponse(payload)
