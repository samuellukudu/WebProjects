# from fastapi import APIRouter

# router = APIRouter(prefix="/auth", tags=["auth"])

# # Placeholder route until auth is properly implemented
# @router.get("/status")
# def auth_status():
#     return {"status": "Authentication temporarily disabled"}
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import timedelta
from src.api.schemas.user import UserCreate, UserLogin, Token
from src.services.auth import create_user, authenticate_user, create_access_token
from src.api.db.database import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/auth", tags=["Authentication"])

ACCESS_TOKEN_EXPIRE_MINUTES = 60

@router.post("/register", response_model=Token)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    user = create_user(db, user_data)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}
