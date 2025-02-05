from pydantic import BaseModel
from typing import List, Optional

class Question(BaseModel):
    id: int
    question_text: str
    options: List[str]
    correct_answer: str

class AssessmentSchema(BaseModel):
    id: int
    title: str
    questions: List[Question]

    class Config:
        orm_mode = True