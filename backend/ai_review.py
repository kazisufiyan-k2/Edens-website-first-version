"""
AI Review Intelligence
=======================
This module powers the "AI review system" requested:

1. analyze_sentiment()  -> runs every incoming review through VADER
   (a proven, offline, pretrained sentiment model — no external API
   calls or training needed) and returns a label + score.

2. generate_admin_suggestion() -> turns the sentiment + rating into a
   short, actionable suggestion for the admin (e.g. "follow up fast",
   "ask for a public testimonial", etc).

3. generate_draft_reply() -> drafts a ready-to-send reply to the
   customer, which the admin can review/edit before sending by email.

4. satisfaction_insights() -> aggregates all reviews into an overall
   customer-satisfaction summary + trend suggestion for the admin
   dashboard. This is the hook described as "AI/ML integration for
   user satisfaction" — it works today on rule-based aggregation, and
   is written so a real trained ML model can be swapped in later by
   only editing this one function (see NOTE below).

NOTE on upgrading to a custom-trained model later:
   Replace the body of analyze_sentiment() with a call to your trained
   model's predict() function, keeping the same return shape:
   {"label": "positive"/"neutral"/"negative", "score": float(-1..1)}
   Nothing else in the app needs to change.
"""
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()


def analyze_sentiment(text: str, rating: int) -> dict:
    """Returns sentiment label + compound score (-1 to 1) for a review."""
    scores = _analyzer.polarity_scores(text or "")
    compound = scores["compound"]

    # Blend text sentiment with star rating for a more reliable label,
    # since a short review like "fine" can score neutral even at 2 stars.
    rating_bias = (rating - 3) / 2  # -1 (1-star) .. +1 (5-star)
    blended = (compound * 0.7) + (rating_bias * 0.3)

    if blended >= 0.25:
        label = "positive"
    elif blended <= -0.25:
        label = "negative"
    else:
        label = "neutral"

    return {"label": label, "score": round(blended, 3)}


def generate_admin_suggestion(label: str, rating: int, text: str) -> str:
    """Short, actionable suggestion for the admin based on the review."""
    text_lower = (text or "").lower()

    urgent_keywords = ["refund", "cancel", "never again", "unsafe", "damage", "leak", "unsafe", "worst"]
    is_urgent = any(k in text_lower for k in urgent_keywords)

    if label == "negative":
        if is_urgent or rating <= 2:
            return ("⚠️ Priority follow-up recommended. Customer appears unhappy — "
                    "call within 24 hours, acknowledge the issue directly, and offer "
                    "a concrete fix (revisit, discount, or refund where appropriate).")
        return ("Reach out personally to understand what went wrong and offer to make "
                "it right. A quick, genuine response often turns this into a repeat customer.")

    if label == "neutral":
        return ("Review is lukewarm — consider a friendly follow-up asking what would "
                "have made the experience a 5-star one. Useful for spotting small service gaps.")

    # positive
    if rating == 5:
        return ("Great review! Thank the customer and, if they're open to it, ask "
                "permission to feature this as a public testimonial on the website.")
    return ("Positive experience overall. A short thank-you reply is enough — consider "
            "asking what could have made it even better.")


def generate_draft_reply(customer_name: str, label: str, rating: int) -> str:
    """AI-drafted reply the admin can edit and send to the customer."""
    first_name = (customer_name or "there").split(" ")[0]

    if label == "negative":
        return (
            f"Hi {first_name},\n\n"
            f"Thank you for letting us know, and we're sorry to hear your experience "
            f"didn't meet expectations. This isn't the standard we aim for at Edens "
            f"Refrigeration and Air-Conditioning.\n\n"
            f"We'd like to make this right — could you let us know a good time for our "
            f"team to call you and sort this out?\n\n"
            f"Kind regards,\nEdens Refrigeration and Air-Conditioning"
        )
    if label == "neutral":
        return (
            f"Hi {first_name},\n\n"
            f"Thanks for taking the time to share your feedback. We're always looking "
            f"to improve — if there's anything specific we could have done better, "
            f"we'd genuinely love to hear it.\n\n"
            f"Kind regards,\nEdens Refrigeration and Air-Conditioning"
        )
    # positive
    return (
        f"Hi {first_name},\n\n"
        f"Thank you so much for the {rating}-star review — really appreciate you taking "
        f"the time! It's great to hear our team could help.\n\n"
        f"Looking forward to being there for your next heating, cooling or refrigeration "
        f"need.\n\n"
        f"Kind regards,\nEdens Refrigeration and Air-Conditioning"
    )


def satisfaction_insights(reviews: list) -> dict:
    """
    Aggregates a list of Review ORM objects into a satisfaction summary
    for the admin dashboard.
    """
    if not reviews:
        return {
            "total_reviews": 0,
            "average_rating": None,
            "positive_pct": 0,
            "neutral_pct": 0,
            "negative_pct": 0,
            "overall_status": "No reviews yet",
            "admin_suggestion": "No customer feedback yet — consider prompting recent "
                                 "customers to leave a review to start building trust signals.",
        }

    total = len(reviews)
    avg_rating = round(sum(r.rating for r in reviews) / total, 2)

    pos = sum(1 for r in reviews if r.sentiment_label == "positive")
    neu = sum(1 for r in reviews if r.sentiment_label == "neutral")
    neg = sum(1 for r in reviews if r.sentiment_label == "negative")

    positive_pct = round((pos / total) * 100, 1)
    neutral_pct = round((neu / total) * 100, 1)
    negative_pct = round((neg / total) * 100, 1)

    if negative_pct >= 25:
        overall_status = "Needs Attention"
        suggestion = (f"{negative_pct}% of reviews are negative — review recent negative "
                      f"feedback for a common root cause (e.g. response time, pricing "
                      f"clarity, technician communication) before it affects reputation.")
    elif positive_pct >= 75:
        overall_status = "Excellent"
        suggestion = ("Customer satisfaction is strong. Good time to ask your happiest "
                      "customers for public reviews/testimonials to reinforce this.")
    else:
        overall_status = "Stable"
        suggestion = ("Satisfaction is steady. Keep monitoring new reviews for early "
                      "signs of recurring complaints.")

    return {
        "total_reviews": total,
        "average_rating": avg_rating,
        "positive_pct": positive_pct,
        "neutral_pct": neutral_pct,
        "negative_pct": negative_pct,
        "overall_status": overall_status,
        "admin_suggestion": suggestion,
    }
