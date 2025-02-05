
from pydantic import BaseModel
from typing import Optional

class AssessmentSchema(BaseModel):
    id: Optional[int] = None
    title: str
    description: Optional[str] = None
    language: str
    level: str