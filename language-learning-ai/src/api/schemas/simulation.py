from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from enum import Enum

class ScenarioType(str, Enum):
    HEALTHCARE = "healthcare_consultation"
    BUSINESS = "business_meeting"
    SALES = "sales_pitch"
    CUSTOMER_SERVICE = "customer_service"
    GENERAL = "general_conversation"

class SimulationResponse(BaseModel):
    text: str
    confidence_score: float
    pronunciation_feedback: Optional[Dict[str, str]]
    grammar_feedback: Optional[Dict[str, str]]

class SimulationPrompt(BaseModel):
    context: str
    options: List[str]
    correct_response: str
    feedback: Dict[str, str]

class SimulationScenario(BaseModel):
    scenario_type: ScenarioType
    industry: str
    difficulty_level: str
    context: str
    prompts: List[SimulationPrompt]
    vocabulary: List[Dict[str, str]]
    learning_objectives: List[str]
