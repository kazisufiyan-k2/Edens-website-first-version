from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc

import models
import schemas
import email_service
from database import get_db
from auth import require_admin

router = APIRouter()


@router.post("/api/enquiry", response_model=schemas.EnquiryOut, status_code=201)
def create_enquiry(payload: schemas.EnquiryCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    enquiry = models.Enquiry(
        business_name=payload.business_name,
        customer_name=payload.customer_name,
        phone=payload.phone,
        email=payload.email,
        site_address=payload.site_address,
        message=payload.message,
    )
    db.add(enquiry)
    db.commit()
    db.refresh(enquiry)

    # Emails are sent in the background so the customer isn't kept waiting
    # on the form even if SMTP is slow / not yet configured.
    background_tasks.add_task(email_service.notify_business_new_enquiry, enquiry)
    background_tasks.add_task(email_service.confirm_enquiry_to_customer, enquiry)

    return enquiry


@router.get("/api/admin/enquiries", response_model=List[schemas.EnquiryOut])
def list_enquiries(db: Session = Depends(get_db), _=Depends(require_admin)):
    return db.query(models.Enquiry).order_by(desc(models.Enquiry.created_at)).all()


@router.patch("/api/admin/enquiries/{enquiry_id}", response_model=schemas.EnquiryOut)
def update_enquiry(enquiry_id: int, payload: schemas.EnquiryStatusUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    enquiry = db.query(models.Enquiry).filter(models.Enquiry.id == enquiry_id).first()
    if not enquiry:
        raise HTTPException(status_code=404, detail="Enquiry not found.")

    if payload.status is not None:
        enquiry.status = payload.status
    if payload.admin_notes is not None:
        enquiry.admin_notes = payload.admin_notes

    db.commit()
    db.refresh(enquiry)
    return enquiry
