"""
Email service — sends notification emails via SMTP.

Currently configured with PLACEHOLDER credentials in .env.example.
Replace SMTP_* values in your real .env file with your actual email
provider details (Gmail App Password, SendGrid, Zoho, etc.) and it
will work as-is — no code changes needed.

If SMTP is not configured yet, emails are safely skipped and logged
to the console instead of crashing the request (so the website keeps
working end-to-end even before real email credentials are added).
"""
import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("edens.email")

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Edens Refrigeration and Air-Conditioning")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "")
BUSINESS_NOTIFY_EMAIL = os.getenv("BUSINESS_NOTIFY_EMAIL", "")


def _is_configured() -> bool:
    return bool(SMTP_HOST and SMTP_USERNAME and SMTP_PASSWORD and SMTP_FROM_EMAIL)


def send_email(to_email: str, subject: str, body: str) -> bool:
    """
    Sends a plain-text email. Returns True if sent, False if skipped/failed.
    Never raises — failures are logged so a form submission never breaks
    just because email isn't set up yet.
    """
    if not _is_configured():
        logger.warning(
            "SMTP not configured yet — skipping email send.\n"
            f"--- Would have sent to: {to_email} ---\nSubject: {subject}\n{body}\n---"
        )
        return False

    try:
        msg = MIMEMultipart()
        msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM_EMAIL, [to_email], msg.as_string())
        return True
    except Exception as exc:
        logger.error(f"Failed to send email to {to_email}: {exc}")
        return False


# ---------------------- Templated notifications ----------------------

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
        f"If your matter is urgent, feel free to call us directly.\n\n"
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
        f"AI Draft Reply (edit before sending):\n{review.ai_draft_reply}\n"
    )
    if BUSINESS_NOTIFY_EMAIL:
        send_email(BUSINESS_NOTIFY_EMAIL, subject, body)


def send_review_reply_to_customer(review) -> bool:
    subject = "Response to your review — Edens Refrigeration and Air-Conditioning"
    return send_email(review.email, subject, review.admin_reply or "")
