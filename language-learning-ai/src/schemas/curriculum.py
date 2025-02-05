from pydantic import BaseModel
from typing import List, Optional

class CurriculumItem(BaseModel):
    title: str
    content: str

class CurriculumSchema(BaseModel):
    id: Optional[int]
    title: str
    items: List[CurriculumItem]