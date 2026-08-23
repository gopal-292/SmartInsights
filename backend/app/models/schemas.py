from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=6, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class BetterAuthBridgeIn(BaseModel):
    """Sync a Better Auth session user into the FastAPI/SQLAlchemy user store."""

    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    better_auth_user_id: str | None = None


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class BusinessProfileIn(BaseModel):
    business_name: str
    business_type: str = ""
    industry: str = ""
    location: str = ""
    currency: str = "INR"
    business_size: str = "SME"


class BusinessProfileOut(BusinessProfileIn):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DatasetOut(BaseModel):
    id: int
    filename: str
    data_type: str
    row_count: int
    columns_json: str
    status: str
    notes: str
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = []


class ReportRequest(BaseModel):
    include_ai: bool = True


class ApiMessage(BaseModel):
    message: str
    details: dict[str, Any] | None = None
