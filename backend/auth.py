"""
Minimal admin authentication.

Kept intentionally simple (single admin user via env credentials +
a bearer token) since this is a small business site with one admin.
Good enough for production use on a low-traffic site; if you later
need multiple admin accounts / roles, swap this for a proper
users table + hashed passwords + JWT.
"""
import os
import secrets
from fastapi import Header, HTTPException, status
from dotenv import load_dotenv

load_dotenv()

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change-this-password")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "change-this-to-a-long-random-secret")


def verify_admin_credentials(username: str, password: str) -> bool:
    return secrets.compare_digest(username, ADMIN_USERNAME) and secrets.compare_digest(password, ADMIN_PASSWORD)


def require_admin(authorization: str = Header(default=None)):
    """
    FastAPI dependency — expects header: Authorization: Bearer <ADMIN_TOKEN>
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid authorization header.")

    token = authorization.split(" ", 1)[1]
    if not secrets.compare_digest(token, ADMIN_TOKEN):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin token.")
    return True
