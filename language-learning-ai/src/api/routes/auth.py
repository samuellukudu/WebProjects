from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])

# Placeholder route until auth is properly implemented
@router.get("/status")
def auth_status():
    return {"status": "Authentication temporarily disabled"}