from fastapi import APIRouter, HTTPException
from ..schemas.curriculum import CurriculumSchema, LanguageLevel
from ...services.mock_db import get_curriculum, create_curriculum
from ...services.ai_engine import create_personalized_curriculum

router = APIRouter(prefix="/curriculum", tags=["curriculum"])

@router.post("/", response_model=CurriculumSchema)
def create_new_curriculum(curriculum: CurriculumSchema):
    try:
        # First try to get existing curriculum
        existing = get_curriculum(curriculum.language, curriculum.level)
        if existing:
            return CurriculumSchema(**existing)
        
        # If none exists, create a new one
        created = create_curriculum(curriculum.model_dump())
        return CurriculumSchema(**created)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{language}/{level}", response_model=CurriculumSchema)
def get_curriculum_by_level(language: str, level: str):
    try:
        # Validate level
        level_enum = LanguageLevel(level.lower())
        
        curriculum = get_curriculum(language.lower(), level_enum.value)
        if not curriculum:
            raise HTTPException(status_code=404, detail="Curriculum not found")
        
        return CurriculumSchema(**curriculum)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid level. Must be one of: {[l.value for l in LanguageLevel]}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while fetching the curriculum: {str(e)}"
        )

@router.post("/personalized")
def generate_personalized_curriculum(user_input: str):
    try:
        curriculum = create_personalized_curriculum(user_input)
        return curriculum
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))