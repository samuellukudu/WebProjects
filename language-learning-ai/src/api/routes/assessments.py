from fastapi import APIRouter, HTTPException
from typing import List
from ..schemas.assessment import AssessmentSchema
from ...services.ai_engine import AIService
from ...services.mock_db import get_assessment as get_assessment_from_db, get_level_requirements

router = APIRouter(prefix="/assessments", tags=["assessments"])

# In-memory storage for assessments (for demonstration purposes)
assessments_db = []

@router.post("/", response_model=AssessmentSchema)
def create_assessment(assessment: AssessmentSchema):
    assessment_dict = assessment.model_dump()
    assessment_dict['id'] = len(assessments_db) + 1
    new_assessment = AssessmentSchema(**assessment_dict)
    assessments_db.append(new_assessment)
    return new_assessment

@router.get("/", response_model=List[AssessmentSchema])
async def get_assessments():
    return assessments_db

@router.get("/{assessment_id}", response_model=AssessmentSchema)
def get_assessment_by_id(assessment_id: int):  # Renamed this function
    for assessment in assessments_db:
        if assessment.id == assessment_id:
            return assessment
    raise HTTPException(status_code=404, detail="Assessment not found")

@router.delete("/{assessment_id}", response_model=AssessmentSchema)
def delete_assessment(assessment_id: int):
    for index, assessment in enumerate(assessments_db):
        if assessment.id == assessment_id:
            return assessments_db.pop(index)
    raise HTTPException(status_code=404, detail="Assessment not found")

@router.post("/generate")
def generate_assessment(language: str, level: str):
    try:
        # First check if we have a pre-made assessment
        assessment = get_assessment_from_db(language, level)
        if assessment:
            return {"content": assessment}
            
        # If no pre-made assessment, generate one using AI
        assessment_content = AIService.generate_assessment(language, level)
        return {"content": assessment_content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/requirements/{level}")
async def get_requirements(level: str):
    requirements = get_level_requirements(level)
    if not requirements:
        raise HTTPException(status_code=404, detail="Level not found")
    return requirements

@router.post("/evaluate")
def evaluate_response(question: str, user_response: str, language: str):
    try:
        evaluation = AIService.evaluate_response(question, user_response, language)
        return {"evaluation": evaluation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))