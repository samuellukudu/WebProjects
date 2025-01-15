from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from .. import models
from ..database import get_db
from pydantic import BaseModel
from sqlalchemy import or_, func

router = APIRouter()

class ProgressUpdate(BaseModel):
    vocabulary_id: int
    proficiency_level: int

class PracticeSession(BaseModel):
    vocabulary_items: List[dict]
    next_review: datetime

@router.post("/update-progress")
async def update_progress(
    progress: ProgressUpdate,
    db: Session = Depends(get_db)
):
    db_progress = db.query(models.UserProgress).filter(
        models.UserProgress.vocabulary_id == progress.vocabulary_id
    ).first()

    if db_progress:
        db_progress.proficiency_level = progress.proficiency_level
        db_progress.last_reviewed = datetime.utcnow()
        days_until_review = 2 ** db_progress.proficiency_level
        db_progress.next_review = datetime.utcnow() + timedelta(days=days_until_review)
    else:
        db_progress = models.UserProgress(
            vocabulary_id=progress.vocabulary_id,
            proficiency_level=progress.proficiency_level,
            last_reviewed=datetime.utcnow(),
            next_review=datetime.utcnow() + timedelta(days=1)
        )
        db.add(db_progress)

    db.commit()
    return {"status": "success"}

@router.get("/daily-session", response_model=PracticeSession)
async def get_daily_session(
    response: Response,
    db: Session = Depends(get_db)
):
    # Add cache control headers
    response.headers["Cache-Control"] = "public, max-age=300"  # Cache for 5 minutes
    
    current_time = datetime.utcnow()
    
    # First, try to get items that need review (limit to 5 for performance)
    due_items = db.query(models.Vocabulary).join(
        models.UserProgress,
        models.Vocabulary.id == models.UserProgress.vocabulary_id,
        isouter=True
    ).filter(
        or_(
            models.UserProgress.next_review <= current_time,
            models.UserProgress.id == None
        )
    ).limit(5).all()
    
    # If we need more items, get new ones efficiently
    if len(due_items) < 5:
        # Get IDs of all reviewed items
        reviewed_ids = db.query(models.UserProgress.vocabulary_id).distinct()
        
        # Get new items excluding reviewed ones
        new_items = db.query(models.Vocabulary).filter(
            ~models.Vocabulary.id.in_(reviewed_ids)
        ).order_by(func.random()).limit(5 - len(due_items)).all()
        
        due_items.extend(new_items)
    
    return {
        "vocabulary_items": due_items,
        "next_review": current_time + timedelta(days=1)
    }

@router.get("/progress-stats")
async def get_progress_stats(
    response: Response,
    db: Session = Depends(get_db)
):
    # Add cache control headers
    response.headers["Cache-Control"] = "public, max-age=300"  # Cache for 5 minutes
    
    # Use more efficient counting
    total_items = db.query(func.count(models.Vocabulary.id)).scalar()
    reviewed_items = db.query(func.count(func.distinct(models.UserProgress.vocabulary_id))).scalar()
    
    proficiency_levels = db.query(
        models.UserProgress.proficiency_level,
        func.count(models.UserProgress.id)
    ).group_by(
        models.UserProgress.proficiency_level
    ).all()
    
    return {
        "total_items": total_items,
        "reviewed_items": reviewed_items,
        "proficiency_distribution": dict(proficiency_levels)
    }
