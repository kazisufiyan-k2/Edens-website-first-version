"""
Email service — sends notification emails via Brevo (HTTP email API).
Works reliably on Render because it uses HTTPS, not blocked SMTP ports.
Brevo free tier allows sending to ANY recipient (no domain verification needed).
"""

# ---- Fix: force IPv4 (Render sometimes can't reach IPv6 addresses) ----
import socket
_original_getaddrinfo = socket.getaddrinfo
def _ipv4_only_getaddrinfo(*args, **kwargs):
    responses = _original_getaddrinfo(*args, **kwargs)
    return [r for r in responses if r[0] == socket.AF_INET]
socket.getaddrinfo = _ipv4_only_getaddrinfo

import os
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("edens.email")

BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Edens Refrigeration and Air-Conditioning")
FROM_ADDRESS = os.getenv("BREVO_FROM_EMAIL", "")
BUSINESS_NOTIFY_EMAIL = os.getenv("BUSINESS_NOTIFY_EMAIL", "")

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def _is_configured() -> bool:
    return bool(BREVO_API_KEY and FROM_ADDRESS)


def send_email(to_email: str, subject: str, body: str) -> bool:
    if not _is_configured():
        logger.warning(f"Brevo not configured — skipping email to {to_email}")
        return False
    try:
        response = requests.post(
            BREVO_API_URL,
            headers={
                "accept": "application/json",
                "api-key": BREVO_API_KEY,
                "content-type": "application/json",
            },
            json={
                "sender": {"name": SMTP_FROM_NAME, "email": FROM_ADDRESS},
                "to": [{"email": to_email}],
                "subject": subject,
                "textContent": body,
            },
            timeout=15,
        )
        if response.status_code not in (200, 201):
            logger.error(f"Brevo error sending to {to_email}: {response.status_code} {response.text}")
            return False
        return True
    except Exception as exc:
        logger.error(f"Failed to send email to {to_email}: {exc}")
        return False


def notify_business_new_enquiry(enquiry) -> None:
    subject = f"New Enquiry from {enquiry.customer_name}"
    body = (
        f"New website enquiry received:\n\n"
        f"Business Name: {enquiry.business_name or '-'}\n"
        f"Customer Name: {enquiry.customer_name}\n"
        f"Phone: {enquiry.phone}\n"
        f"Email: {enquiry.email}\n"
        f"Site Address: {enquiry.site_address or '-'}\n\n"
        f"Message:\n{enquiry.message}\n"
    )
    if BUSINESS_NOTIFY_EMAIL:
        send_email(BUSINESS_NOTIFY_EMAIL, subject, body)


def confirm_enquiry_to_customer(enquiry) -> None:
    subject = "We've received your enquiry — Edens Refrigeration and Air-Conditioning"
    body = (
        f"Hi {enquiry.customer_name},\n\n"
        f"Thank you for reaching out to Edens Refrigeration and Air-Conditioning. "
        f"We've received your enquiry and one of our technicians will get back to you shortly.\n\n"
        f"Your message:\n\"{enquiry.message}\"\n\n"
        f"Kind regards,\nEdens Refrigeration and Air-Conditioning\n"
        f"33 Lotus Place, Wigram, Christchurch, 8025, New Zealand"
    )
    send_email(enquiry.email, subject, body)


def notify_business_new_review(review) -> None:
    subject = f"New {review.rating}-star Review ({review.sentiment_label})"
    body = (
        f"New review submitted:\n\n"
        f"Customer: {review.customer_name} ({review.email})\n"
        f"Rating: {review.rating}/5\n"
        f"Sentiment: {review.sentiment_label} (score: {review.sentiment_score})\n\n"
        f"Review:\n{review.message}\n\n"
        f"AI Suggestion for you:\n{review.ai_admin_suggestion}\n\n"
        f"AI Draft Reply:\n{review.ai_draft_reply}\n"
    )
    if BUSINESS_NOTIFY_EMAIL:
        send_email(BUSINESS_NOTIFY_EMAIL, subject, body)


def send_review_reply_to_customer(review) -> bool:
    subject = "Response to your review — Edens Refrigeration and Air-Conditioning"
    return send_email(review.email, subject, review.admin_reply or "")