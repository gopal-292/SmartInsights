from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.entities import BusinessProfile, User
from app.models.schemas import BusinessProfileIn, BusinessProfileOut

router = APIRouter(prefix="/business", tags=["Business Profile"])


@router.get("/profile", response_model=BusinessProfileOut | None)
def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(BusinessProfile).filter(BusinessProfile.user_id == current_user.id).first()
    return BusinessProfileOut.model_validate(profile) if profile else None


@router.post("/profile", response_model=BusinessProfileOut)
def upsert_profile(
    payload: BusinessProfileIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(BusinessProfile).filter(BusinessProfile.user_id == current_user.id).first()
    if profile is None:
        profile = BusinessProfile(user_id=current_user.id, **payload.model_dump())
        db.add(profile)
    else:
        for key, value in payload.model_dump().items():
            setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return BusinessProfileOut.model_validate(profile)


@router.delete("/profile")
def delete_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(BusinessProfile).filter(BusinessProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    db.delete(profile)
    db.commit()
    return {"message": "Business profile deleted"}
