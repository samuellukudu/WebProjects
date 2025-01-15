from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime, timedelta
from pydantic import BaseModel
from .. import models
from ..database import get_db

router = APIRouter()

class VocabularyInPractice(BaseModel):
    id: int
    chinese_simplified: str
    chinese_traditional: str | None
    pinyin: str
    english: str
    context_category: str
    difficulty_level: int
    usage_examples: dict

    class Config:
        from_attributes = True

class PracticeSession(BaseModel):
    vocabulary_items: List[VocabularyInPractice]
    session_id: str
    timestamp: datetime

    class Config:
        from_attributes = True

class ProgressUpdate(BaseModel):
    vocabulary_id: int
    proficiency_level: int

@router.get("/daily-session", response_model=PracticeSession)
async def get_daily_session(db: Session = Depends(get_db)):
    # Get 5 random vocabulary items
    vocabulary_items = db.query(models.Vocabulary).order_by(func.random()).limit(5).all()
    
    if not vocabulary_items:
        raise HTTPException(status_code=404, detail="No vocabulary items found")
    
    # Create a practice session
    session = {
        "vocabulary_items": vocabulary_items,
        "session_id": datetime.now().strftime("%Y%m%d%H%M%S"),
        "timestamp": datetime.now()
    }
    
    return session

@router.post("/update-progress")
async def update_progress(progress: ProgressUpdate, db: Session = Depends(get_db)):
    # Find existing progress or create new one
    db_progress = db.query(models.UserProgress).filter(
        models.UserProgress.vocabulary_id == progress.vocabulary_id
    ).first()
    
    if db_progress:
        # Update existing progress
        db_progress.proficiency_level = progress.proficiency_level
        db_progress.last_reviewed = datetime.now()
        db_progress.next_review = datetime.now() + timedelta(days=1)  # Simple spaced repetition
    else:
        # Create new progress
        db_progress = models.UserProgress(
            vocabulary_id=progress.vocabulary_id,
            proficiency_level=progress.proficiency_level,
            last_reviewed=datetime.now(),
            next_review=datetime.now() + timedelta(days=1)
        )
        db.add(db_progress)
    
    try:
        db.commit()
        return {"message": "Progress updated successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    total_items = db.query(models.Vocabulary).count()
    reviewed_items = db.query(models.UserProgress).count()
    mastered_items = db.query(models.UserProgress).filter(
        models.UserProgress.proficiency_level >= 4
    ).count()
    
    return {
        "total_items": total_items,
        "reviewed_items": reviewed_items,
        "mastered_items": mastered_items,
        "completion_rate": (reviewed_items / total_items * 100) if total_items > 0 else 0
    }
