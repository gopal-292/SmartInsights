from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.entities import User
from app.services.data_store import load_user_frames
from app.services.ml_engine import analyze_sentiment, detect_anomalies, forecast_sales, segment_customers
from app.services.patterns import detect_patterns

router = APIRouter(prefix="/ml", tags=["Machine Learning"])


@router.get("/forecast")
def forecast(
    periods: int = Query(6, ge=1, le=12, description="Months to forecast ahead"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return forecast_sales(load_user_frames(db, current_user.id), periods=periods)


@router.get("/patterns")
def patterns(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return detect_patterns(load_user_frames(db, current_user.id))


@router.get("/anomalies")
def anomalies(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return detect_anomalies(load_user_frames(db, current_user.id))


@router.get("/sentiment")
def sentiment(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return analyze_sentiment(load_user_frames(db, current_user.id))


@router.get("/segments")
def segments(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return segment_customers(load_user_frames(db, current_user.id))
