from pydantic import BaseModel
from typing import Optional, List

class Assessment(BaseModel):
    id: Optional[int] = None
    title: str
    description: Optional[str] = None
    language: str
    level: str
