from fastapi import APIRouter, HTTPException
from ..schemas.onboarding import (
    OnboardingSchema, LearningGoal, LanguageStruggle,
    LearningStyle, Industry
)
from ...services.ai_engine import analyze_user_preferences

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

@router.post("/")
def create_user_profile(onboarding_data: OnboardingSchema):
    try:
        # Analyze user preferences and generate recommendations
        analysis = analyze_user_preferences(onboarding_data.model_dump())
        return {
            "profile": onboarding_data,
            "recommendations": analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/options")
def get_onboarding_options():
    return {
        "learning_goals": [goal.value for goal in LearningGoal],
        "struggles": [struggle.value for struggle in LanguageStruggle],
        "learning_styles": [style.value for style in LearningStyle],
        "industries": [industry.value for industry in Industry]
    }
