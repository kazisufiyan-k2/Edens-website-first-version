import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from database import engine, Base
import models  # noqa: F401  (ensures models are registered before create_all)
from routes import enquiry, review, admin

load_dotenv()
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Edens Refrigeration and Air-Conditioning API",
    description="Backend API for enquiries, AI-powered review management, and admin dashboard.",
    version="1.0.0",
)

# ---- CORS ----
allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "*")
allowed_origins = ["*"] if allowed_origins_raw.strip() == "*" else [o.strip() for o in allowed_origins_raw.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Create DB tables on startup (SQLite file created automatically) ----
Base.metadata.create_all(bind=engine)

# ---- Routers ----
app.include_router(enquiry.router, tags=["Enquiry"])
app.include_router(review.router, tags=["Reviews"])
app.include_router(admin.router, tags=["Admin"])


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "Edens Refrigeration and Air-Conditioning API",
        "docs": "/docs",
    }


@app.get("/api/health")
def health_check():
    return {"status": "healthy"}
