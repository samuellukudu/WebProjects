"""
Base crawler class for UniScholar platform.

Provides common crawling functionality that can be extended by specialized crawlers.
"""

import logging
import time
import requests
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser

from ..core.exceptions import CrawlerError

class BaseCrawler(ABC):
    """Base class for all crawlers in the UniScholar platform"""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize base crawler with configuration"""
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Default configuration
        self.request_delay = self.config.get('request_delay', 1.0)
        self.max_retries = self.config.get('max_retries', 3)
        self.session_timeout = self.config.get('session_timeout', 30)
        self.max_concurrent = self.config.get('max_concurrent', 5)
        self.robots_respect = self.config.get('robots_respect', True)
        
        # Session setup
        self.session = requests.Session()
        self.session.timeout = self.session_timeout
        
        # Robot parser cache
        self.robot_parsers = {}
    
    @abstractmethod
    def crawl(self, *args, **kwargs):
        """Main crawling method - must be implemented by subclasses"""
        pass
    
    def can_fetch(self, url: str, user_agent: str = '*') -> bool:
        """Check if URL can be fetched according to robots.txt"""
        if not self.robots_respect:
            return True
            
        parsed_uri = urlparse(url)
        domain = f"{parsed_uri.scheme}://{parsed_uri.netloc}"
        
        if domain not in self.robot_parsers:
            rp = RobotFileParser()
            rp.set_url(urljoin(domain, 'robots.txt'))
            try:
                rp.read()
                self.robot_parsers[domain] = rp
            except Exception as e:
                self.logger.debug(f"Could not read robots.txt for {domain}: {e}")
                self.robot_parsers[domain] = None
        
        rp = self.robot_parsers.get(domain)
        return rp is None or rp.can_fetch(user_agent, url)
    
    def rate_limit(self, url: str):
        """Apply rate limiting between requests"""
        if self.request_delay > 0:
            time.sleep(self.request_delay)
    
    def get_domain(self, url: str) -> str:
        """Extract domain from URL"""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"
    
    def is_valid_url(self, url: str) -> bool:
        """Check if URL is valid"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def cleanup(self):
        """Cleanup resources"""
        if hasattr(self, 'session'):
            self.session.close() 