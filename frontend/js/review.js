// ============================================================
// REVIEW FORM — customer submits review; backend runs AI sentiment
// analysis on it automatically (see backend/ai_review.py)
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('review-form');
  if (!form) return;

  const statusBox = document.getElementById('review-status');
  const submitBtn = form.querySelector('button[type="submit"]');
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  function setError(fieldId, message) {
    const errorEl = document.getElementById(fieldId + '-error');
    if (errorEl) {
      errorEl.textContent = message;
      errorEl.classList.toggle('show', Boolean(message));
    }
  }

  function showStatus(type, message) {
    statusBox.textContent = message;
    statusBox.className = 'form-status show ' + type;
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const data = {
      customer_name: document.getElementById('rev-name').value,
      email: document.getElementById('rev-email').value,
      rating: parseInt(document.getElementById('review-rating').value || '0', 10),
      message: document.getElementById('rev-message').value,
    };

    let valid = true;
    if (!data.customer_name.trim()) { setError('rev-name', 'Please enter your name.'); valid = false; }
    else setError('rev-name', '');

    if (!emailPattern.test(data.email.trim())) { setError('rev-email', 'Please enter a valid email address.'); valid = false; }
    else setError('rev-email', '');

    if (!data.rating) { setError('rev-rating', 'Please select a star rating.'); valid = false; }
    else setError('rev-rating', '');

    if (!data.message.trim() || data.message.trim().length < 5) { setError('rev-message', 'Please write a short review.'); valid = false; }
    else setError('rev-message', '');

    if (!valid) {
      showStatus('error', 'Please fix the highlighted fields and try again.');
      return;
    }

    submitBtn.disabled = true;
    const originalText = submitBtn.textContent;
    submitBtn.textContent = 'Submitting...';

    try {
      const res = await fetch(`${API_BASE_URL}/api/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Something went wrong. Please try again.');
      }

      showStatus('success', 'Thank you for your feedback! Your review has been submitted.');
      form.reset();
      document.querySelectorAll('.star-rating span').forEach(s => s.classList.remove('active'));
    } catch (err) {
      showStatus('error', err.message || 'Unable to submit review right now.');
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = originalText;
    }
  });
});
