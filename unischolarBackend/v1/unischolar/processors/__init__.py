"""
Data processing modules for UniScholar platform.

Contains post-processors, validators, and enrichers for extracted data.
"""

# Optional imports that may fail due to dependencies
try:
    from .post_processor import DataPostProcessor
except ImportError:
    DataPostProcessor = None

# Placeholder for future modules
BaseProcessor = None
DataValidator = None
DataEnricher = None

__all__ = []

# Add available modules to exports
if BaseProcessor is not None:
    __all__.append("BaseProcessor")
if DataPostProcessor is not None:
    __all__.append("DataPostProcessor")
if DataValidator is not None:
    __all__.append("DataValidator")
if DataEnricher is not None:
    __all__.append("DataEnricher") 