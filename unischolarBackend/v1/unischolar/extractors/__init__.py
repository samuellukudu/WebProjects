"""
Data extraction modules for UniScholar platform.

Contains various extractors for different types of educational entities
and content from web sources.
"""

from .base import BaseExtractor

# Import with error handling due to potential dependency issues
try:
    from .dynamic_ner import DynamicNERExtractor
except ImportError:
    DynamicNERExtractor = None

try:
    from .search_ner import SearchNERProcessor, EducationalEntities, ExtractedEntity
except ImportError:
    SearchNERProcessor = None
    EducationalEntities = None
    ExtractedEntity = None

try:
    from .educational_extractor import EducationalExtractor
except ImportError:
    EducationalExtractor = None

try:
    from .university_name_extractor import UniversityNameExtractor, UniversityName
except ImportError:
    UniversityNameExtractor = None
    UniversityName = None

# DynamicNERExtractor is imported directly in main.py with error handling
# due to spaCy dependency issues in some environments
EducationalPipeline = None

# Placeholder for future modules
OrganizationExtractor = None
IntentAnalyzer = None

__all__ = [
    'EntityExtractor',
    'DynamicNERExtractor', 
    'SearchNERProcessor',
    'EducationalEntities',
    'ExtractedEntity',
    'EducationalExtractor',
    'UniversityNameExtractor',
    'UniversityName'
]

# Add available modules to exports
if DynamicNERExtractor is not None:
    __all__.append("DynamicNERExtractor")
if SearchNERProcessor is not None:
    __all__.append("SearchNERProcessor")
if EducationalExtractor is not None:
    __all__.append("EducationalExtractor")
if EducationalPipeline is not None:
    __all__.append("EducationalPipeline")
if OrganizationExtractor is not None:
    __all__.append("OrganizationExtractor")
if IntentAnalyzer is not None:
    __all__.append("IntentAnalyzer") 