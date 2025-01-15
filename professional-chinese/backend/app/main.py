from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from .routers import vocabulary, practice
from .database import engine, Base
from . import models
from .initial_data import seed_vocabulary

app = FastAPI(
    title="Professional Chinese Learning API",
    description="API for professional context-based Chinese language learning",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Drop and recreate all tables
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(vocabulary.router, prefix="/api/vocabulary", tags=["Vocabulary"])
app.include_router(practice.router, prefix="/api/practice", tags=["Practice"])

@app.on_event("startup")
async def startup_event():
    # Create a new database session
    from .database import SessionLocal
    db = SessionLocal()
    try:
        # Seed initial vocabulary data
        seed_vocabulary(db)
    finally:
        db.close()

@app.get("/")
def root():
    return {"message": "Welcome to Professional Chinese Learning API"}
