"""
Utility modules for UniScholar platform.

Contains shared utilities for web operations, text processing, and file I/O.
"""

from .web_utils import WebUtils
from .text_utils import TextUtils
from .file_utils import FileUtils

__all__ = [
    "WebUtils",
    "TextUtils",
    "FileUtils"
] 