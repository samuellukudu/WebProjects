"""
Data extraction modules for UniScholar platform.

Contains various extractors for different types of educational entities
and content from web sources.
"""

from .base import BaseExtractor

# DynamicNERExtractor is imported directly in main.py with error handling
# due to spaCy dependency issues in some environments
DynamicNERExtractor = None

# Placeholder for future modules
OrganizationExtractor = None
IntentAnalyzer = None

__all__ = ["BaseExtractor"]

# Add available modules to exports
if DynamicNERExtractor is not None:
    __all__.append("DynamicNERExtractor")
if OrganizationExtractor is not None:
    __all__.append("OrganizationExtractor")
if IntentAnalyzer is not None:
    __all__.append("IntentAnalyzer") 