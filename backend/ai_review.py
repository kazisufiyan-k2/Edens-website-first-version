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
import random

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()


def analyze_sentiment(text: str, rating: int) -> dict:
    """Returns sentiment label + compound score (-1 to 1) for a review."""
    raw_text = text or ""
    lowered = raw_text.lower()

    negative_keywords = [
        "bad", "poor", "terrible", "awful", "very bad", "worst",
        "disappointed", "frustrated", "problem", "issues", "issue", "slow",
        "rude", "late", "failed", "broken", "leak", "damage", "unsafe",
        "refund", "never again", "not happy", "service bad"
    ]
    positive_keywords = [
        "good", "great", "excellent", "amazing", "happy", "very good",
        "fast", "professional", "friendly", "smooth", "perfect", "satisfied",
        "love", "fantastic", "reliable", "quick", "helpful", "nice"
    ]
    explicit_negative_phrases = [
        "not good", "bad service", "service bad", "not happy", "not satisfied",
        "not great", "very bad", "never again", "did not like", "didn't like"
    ]
    explicit_positive_phrases = [
        "very good", "great service", "excellent service", "really good",
        "happy with", "very happy", "loved it", "fantastic service"
    ]

    negative_hits = sum(1 for keyword in negative_keywords if keyword in lowered)
    positive_hits = sum(1 for keyword in positive_keywords if keyword in lowered)
    explicit_negative = any(phrase in lowered for phrase in explicit_negative_phrases)
    explicit_positive = any(phrase in lowered for phrase in explicit_positive_phrases)

    # Explicit phrases should win over a misleading star click.
    if explicit_negative and not explicit_positive:
        label = "negative"
        score = -0.8
        return {"label": label, "score": round(score, 3)}

    if explicit_positive and not explicit_negative:
        label = "positive"
        score = 0.8
        return {"label": label, "score": round(score, 3)}

    if negative_hits > 0 and positive_hits == 0:
        label = "negative"
        score = -0.7
        return {"label": label, "score": round(score, 3)}

    if positive_hits > 0 and negative_hits == 0:
        label = "positive"
        score = 0.7
        return {"label": label, "score": round(score, 3)}

    scores = _analyzer.polarity_scores(raw_text)
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
        reply_pool = [
            f"Hi {first_name},\n\nWe are very sorry that your experience fell short of expectations. We take every issue seriously and understand how frustrating it is when your heating, cooling, or refrigeration needs are not resolved properly. We would appreciate the chance to speak with you directly and make this right as quickly as possible.\n\nIf you are open to it, please let us know a good time for our team to call you and discuss the next steps.\n\nKind regards,\nEdens Refrigeration and Air-Conditioning",
            f"Hi {first_name},\n\nThank you for raising this with us. We are sorry to hear your service experience did not meet the level of care and quality we aim to provide. We understand how disruptive a problem like this can be, especially when your home or business depends on reliable climate control.\n\nWe would welcome the opportunity to review what happened with you and arrange a proper follow-up. Please send us a few details so we can contact you and sort it out quickly.\n\nKind regards,\nEdens Refrigeration and Air-Conditioning",
            f"Hi {first_name},\n\nWe are sorry to hear that your visit did not go as planned. This is not the standard of service we expect from our team, and we appreciate you taking the time to tell us. We understand the importance of getting this matter resolved efficiently and professionally.\n\nIf you are willing, we would like to escalate this internally and speak with you directly so we can address the issue and find a suitable resolution.\n\nKind regards,\nEdens Refrigeration and Air-Conditioning",
            f"Hi {first_name},\n\nThank you for bringing this to our attention. We are genuinely sorry that your experience left you disappointed, and we understand why you would feel that way. We value your feedback and want to act on it without delay.\n\nOur team would be happy to contact you promptly to discuss the issue, arrange a revisit, and do everything we can to restore your confidence in our service.\n\nKind regards,\nEdens Refrigeration and Air-Conditioning",
            f"Hi {first_name},\n\nWe appreciate you telling us about this. We are sorry that the service did not meet expectations and understand your frustration. We know that problems with heating, cooling, and refrigeration can affect your home or business quickly, so we take this seriously.\n\nIf needed, we are happy to revisit the work, discuss a refund or adjustment, or find another practical way to put things right.\n\nKind regards,\nEdens Refrigeration and Air-Conditioning",
            f"Hi {first_name},\n\nWe are sorry to hear that your experience was disappointing, and we appreciate you being honest with us. We understand that a poor service experience can quickly damage trust, and we want to acknowledge that.\n\nIf you are willing, we would like the chance to make things right and invite you to contact us so we can discuss a second opportunity to provide the service you expected.\n\nKind regards,\nEdens Refrigeration and Air-Conditioning",
            f"Hi {first_name},\n\nThank you for sharing this concern with us. We are sorry that the issue was not resolved to your satisfaction, and we understand how frustrating that must have been. We take this feedback seriously and want to ensure your next interaction with us is a much better one.\n\nPlease let us know the best way to contact you, and we will prioritise a prompt reschedule or follow-up so we can address the matter properly.\n\nKind regards,\nEdens Refrigeration and Air-Conditioning",
            f"Hi {first_name},\n\nWe appreciate you taking the time to tell us about this, and we are sorry the service fell below the standard you expected. We understand how difficult it can be when a problem is not handled in a timely or professional way.\n\nOur management team would like to review the details with you directly so we can understand the full picture and ensure the right steps are taken to make it right.\n\nKind regards,\nEdens Refrigeration and Air-Conditioning",
            f"Hi {first_name},\n\nWe are sincerely sorry that your experience was disappointing, and we appreciate the opportunity to respond. We understand how important it is to have a reliable, well-managed service when it comes to heating, cooling, or refrigeration.\n\nWe would be pleased to arrange a no-charge revisit or discuss the issue with you directly so we can make a proper amends and restore confidence in our work.\n\nKind regards,\nEdens Refrigeration and Air-Conditioning",
            f"Hi {first_name},\n\nThank you for reaching out and for being open about what went wrong. We are sorry that the issue was not resolved in a way that left you feeling supported, and we take that feedback seriously. We want to understand exactly what happened so we can improve and do better next time.\n\nPlease feel free to contact us with the details, and we would welcome the chance to discuss the matter with you directly and find a constructive solution.\n\nKind regards,\nEdens Refrigeration and Air-Conditioning",
        ]
        return random.choice(reply_pool)

    if label == "neutral":
        reply_pool = [
            f"Hi {first_name},\n\nThank you for taking the time to leave feedback. We value your opinion and would love to understand what, if anything, could have made the experience even better for you.\n\nIf there is a particular part of the service you would like us to improve, please let us know so we can keep learning and delivering better results.\n\nKind regards,\nEdens Refrigeration and Air-Conditioning",
            f"Hi {first_name},\n\nWe appreciate your feedback and are grateful you took the time to share it with us. We are always looking for ways to improve the experience for our customers, whether that relates to communication, timing, or the quality of the work itself.\n\nIf you can tell us a little more about what stood out to you, we would be very happy to take that on board.\n\nKind regards,\nEdens Refrigeration and Air-Conditioning",
            f"Hi {first_name},\n\nThank you for your message. We appreciate your feedback and are glad to know you took the time to let us know about your experience. We are always working to provide a professional service that feels smooth, clear, and reliable from start to finish.\n\nIf there is anything specific you feel we could improve, please share it with us and we will take it into consideration.\n\nKind regards,\nEdens Refrigeration and Air-Conditioning",
            f"Hi {first_name},\n\nThank you for the feedback. We are pleased to hear you chose us and we would welcome the chance to learn a little more about your experience. There is always room to improve, and we value honest input from our customers.\n\nIf there was a particular detail that stood out to you, we would be grateful to hear more so we can keep refining our service.\n\nKind regards,\nEdens Refrigeration and Air-Conditioning",
            f"Hi {first_name},\n\nThank you for the review and for taking the time to share your thoughts. We appreciate hearing from customers and we always welcome the opportunity to improve.\n\nIf there is anything we could have done differently to make the experience even better, we would be glad to hear from you.\n\nKind regards,\nEdens Refrigeration and Air-Conditioning",
            f"Hi {first_name},\n\nWe appreciate your feedback and thank you for the time you spent telling us about your experience. We are pleased that you chose Edens and are always looking for ways to make our service more helpful and consistent.\n\nIf you feel there is anything we could do better, we would be very grateful to hear about it so we can continue improving.\n\nKind regards,\nEdens Refrigeration and Air-Conditioning",
            f"Hi {first_name},\n\nThank you for your kind words and for taking the time to leave feedback. We genuinely value customer input, and this helps us understand where we are doing well and where we can do even better.\n\nIf you are happy to share a little more detail, we would be grateful to hear what would have made the experience stand out even more.\n\nKind regards,\nEdens Refrigeration and Air-Conditioning",
            f"Hi {first_name},\n\nThank you for reaching out and for sharing your feedback. We appreciate the chance to learn from each customer experience and we take every comment seriously.\n\nIf there was anything specific that could have improved the service for you, we would welcome the opportunity to hear about it and apply that learning going forward.\n\nKind regards,\nEdens Refrigeration and Air-Conditioning",
            f"Hi {first_name},\n\nWe value your feedback and are grateful you took the time to let us know how things went. We are always interested in understanding what matters most to our customers and how we can improve the service experience.\n\nIf you are willing, we would love to hear a little more about what you experienced so we can keep refining our approach.\n\nKind regards,\nEdens Refrigeration and Air-Conditioning",
            f"Hi {first_name},\n\nThank you for sharing your thoughts with us. We appreciate the opportunity to hear from customers and we are always looking for ways to improve. Your feedback helps us learn where we are doing well and where we can do better in the future.\n\nIf you have any additional comments, we would be glad to hear them and take them into account as we continue to improve our service.\n\nKind regards,\nEdens Refrigeration and Air-Conditioning",
        ]
        return random.choice(reply_pool)

    if label == "positive" and rating == 5:
        reply_pool = [
            f"Hi {first_name},\n\nThank you so much for the wonderful review and for taking the time to share your feedback with us. We are delighted to hear that your experience with Edens Refrigeration and Air-Conditioning was such a positive one.\n\nIt means a great deal to our team to know we could help you comfortably and professionally, and we are grateful for your trust.\n\nKind regards,\nEdens Refrigeration and Air-Conditioning",
            f"Hi {first_name},\n\nWe really appreciate your 5-star review and are delighted that you had such a positive experience with us. Thank you for recognising the effort our team puts into delivering reliable, professional service.\n\nWe are very grateful for the trust you placed in us and we hope to be there for you again whenever you need heating, cooling, or refrigeration support.\n\nKind regards,\nEdens Refrigeration and Air-Conditioning",
            f"Hi {first_name},\n\nThank you for the kind words and for leaving such a glowing review. Your feedback is a wonderful reminder of why we work so hard to deliver dependable service and quality workmanship to every customer.\n\nWe are proud to have been part of your experience and appreciate the confidence you have shown in our team.\n\nKind regards,\nEdens Refrigeration and Air-Conditioning",
            f"Hi {first_name},\n\nWe are so grateful for your review and for the trust you have placed in our business. It is wonderful to know that your experience was smooth, professional, and reassuring from start to finish.\n\nYour support means a lot to us, and we would be delighted to assist you again in the future should you need any further heating, cooling, or refrigeration services.\n\nKind regards,\nEdens Refrigeration and Air-Conditioning",
            f"Hi {first_name},\n\nThank you for the positive feedback and for recommending us so highly. We are pleased to hear our team delivered a service experience that met your expectations and left you confident in the result.\n\nWe appreciate your support and are always here to help with any future requirements.\n\nKind regards,\nEdens Refrigeration and Air-Conditioning",
            f"Hi {first_name},\n\nThank you very much for your kind review. We really appreciate you taking the time to share your experience, and we are delighted to hear that our service was helpful and reassuring.\n\nIt is feedback like this that motivates our team to keep raising the standard and delivering the best possible experience for our customers.\n\nKind regards,\nEdens Refrigeration and Air-Conditioning",
            f"Hi {first_name},\n\nYour 5-star review is truly appreciated, and we are so pleased to hear that you had such a positive experience with Edens. We take great pride in delivering honest, dependable service and being there when our customers need us.\n\nThank you for choosing us and for sharing your experience so clearly — it means a great deal to our team.\n\nKind regards,\nEdens Refrigeration and Air-Conditioning",
            f"Hi {first_name},\n\nThank you for the wonderful feedback and for making the effort to leave a review. We are very pleased to know that your experience was a positive one and that our team was able to help in a way that felt professional and reassuring.\n\nWe really value your trust and are grateful for the confidence you have shown in us.\n\nKind regards,\nEdens Refrigeration and Air-Conditioning",
            f"Hi {first_name},\n\nWe are very thankful for your support and for the time you took to leave such a positive review. Being part of the Christchurch community means a great deal to us, and it is wonderful to know our work made a difference for you.\n\nWe look forward to continuing to serve local homes and businesses with the same level of care and professionalism.\n\nKind regards,\nEdens Refrigeration and Air-Conditioning",
            f"Hi {first_name},\n\nThank you so much for your kind words. We are truly grateful for your support and for sharing such a positive experience with others. It means a lot to know we met your expectations and delivered service you felt good about.\n\nWe are thankful for your trust and hope to see you again whenever you need expert heating, cooling, or refrigeration support.\n\nKind regards,\nEdens Refrigeration and Air-Conditioning",
        ]
        return random.choice(reply_pool)

    # positive under 5-star
    reply_pool = [
        f"Hi {first_name},\n\nThank you for taking the time to leave a review. We are grateful for your feedback and are pleased to hear that there were parts of the experience that you appreciated. We always want to make sure our customers feel supported and understood from start to finish.\n\nIf there is anything specific that would have made the experience even better, we would be glad to hear it so we can continue improving.\n\nKind regards,\nEdens Refrigeration and Air-Conditioning",
        f"Hi {first_name},\n\nThank you for your feedback and for sharing your experience with us. We are glad to know there were positive aspects to the service, and we appreciate the chance to learn from the rest. We value the opportunity to improve and make every customer experience stronger.\n\nPlease feel free to let us know what would have made the service truly exceptional for you.\n\nKind regards,\nEdens Refrigeration and Air-Conditioning",
        f"Hi {first_name},\n\nThank you for taking the time to leave us this review. We appreciate your honesty and are always looking for ways to improve the service we provide. It is helpful to understand where we can do better so we can keep refining our approach.\n\nWe are grateful for the opportunity to learn from your experience and we appreciate your willingness to share it with us.\n\nKind regards,\nEdens Refrigeration and Air-Conditioning",
        f"Hi {first_name},\n\nThank you for your review and for taking the time to let us know how we did. We are pleased to hear that there were some parts of the experience that worked well, and we are grateful for the opportunity to improve the rest.\n\nWe would be glad to welcome you back in the future and do our best to deliver an even better experience next time.\n\nKind regards,\nEdens Refrigeration and Air-Conditioning",
        f"Hi {first_name},\n\nWe appreciate you sharing your feedback with us. We are always looking for ways to improve our service and the experience we provide to customers, and we value hearing where we can do better.\n\nIf you are open to it, we would welcome the chance to understand what would have made the service feel more complete or more consistent for you.\n\nKind regards,\nEdens Refrigeration and Air-Conditioning",
        f"Hi {first_name},\n\nThank you for taking the time to leave your honest feedback. We appreciate the opportunity to learn from your experience and understand where there may have been a gap. We want every customer to feel supported, informed, and confident in the work we do.\n\nIf you are happy to share a little more, we would be grateful to know what would have made the experience feel better from your perspective.\n\nKind regards,\nEdens Refrigeration and Air-Conditioning",
        f"Hi {first_name},\n\nWe are thankful for your feedback and for the chance to respond. We understand that even a mostly positive experience can still have room for improvement, and we value that insight. Our goal is to keep improving so our service feels steady and reliable every time.\n\nIf you are willing, we would appreciate the chance to hear what we could do better next time so we can show you the standard of service we are aiming for.\n\nKind regards,\nEdens Refrigeration and Air-Conditioning",
        f"Hi {first_name},\n\nThank you for your honest feedback. We are grateful for the opportunity to learn from it and we appreciate that you shared details about your experience with us. We value the trust our customers place in us and want to keep improving the standard of service we provide.\n\nIf there was one thing we could do differently to make it feel more complete for you, we would welcome that insight.\n\nKind regards,\nEdens Refrigeration and Air-Conditioning",
        f"Hi {first_name},\n\nWe appreciate you leaving feedback and we are grateful for the opportunity to learn from it. We know that even small improvements can have a big impact on how a customer feels about the full experience, and we take that seriously.\n\nWe hope to earn your confidence again in future and would welcome the chance to do even better on the next opportunity.\n\nKind regards,\nEdens Refrigeration and Air-Conditioning",
        f"Hi {first_name},\n\nThank you for your review and for taking the time to share your thoughts. We value your honesty and appreciate the chance to hear what could have made the experience even stronger. We always aim to provide a reliable, professional service and we are grateful for the feedback that helps us improve.\n\nIf you are open to it, we would be happy to speak with you again and do our best to deliver a better experience next time.\n\nKind regards,\nEdens Refrigeration and Air-Conditioning",
    ]
    return random.choice(reply_pool)


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


if __name__ == "__main__":
    for lbl, rt in [("negative", 1), ("neutral", 3), ("positive", 5), ("positive", 4)]:
        results = set()
        for _ in range(30):
            results.add(generate_draft_reply("John", lbl, rt))
        print(f"{lbl} (rating={rt}): {len(results)} unique replies seen in 30 calls (pool size should be 10)")
