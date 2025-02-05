from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class ResourceType(str, Enum):
    VIDEO = "video"
    ARTICLE = "article"
    EXERCISE = "exercise"
    QUIZ = "quiz"

class LanguageLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class ResourceItem(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    type: ResourceType
    url: Optional[str] = Field(None, pattern="^https?://.*")
    description: Optional[str] = Field(None, max_length=500)

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Present Simple Tutorial",
                "type": "video",
                "url": "https://example.com/video",
                "description": "Learn the basics of present simple tense"
            }
        }

class TopicItem(BaseModel):
    topic: str = Field(..., min_length=1, max_length=100)
    resources: List[ResourceItem]
    duration: Optional[str] = Field(None, pattern="^[0-9]+ (day|week|month)s?$")

    class Config:
        json_schema_extra = {
            "example": {
                "topic": "Basic Grammar",
                "resources": [{
                    "title": "Present Simple Tutorial",
                    "type": "video",
                    "url": "https://example.com/video",
                    "description": "Learn the basics of present simple tense"
                }],
                "duration": "1 week"
            }
        }

class CurriculumSchema(BaseModel):
    user_id: Optional[int] = None
    language: str = Field(..., min_length=1, max_length=50)
    level: LanguageLevel
    topics: List[TopicItem] = Field(..., min_items=1)
    learning_style: Optional[str] = Field(None, pattern="^(visual|auditory|reading|kinesthetic)$")

    class Config:
        json_schema_extra = {
            "example": {
                "language": "english",
                "level": "beginner",
                "topics": [{
                    "topic": "Basic Grammar",
                    "resources": [{
                        "title": "Present Simple Tutorial",
                        "type": "video",
                        "url": "https://example.com/video",
                        "description": "Learn the basics of present simple tense"
                    }],
                    "duration": "1 week"
                }],
                "learning_style": "visual"
            }
        }
