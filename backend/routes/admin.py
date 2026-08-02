from fastapi import APIRouter, HTTPException, Depends
import schemas
from auth import verify_admin_credentials, require_admin, ADMIN_TOKEN

router = APIRouter()


@router.post("/api/admin/login", response_model=schemas.AdminLoginResponse)
def admin_login(payload: schemas.AdminLogin):
    if not verify_admin_credentials(payload.username, payload.password):
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    # Simple static token model (see auth.py). Frontend stores this and
    # sends it as "Authorization: Bearer <token>" on admin requests.
    return {"token": ADMIN_TOKEN}


@router.get("/api/admin/verify")
def verify_token(_=Depends(require_admin)):
    return {"valid": True}
