from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class LearningGoal(str, Enum):
    WORK = "work"
    SOCIAL = "social"
    SPECIALIZED = "specialized"
    TRAVEL = "travel"
    OTHER = "other"

class LanguageStruggle(str, Enum):
    PRONUNCIATION = "pronunciation"
    GRAMMAR = "grammar"
    VOCABULARY = "vocabulary"
    LISTENING = "listening"
    SPEAKING = "speaking"
    WRITING = "writing"

class LearningStyle(str, Enum):
    TEXT = "text"
    AUDIO = "audio"
    ROLEPLAY = "roleplay"
    VISUAL = "visual"

class Industry(str, Enum):
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    TECHNOLOGY = "technology"
    SALES = "sales"
    LEGAL = "legal"
    OTHER = "other"

class OnboardingSchema(BaseModel):
    user_id: int
    learning_goal: LearningGoal
    custom_goal: Optional[str] = Field(None, max_length=500)
    struggles: List[LanguageStruggle]
    custom_struggle: Optional[str] = Field(None, max_length=500)
    proficiency_level: str
    learning_style: List[LearningStyle]
    industry: Industry
    custom_industry: Optional[str] = Field(None, max_length=100)
    language: str = Field(..., min_length=1, max_length=50)

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "learning_goal": "work",
                "custom_goal": "I need to communicate with international clients",
                "struggles": ["speaking", "writing"],
                "custom_struggle": "Business email writing",
                "proficiency_level": "intermediate",
                "learning_style": ["visual", "audio"],
                "industry": "technology",
                "language": "english"
            }
        }
