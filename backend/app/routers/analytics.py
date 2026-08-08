from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.entities import User
from app.services.analytics import (
    dashboard_kpis,
    expense_analytics,
    inventory_analytics,
    profitability_analytics,
    sales_analytics,
)
from app.services.data_store import load_user_frames

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard")
def dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    frames = load_user_frames(db, current_user.id)
    return {
        "kpis": dashboard_kpis(frames),
        "sales": sales_analytics(frames),
        "expenses": expense_analytics(frames),
        "profitability": profitability_analytics(frames),
        "inventory": inventory_analytics(frames),
    }


@router.get("/sales")
def sales(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return sales_analytics(load_user_frames(db, current_user.id))


@router.get("/expenses")
def expenses(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return expense_analytics(load_user_frames(db, current_user.id))


@router.get("/profitability")
def profitability(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return profitability_analytics(load_user_frames(db, current_user.id))


@router.get("/inventory")
def inventory(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return inventory_analytics(load_user_frames(db, current_user.id))
