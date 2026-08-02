from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean
from sqlalchemy.sql import func
from database import Base


class Enquiry(Base):
    __tablename__ = "enquiries"

    id = Column(Integer, primary_key=True, index=True)
    business_name = Column(String(150), nullable=True)
    customer_name = Column(String(150), nullable=False)
    phone = Column(String(30), nullable=False)
    email = Column(String(150), nullable=False, index=True)
    site_address = Column(String(255), nullable=True)
    message = Column(Text, nullable=False)

    status = Column(String(30), default="new")  # new / contacted / resolved
    admin_notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String(150), nullable=False)
    email = Column(String(150), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5
    message = Column(Text, nullable=False)

    # ---- AI-generated fields (filled automatically on submit) ----
    sentiment_label = Column(String(20), nullable=True)     # positive / neutral / negative
    sentiment_score = Column(Float, nullable=True)          # -1.0 to 1.0
    ai_admin_suggestion = Column(Text, nullable=True)        # what admin should do
    ai_draft_reply = Column(Text, nullable=True)             # AI-drafted reply to customer

    is_published = Column(Boolean, default=False)   # admin approves before showing on site
    admin_reply = Column(Text, nullable=True)
    reply_sent = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
