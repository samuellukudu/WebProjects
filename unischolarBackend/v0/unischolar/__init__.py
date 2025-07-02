"""
UniScholar - Comprehensive Student Educational Dataset Platform

A robust system for extracting, processing, and managing educational data including
universities, scholarships, academic programs, student events, and funding opportunities.
"""

__version__ = "1.0.0"
__author__ = "UniScholar Team"
__description__ = "Comprehensive Student Educational Dataset Platform"

# Core imports for easy access
from .core.models import (
    University,
    Scholarship, 
    AcademicProgram,
    StudentEvent,
    Funding,
    Organization,
    GeneralContent,
    QueryIntent
)

from .core.config import Config

# Note: DynamicNERExtractor and DataPostProcessor are imported 
# in main.py with proper error handling due to spaCy dependencies

__all__ = [
    "University",
    "Scholarship", 
    "AcademicProgram",
    "StudentEvent", 
    "Funding",
    "Organization",
    "GeneralContent",
    "QueryIntent",
    "Config"
] 