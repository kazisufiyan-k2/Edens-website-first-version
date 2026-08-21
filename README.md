# Edens Refrigeration and Air-Conditioning — Website

Simple stack: **HTML + CSS + JS** frontend, **FastAPI** backend (SQLite database — no
separate DB server needed), with a built-in **AI review system**.

```
edens-website/
├── frontend/        <- the public website (index, services, about, contact)
├── admin/           <- admin dashboard (enquiries + AI review management)
└── backend/         <- FastAPI API (enquiries, reviews, AI sentiment, email)
```

---

## 1. Run the Backend (FastAPI)

Open a terminal in VS Code inside the `backend/` folder:

```bash
cd backend
python -m venv venv

# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

Copy the environment file and edit it:

```bash
cp .env.example .env
```

Open `.env` and set:
- `ADMIN_USERNAME` / `ADMIN_PASSWORD` — your real admin login
- `SMTP_*` values — your real email account (Gmail App Password works well)
- `BUSINESS_NOTIFY_EMAIL` — where new enquiries/reviews should be emailed to

**Note:** if you leave the SMTP settings as placeholders, the site still works
fully — emails are just skipped (logged to the terminal) instead of crashing.

Start the server:

```bash
uvicorn main:app --reload --port 8000
```

Backend now runs at **http://localhost:8000**
API docs (auto-generated): **http://localhost:8000/docs**

---

## 2. Run the Frontend (HTML/CSS/JS)

No build step needed — but for the JS `fetch()` calls to the backend to work
properly, serve it with a simple local server instead of double-clicking the
HTML file. In VS Code:

- Install the **"Live Server"** extension, right-click `frontend/index.html` → **"Open with Live Server"**

OR from terminal:

```bash
cd frontend
python -m http.server 5500
```

Then open **http://localhost:5500** in your browser.

Your images: drop them into `frontend/images/` using these exact names (already referenced in the code):
- `logo.png` — already included from your uploaded logo
- `about-1.jpg` — photo for the About section on the homepage

---

## 3. Run the Admin Dashboard

```bash
cd admin
python -m http.server 5600
```

Open **http://localhost:5600/admin.html**

Log in with the `ADMIN_USERNAME` / `ADMIN_PASSWORD` you set in `backend/.env`.

From here you can:
- View all **enquiries** and update their status (New / Contacted / Resolved)
- View all **reviews**, each auto-tagged by AI as Positive / Neutral / Negative
- See an **AI suggestion** on how to handle each review
- Edit and send an **AI-drafted reply** by email to the customer
- **Publish** approved reviews so they show up on the public website
- See an overall **customer satisfaction summary** on the Overview tab

---

## 4. How the AI Review System Works

1. A customer submits a review on the Contact page.
2. The backend (`backend/ai_review.py`) runs it through a sentiment model
   (VADER — pretrained, works fully offline, no API key needed) combined
   with the star rating, and labels it Positive / Neutral / Negative.
3. It generates a short **suggestion for the admin** (e.g. "follow up within
   24 hours") and a **draft reply** the admin can edit before sending.
4. The admin dashboard shows all of this, and lets the admin approve the
   review to appear on the public site, or send the reply by email.
5. The **Overview tab** aggregates all reviews into a satisfaction summary.

**Upgrading to your own trained ML model later:** everything AI-related
lives in one file — `backend/ai_review.py`. Swap the body of
`analyze_sentiment()` with a call to your model and nothing else in the
app needs to change.

---

## 5. Before Going Live

- [ ] Replace placeholder phone number (`+64 00 000 0000`) across all pages
- [ ] Replace placeholder email (`edensqueenstownltd@gmail.com`) across all pages
- [ ] Add real photos to `frontend/images/`
- [ ] Set real SMTP credentials in `backend/.env`
- [ ] Change `ADMIN_PASSWORD` and `ADMIN_TOKEN` in `backend/.env` to something secure
- [ ] When deploying, update `API_BASE_URL` in `frontend/js/config.js` and
      `admin/admin.js` from `localhost:8000` to your live backend URL
- [ ] Set `ALLOWED_ORIGINS` in `backend/.env` to your real website domain (instead of `*`)

---

## Pages Included

**Public site:** Home · Services (all 9 services) · About · Contact (Enquiry form + Review form)
**Admin:** Login · Overview (AI satisfaction insights) · Enquiries · Reviews (AI-powered)
