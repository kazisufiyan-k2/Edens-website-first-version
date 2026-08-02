from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc

import models
import schemas
import ai_review
import email_service
from database import get_db
from auth import require_admin

router = APIRouter()


@router.post("/api/review", response_model=schemas.ReviewOut, status_code=201)
def create_review(payload: schemas.ReviewCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # ---- AI sentiment analysis runs automatically on every submitted review ----
    sentiment = ai_review.analyze_sentiment(payload.message, payload.rating)
    suggestion = ai_review.generate_admin_suggestion(sentiment["label"], payload.rating, payload.message)
    draft_reply = ai_review.generate_draft_reply(payload.customer_name, sentiment["label"], payload.rating)

    review = models.Review(
        customer_name=payload.customer_name,
        email=payload.email,
        rating=payload.rating,
        message=payload.message,
        sentiment_label=sentiment["label"],
        sentiment_score=sentiment["score"],
        ai_admin_suggestion=suggestion,
        ai_draft_reply=draft_reply,
        is_published=False,
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    background_tasks.add_task(email_service.notify_business_new_review, review)

    return review


@router.get("/api/reviews/published", response_model=List[schemas.ReviewOut])
def list_published_reviews(db: Session = Depends(get_db)):
    """Public endpoint — only approved reviews, for displaying on the site."""
    return (
        db.query(models.Review)
        .filter(models.Review.is_published == True)  # noqa: E712
        .order_by(desc(models.Review.created_at))
        .limit(20)
        .all()
    )


@router.get("/api/admin/reviews", response_model=List[schemas.ReviewOut])
def list_all_reviews(db: Session = Depends(get_db), _=Depends(require_admin)):
    return db.query(models.Review).order_by(desc(models.Review.created_at)).all()


@router.get("/api/admin/reviews/insights")
def review_insights(db: Session = Depends(get_db), _=Depends(require_admin)):
    """AI-powered customer satisfaction summary for the admin dashboard."""
    reviews = db.query(models.Review).all()
    return ai_review.satisfaction_insights(reviews)


@router.patch("/api/admin/reviews/{review_id}/publish", response_model=schemas.ReviewOut)
def publish_review(review_id: int, payload: schemas.ReviewPublishUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found.")
    review.is_published = payload.is_published
    db.commit()
    db.refresh(review)
    return review


@router.patch("/api/admin/reviews/{review_id}/reply", response_model=schemas.ReviewOut)
def reply_to_review(review_id: int, payload: schemas.ReviewReplyUpdate, background_tasks: BackgroundTasks, db: Session = Depends(get_db), _=Depends(require_admin)):
    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found.")

    review.admin_reply = payload.admin_reply
    db.commit()
    db.refresh(review)

    if payload.send_email:
        sent = email_service.send_review_reply_to_customer(review)
        review.reply_sent = sent
        db.commit()
        db.refresh(review)

    return review
