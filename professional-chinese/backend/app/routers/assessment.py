from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.utils.logger import logger
from app.utils.model import model
import json

router = APIRouter()

@router.post("/quiz/generate")
async def generate_quiz(
    week_number: int,
    curriculum_id: int,
    db: Session = Depends(get_db)
):
    try:
        curriculum = db.query(models.Curriculum).filter(
            models.Curriculum.id == curriculum_id
        ).first()
        
        if not curriculum:
            raise HTTPException(status_code=404, detail="Curriculum not found")
            
        week_data = curriculum.content["weekly_plan"][week_number - 1]
        
        # Generate quiz using language model
        prompt = f"""Create a quiz based on:
        Focus: {week_data['focus']}
        Vocabulary: {', '.join(week_data['vocabulary_focus'])}
        Grammar: {', '.join(week_data['grammar_points'])}
        
        Generate 5 questions with the following format:
        {{
            "questions": [
                {{
                    "type": "multiple_choice",
                    "question": "Question text",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": "Correct option",
                    "explanation": "Why this is correct"
                }}
            ]
        }}"""
        
        response = model.generate_content(prompt)
        quiz_data = json.loads(response.text)
        
        return quiz_data
        
    except Exception as e:
        logger.error(f"Error generating quiz: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate quiz: {str(e)}"
        )