from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, case, desc
from typing import List, Optional
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
    session_type: str
    current_level: int

    class Config:
        from_attributes = True

class ProgressUpdate(BaseModel):
    vocabulary_id: int
    proficiency_level: int
    is_correct: bool

def calculate_next_review(proficiency_level: int, is_correct: bool) -> datetime:
    """Calculate next review time based on proficiency and correctness."""
    base_days = 2 ** proficiency_level if is_correct else 1
    # Add some randomness to prevent all reviews clustering
    variance = base_days * 0.2  # 20% variance
    days = base_days + (variance * (datetime.now().timestamp() % 1 - 0.5))
    return datetime.now() + timedelta(days=max(1, days))

def get_user_level(db: Session) -> int:
    """Calculate user's current level based on progress."""
    avg_proficiency = db.query(
        func.avg(models.UserProgress.proficiency_level)
    ).scalar() or 0
    
    return min(5, int(avg_proficiency) + 1)

@router.get("/daily-session", response_model=PracticeSession)
async def get_daily_session(
    session_type: str = "standard",
    db: Session = Depends(get_db)
):
    current_level = get_user_level(db)
    
    # Base query for vocabulary items
    query = db.query(models.Vocabulary)
    
    if session_type == "flashcard":
        # For flashcard mode, prioritize items based on review schedule and difficulty
        subquery = db.query(models.UserProgress.vocabulary_id)
        new_items = query.filter(~models.Vocabulary.id.in_(subquery))
        
        # Get a mix of new and review items
        new_vocab = new_items.filter(
            models.Vocabulary.difficulty_level <= current_level
        ).order_by(func.random()).limit(3).all()
        
        review_vocab = query.join(
            models.UserProgress
        ).filter(
            models.UserProgress.next_review <= datetime.now(),
            models.Vocabulary.difficulty_level <= current_level
        ).order_by(
            models.UserProgress.next_review
        ).limit(2).all()
        
        vocabulary_items = new_vocab + review_vocab
    else:
        # Standard mode: random items at or below current level
        vocabulary_items = query.filter(
            models.Vocabulary.difficulty_level <= current_level
        ).order_by(func.random()).limit(5).all()
    
    if not vocabulary_items:
        raise HTTPException(status_code=404, detail="No vocabulary items found")
    
    return {
        "vocabulary_items": vocabulary_items,
        "session_id": datetime.now().strftime("%Y%m%d%H%M%S"),
        "timestamp": datetime.now(),
        "session_type": session_type,
        "current_level": current_level
    }

@router.post("/update-progress")
async def update_progress(progress: ProgressUpdate, db: Session = Depends(get_db)):
    db_progress = db.query(models.UserProgress).filter(
        models.UserProgress.vocabulary_id == progress.vocabulary_id
    ).first()
    
    next_review = calculate_next_review(progress.proficiency_level, progress.is_correct)
    
    if db_progress:
        # Update existing progress
        if progress.is_correct:
            db_progress.proficiency_level = min(5, db_progress.proficiency_level + 1)
        else:
            db_progress.proficiency_level = max(0, db_progress.proficiency_level - 1)
        
        db_progress.last_reviewed = datetime.now()
        db_progress.next_review = next_review
    else:
        # Create new progress
        initial_level = 1 if progress.is_correct else 0
        db_progress = models.UserProgress(
            vocabulary_id=progress.vocabulary_id,
            proficiency_level=initial_level,
            last_reviewed=datetime.now(),
            next_review=next_review
        )
        db.add(db_progress)
    
    try:
        db.commit()
        return {
            "message": "Progress updated successfully",
            "new_level": db_progress.proficiency_level,
            "next_review": next_review
        }
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
    
    # Get proficiency distribution
    proficiency_dist = db.query(
        models.UserProgress.proficiency_level,
        func.count(models.UserProgress.id)
    ).group_by(
        models.UserProgress.proficiency_level
    ).all()
    
    # Calculate streak
    today = datetime.now().date()
    recent_activity = db.query(
        func.date(models.UserProgress.last_reviewed)
    ).distinct().order_by(
        desc(func.date(models.UserProgress.last_reviewed))
    ).all()
    
    streak = 0
    for i, (date,) in enumerate(recent_activity):
        if date == today - timedelta(days=i):
            streak += 1
        else:
            break
    
    return {
        "total_items": total_items,
        "reviewed_items": reviewed_items,
        "mastered_items": mastered_items,
        "completion_rate": (reviewed_items / total_items * 100) if total_items > 0 else 0,
        "current_level": get_user_level(db),
        "streak": streak,
        "proficiency_distribution": dict(proficiency_dist)
    }
