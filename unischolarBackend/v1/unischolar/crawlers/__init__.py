"""
Web crawling modules for UniScholar platform.

Contains various crawlers for different types of web sources
and content discovery strategies.
"""

from .base import BaseCrawler
from .academic import AcademicWebCrawler

__all__ = [
    "BaseCrawler",
    "AcademicWebCrawler"
] 