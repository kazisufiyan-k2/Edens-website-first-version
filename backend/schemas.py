from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


# ===================== ENQUIRY =====================

class EnquiryCreate(BaseModel):
    business_name: Optional[str] = None
    customer_name: str = Field(..., min_length=2, max_length=150)
    phone: str = Field(..., min_length=7, max_length=30)
    email: EmailStr
    site_address: Optional[str] = None
    message: str = Field(..., min_length=10, max_length=3000)

    @field_validator("customer_name", "message")
    @classmethod
    def not_blank(cls, v: str):
        if not v.strip():
            raise ValueError("This field cannot be empty.")
        return v.strip()


class EnquiryOut(BaseModel):
    id: int
    business_name: Optional[str]
    customer_name: str
    phone: str
    email: str
    site_address: Optional[str]
    message: str
    status: str
    admin_notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class EnquiryStatusUpdate(BaseModel):
    status: Optional[str] = None
    admin_notes: Optional[str] = None


# ===================== REVIEW =====================

class ReviewCreate(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    rating: int = Field(..., ge=1, le=5)
    message: str = Field(..., min_length=5, max_length=2000)

    @field_validator("customer_name", "message")
    @classmethod
    def not_blank(cls, v: str):
        if not v.strip():
            raise ValueError("This field cannot be empty.")
        return v.strip()


class ReviewOut(BaseModel):
    id: int
    customer_name: str
    email: str
    rating: int
    message: str
    sentiment_label: Optional[str]
    sentiment_score: Optional[float]
    ai_admin_suggestion: Optional[str]
    ai_draft_reply: Optional[str]
    is_published: bool
    admin_reply: Optional[str]
    reply_sent: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ReviewReplyUpdate(BaseModel):
    admin_reply: str = Field(..., min_length=2, max_length=2000)
    send_email: bool = True


class ReviewPublishUpdate(BaseModel):
    is_published: bool


# ===================== ADMIN =====================

class AdminLogin(BaseModel):
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    token: str
