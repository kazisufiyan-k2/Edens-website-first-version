// ============================================================
// EDENS ADMIN DASHBOARD
// ============================================================
const API_BASE_URL = "http://localhost:8000";
const TOKEN_KEY = "edens_admin_token";

// ---------------- AUTH ----------------
function getToken() { return sessionStorage.getItem(TOKEN_KEY); }
function setToken(t) { sessionStorage.setItem(TOKEN_KEY, t); }
function clearToken() { sessionStorage.removeItem(TOKEN_KEY); }

function authHeaders() {
  return { "Authorization": `Bearer ${getToken()}`, "Content-Type": "application/json" };
}

async function apiGet(path) {
  const res = await fetch(`${API_BASE_URL}${path}`, { headers: authHeaders() });
  if (res.status === 401) { clearToken(); showLogin(); throw new Error("Session expired"); }
  if (!res.ok) throw new Error("Request failed");
  return res.json();
}

async function apiPatch(path, body) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: "PATCH", headers: authHeaders(), body: JSON.stringify(body),
  });
  if (res.status === 401) { clearToken(); showLogin(); throw new Error("Session expired"); }
  if (!res.ok) throw new Error("Request failed");
  return res.json();
}

function showLogin() {
  document.getElementById("login-screen").classList.remove("hidden");
  document.getElementById("dashboard").classList.add("hidden");
}
function showDashboard() {
  document.getElementById("login-screen").classList.add("hidden");
  document.getElementById("dashboard").classList.remove("hidden");
  loadOverview();
  loadEnquiries();
  loadReviews();
}

document.addEventListener("DOMContentLoaded", () => {
  if (getToken()) showDashboard(); else showLogin();

  document.getElementById("login-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const username = document.getElementById("login-username").value;
    const password = document.getElementById("login-password").value;
    const errorBox = document.getElementById("login-error");
    errorBox.classList.remove("show");

    try {
      const res = await fetch(`${API_BASE_URL}/api/admin/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      if (!res.ok) throw new Error("Invalid username or password.");
      const data = await res.json();
      setToken(data.token);
      showDashboard();
    } catch (err) {
      errorBox.textContent = err.message;
      errorBox.classList.add("show");
    }
  });

  document.getElementById("logout-btn").addEventListener("click", () => {
    clearToken();
    showLogin();
  });

  document.querySelectorAll(".nav-item").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".nav-item").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById(`tab-${btn.dataset.tab}`).classList.add("active");
    });
  });
});

// ---------------- OVERVIEW ----------------
async function loadOverview() {
  try {
    const data = await apiGet("/api/admin/reviews/insights");
    document.getElementById("stat-total").textContent = data.total_reviews;
    document.getElementById("stat-avg").textContent = data.average_rating ?? "—";
    document.getElementById("stat-pos").textContent = data.positive_pct + "%";
    document.getElementById("stat-neg").textContent = data.negative_pct + "%";
    document.getElementById("insight-status").textContent = data.overall_status;
    document.getElementById("insight-text").textContent = data.admin_suggestion;
  } catch (e) { /* handled by auth redirect */ }
}

// ---------------- ENQUIRIES ----------------
async function loadEnquiries() {
  const container = document.getElementById("enquiries-list");
  try {
    const items = await apiGet("/api/admin/enquiries");
    if (!items.length) {
      container.innerHTML = `<div class="empty-state">No enquiries yet.</div>`;
      return;
    }
    container.innerHTML = items.map(renderEnquiryCard).join("");
    items.forEach(item => {
      const select = document.getElementById(`status-${item.id}`);
      if (select) {
        select.addEventListener("change", async () => {
          await apiPatch(`/api/admin/enquiries/${item.id}`, { status: select.value });
        });
      }
    });
  } catch (e) { /* handled */ }
}

function renderEnquiryCard(item) {
  const date = new Date(item.created_at).toLocaleString();
  return `
    <div class="card">
      <div class="card-top">
        <div>
          <div class="name">${escapeHtml(item.customer_name)} ${item.business_name ? `— ${escapeHtml(item.business_name)}` : ""}</div>
          <div class="meta">${date}</div>
        </div>
        <select class="status-select" id="status-${item.id}">
          <option value="new" ${item.status === "new" ? "selected" : ""}>New</option>
          <option value="contacted" ${item.status === "contacted" ? "selected" : ""}>Contacted</option>
          <option value="resolved" ${item.status === "resolved" ? "selected" : ""}>Resolved</option>
        </select>
      </div>
      <div class="card-body">
        <div class="card-field"><strong>Phone:</strong> ${escapeHtml(item.phone)}</div>
        <div class="card-field"><strong>Email:</strong> ${escapeHtml(item.email)}</div>
        ${item.site_address ? `<div class="card-field"><strong>Site Address:</strong> ${escapeHtml(item.site_address)}</div>` : ""}
        <p style="margin-top:10px;">${escapeHtml(item.message)}</p>
      </div>
    </div>
  `;
}

// ---------------- REVIEWS (AI) ----------------
async function loadReviews() {
  const container = document.getElementById("reviews-list");
  try {
    const items = await apiGet("/api/admin/reviews");
    if (!items.length) {
      container.innerHTML = `<div class="empty-state">No reviews yet.</div>`;
      return;
    }
    container.innerHTML = items.map(renderReviewCard).join("");

    items.forEach(item => {
      document.getElementById(`publish-${item.id}`)?.addEventListener("click", async () => {
        await apiPatch(`/api/admin/reviews/${item.id}/publish`, { is_published: !item.is_published });
        loadReviews();
      });
      document.getElementById(`reply-toggle-${item.id}`)?.addEventListener("click", () => {
        document.getElementById(`reply-editor-${item.id}`).classList.toggle("show");
      });
      document.getElementById(`reply-send-${item.id}`)?.addEventListener("click", async () => {
        const text = document.getElementById(`reply-text-${item.id}`).value;
        if (!text.trim()) return;
        await apiPatch(`/api/admin/reviews/${item.id}/reply`, { admin_reply: text, send_email: true });
        loadReviews();
      });
    });
  } catch (e) { /* handled */ }
}

function renderReviewCard(item) {
  const date = new Date(item.created_at).toLocaleString();
  const stars = "★".repeat(item.rating) + "☆".repeat(5 - item.rating);
  return `
    <div class="card">
      <div class="card-top">
        <div>
          <div class="name">${escapeHtml(item.customer_name)} <span style="color:#d6283f; margin-left:6px;">${stars}</span></div>
          <div class="meta">${escapeHtml(item.email)} • ${date}</div>
        </div>
        <span class="badge badge-${item.sentiment_label}">${item.sentiment_label}</span>
      </div>
      <div class="card-body">
        <p>"${escapeHtml(item.message)}"</p>
        <div class="ai-box suggestion">
          <span class="ai-label">🤖 AI Suggestion for Admin</span>
          ${escapeHtml(item.ai_admin_suggestion || "")}
        </div>
        <div class="ai-box draft">
          <span class="ai-label">✉️ AI Draft Reply</span>
          ${escapeHtml(item.ai_draft_reply || "")}
        </div>
        ${item.admin_reply ? `<div class="ai-box" style="border-left-color:#1c7a3f;"><span class="ai-label" style="color:#1c7a3f;">Sent Reply ${item.reply_sent ? "(emailed)" : ""}</span>${escapeHtml(item.admin_reply)}</div>` : ""}
      </div>
      <div class="card-actions">
        <button class="btn-sm ${item.is_published ? "primary" : "outline"}" id="publish-${item.id}">
          ${item.is_published ? "Published on site ✓" : "Publish on site"}
        </button>
        <button class="btn-sm outline" id="reply-toggle-${item.id}">Edit &amp; Send Reply</button>
      </div>
      <div class="reply-editor" id="reply-editor-${item.id}">
        <textarea id="reply-text-${item.id}">${escapeHtml(item.admin_reply || item.ai_draft_reply || "")}</textarea>
        <button class="btn-sm primary" style="margin-top:8px;" id="reply-send-${item.id}">Send Reply Email</button>
      </div>
    </div>
  `;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}
