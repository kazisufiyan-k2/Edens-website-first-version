// ============================================================
// ENQUIRY FORM — validation + submit to FastAPI backend
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('enquiry-form');
  if (!form) return;

  const statusBox = document.getElementById('enquiry-status');
  const submitBtn = form.querySelector('button[type="submit"]');

  const phonePattern = /^[0-9+\-\s()]{7,20}$/;
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  function setError(fieldId, message) {
    const errorEl = document.getElementById(fieldId + '-error');
    if (errorEl) {
      errorEl.textContent = message;
      errorEl.classList.toggle('show', Boolean(message));
    }
  }

  function validate(data) {
    let valid = true;

    if (!data.customer_name.trim()) {
      setError('enq-name', 'Please enter your name.');
      valid = false;
    } else setError('enq-name', '');

    if (!phonePattern.test(data.phone.trim())) {
      setError('enq-phone', 'Please enter a valid contact number.');
      valid = false;
    } else setError('enq-phone', '');

    if (!emailPattern.test(data.email.trim())) {
      setError('enq-email', 'Please enter a valid email address.');
      valid = false;
    } else setError('enq-email', '');

    if (!data.message.trim() || data.message.trim().length < 10) {
      setError('enq-message', 'Please briefly describe your issue or requirement (min 10 characters).');
      valid = false;
    } else setError('enq-message', '');

    return valid;
  }

  function showStatus(type, message) {
    statusBox.textContent = message;
    statusBox.className = 'form-status show ' + type;
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const data = {
      business_name: document.getElementById('enq-business').value,
      customer_name: document.getElementById('enq-name').value,
      phone: document.getElementById('enq-phone').value,
      email: document.getElementById('enq-email').value,
      site_address: document.getElementById('enq-address').value,
      message: document.getElementById('enq-message').value,
    };

    if (!validate(data)) {
      showStatus('error', 'Please fix the highlighted fields and try again.');
      return;
    }

    submitBtn.disabled = true;
    const originalText = submitBtn.textContent;
    submitBtn.textContent = 'Sending...';

    try {
      const res = await fetch(`${API_BASE_URL}/api/enquiry`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Something went wrong. Please try again.');
      }

      showStatus('success', "Thank you! Your enquiry has been received — our team will contact you shortly.");
      form.reset();
    } catch (err) {
      showStatus('error', err.message || 'Unable to send enquiry right now. Please call us directly.');
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = originalText;
    }
  });
});
