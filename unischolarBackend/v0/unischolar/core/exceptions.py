"""
Custom exceptions for UniScholar platform.

Provides specific exception types for different error scenarios.
"""


class UniScholarException(Exception):
    """Base exception for all UniScholar-related errors"""
    pass


class ConfigurationError(UniScholarException):
    """Raised when there's a configuration-related error"""
    pass


class ExtractionError(UniScholarException):
    """Raised when data extraction fails"""
    pass


class ValidationError(UniScholarException):
    """Raised when data validation fails"""
    pass


class CrawlerError(UniScholarException):
    """Raised when crawling operations fail"""
    pass


class ProcessingError(UniScholarException):
    """Raised when post-processing operations fail"""
    pass


class NetworkError(UniScholarException):
    """Raised when network operations fail"""
    pass


class ParsingError(UniScholarException):
    """Raised when HTML/content parsing fails"""
    pass


class DuplicateEntityError(UniScholarException):
    """Raised when duplicate entities are detected"""
    pass


class InvalidURLError(UniScholarException):
    """Raised when an invalid URL is encountered"""
    pass


class TimeoutError(UniScholarException):
    """Raised when operations timeout"""
    pass


class RateLimitError(UniScholarException):
    """Raised when rate limits are exceeded"""
    pass 