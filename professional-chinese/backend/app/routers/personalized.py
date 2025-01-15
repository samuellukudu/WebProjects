from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from ..database import get_db
from .. import models
from sqlalchemy import func
import google.generativeai as genai
from ..config import GEMINI_API_KEY

router = APIRouter()

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

class LearningGoalCreate(BaseModel):
    prompt: str

class LearningGoalResponse(BaseModel):
    id: int
    prompt: str
    target_level: int
    focus_categories: List[str]
    created_at: datetime

    class Config:
        from_attributes = True

@router.post("/goals", response_model=LearningGoalResponse)
async def create_learning_goal(
    goal: LearningGoalCreate,
    db: Session = Depends(get_db)
):
    try:
        prompt = f"""Analyze this Chinese learning goal and determine:
        1. Appropriate focus categories (business, email, meetings, etc.)
        2. Target HSK/proficiency level (1-5)
        
        Goal: {goal.prompt}
        
        Return your analysis in this format:
        {{"categories": [...], "target_level": X}}"""

        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.3,
                max_output_tokens=1024,
            )
        )
        
        analysis = eval(response.text)
        
        db_goal = models.LearningGoal(
            prompt=goal.prompt,
            target_level=analysis['target_level'],
            focus_categories=analysis['categories']
        )
        db.add(db_goal)
        db.commit()
        db.refresh(db_goal)
        
        # Generate initial personalized lesson
        await generate_personalized_lesson(db_goal.id, db)
        
        return db_goal
    except Exception as e:
        logger.error(f"Error creating learning goal: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create learning goal: {str(e)}"
        )

@router.get("/lessons/next")
async def get_next_lesson(db: Session = Depends(get_db)):
    # Get the most recent uncompleted lesson
    lesson = db.query(models.PersonalizedLesson).filter(
        models.PersonalizedLesson.completed == False
    ).order_by(
        models.PersonalizedLesson.created_at.desc()
    ).first()
    
    if not lesson:
        raise HTTPException(status_code=404, detail="No lessons available")
    
    # Get vocabulary items for the lesson
    vocabulary = db.query(models.Vocabulary).filter(
        models.Vocabulary.id.in_(lesson.vocabulary_ids)
    ).all()
    
    return {
        "lesson_id": lesson.id,
        "vocabulary": vocabulary,
        "difficulty_level": lesson.difficulty_level,
        "focus_category": lesson.focus_category
    }

async def generate_personalized_lesson(goal_id: int, db: Session):
    goal = db.query(models.LearningGoal).filter(
        models.LearningGoal.id == goal_id
    ).first()
    
    if not goal:
        raise HTTPException(status_code=404, detail="Learning goal not found")
    
    # Get user's current level
    avg_proficiency = db.query(
        func.avg(models.UserProgress.proficiency_level)
    ).scalar() or 0
    current_level = min(5, int(avg_proficiency) + 1)
    
    # Select vocabulary items based on categories and difficulty
    vocabulary = db.query(models.Vocabulary).filter(
        models.Vocabulary.context_category.in_(goal.focus_categories),
        models.Vocabulary.difficulty_level <= current_level + 1
    ).order_by(func.random()).limit(5).all()
    
    lesson = models.PersonalizedLesson(
        goal_id=goal_id,
        vocabulary_ids=[v.id for v in vocabulary],
        difficulty_level=current_level,
        focus_category=goal.focus_categories[0]  # Primary focus category
    )
    
    db.add(lesson)
    db.commit() 