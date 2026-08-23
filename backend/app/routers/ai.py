from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.entities import BusinessProfile, User
from app.models.schemas import ChatRequest, ChatResponse
from app.services.ai_engine import (
    answer_business_question,
    build_report_payload,
    generate_insights,
    generate_recommendations,
)
from app.services.data_store import load_user_frames
from app.services.langchain_rag import answer_with_rag
from app.services.report_generator import (
    ReportGenerationError,
    generate_report_pdf,
    render_report_html,
)

router = APIRouter(prefix="/ai", tags=["AI"])


def _report_context(db: Session, user: User) -> dict:
    frames = load_user_frames(db, user.id)
    payload = build_report_payload(frames)
    profile = db.query(BusinessProfile).filter(BusinessProfile.user_id == user.id).first()
    if profile:
        payload["business"] = {
            "business_name": profile.business_name,
            "business_type": profile.business_type,
            "industry": profile.industry,
            "location": profile.location,
            "currency": profile.currency,
            "business_size": profile.business_size,
        }
    else:
        payload["business"] = None
    return payload


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
    enriched = answer_with_rag(current_user.id, payload.question, base["answer"])
    return ChatResponse(
        answer=enriched["answer"],
        sources=[str(s)[:180] for s in enriched.get("sources", [])],
    )


@router.get("/report")
def report(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return JSONResponse(_report_context(db, current_user))


@router.get("/report/html")
def report_html(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Jinja2-rendered HTML report (preview / download)."""
    try:
        html = render_report_html(_report_context(db, current_user))
    except ReportGenerationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return Response(
        content=html,
        media_type="text/html; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="smartinsights-report.html"'},
    )


@router.get("/report/pdf")
def report_pdf(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Jinja2 template rendered to PDF with WeasyPrint."""
    payload = _report_context(db, current_user)
    try:
        pdf_bytes = generate_report_pdf(payload)
    except ReportGenerationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    business = (payload.get("business") or {}).get("business_name") or "smartinsights"
    safe_name = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in business.lower())[:40]
    filename = f"{safe_name}-report-{stamp}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
