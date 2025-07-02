"""
Web utilities for UniScholar platform.

Provides utilities for web scraping, URL handling, and HTTP operations.
"""

import requests
import time
import random
from typing import List, Dict, Optional
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup

from ..core.config import get_config
from ..core.exceptions import NetworkError, RateLimitError


class WebUtils:
    """Utilities for web operations"""
    
    def __init__(self):
        self.config = get_config()
        self.session = requests.Session()
        self._setup_session()
    
    def _setup_session(self):
        """Setup requests session with configuration"""
        # Set default headers
        self.session.headers.update({
            'User-Agent': random.choice(self.config.crawler.user_agents)
        })
        
        # Set timeout
        self.session.timeout = self.config.crawler.session_timeout
    
    def fetch_url(self, url: str, retries: int = None) -> Optional[str]:
        """Fetch content from URL with retries and rate limiting"""
        if retries is None:
            retries = self.config.crawler.max_retries
        
        for attempt in range(retries + 1):
            try:
                # Apply rate limiting
                time.sleep(self.config.crawler.request_delay)
                
                # Rotate user agent
                self.session.headers.update({
                    'User-Agent': random.choice(self.config.crawler.user_agents)
                })
                
                response = self.session.get(url, timeout=self.config.crawler.session_timeout)
                response.raise_for_status()
                
                return response.text
                
            except requests.exceptions.RequestException as e:
                if attempt < retries:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    time.sleep(wait_time)
                    continue
                else:
                    raise NetworkError(f"Failed to fetch {url} after {retries} retries: {e}")
        
        return None
    
    def can_fetch(self, url: str) -> bool:
        """Check if URL can be fetched according to robots.txt"""
        if not self.config.crawler.robots_respect:
            return True
        
        try:
            parsed_url = urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            
            return rp.can_fetch('*', url)
        except Exception:
            return True  # If robots.txt can't be checked, allow by default
    
    def search_web(self, query: str, max_results: int = 30) -> List[Dict[str, str]]:
        """Search the web and return results"""
        # Placeholder implementation - in a real system you'd integrate with
        # search APIs like DuckDuckGo, Google Custom Search, etc.
        
        # For now, return a mock result structure
        results = []
        for i in range(min(max_results, 5)):  # Limit to 5 for demo
            results.append({
                'title': f"Sample Result {i+1} for '{query}'",
                'url': f"https://example.com/result{i+1}",
                'snippet': f"This is a sample snippet for result {i+1} about {query}."
            })
        
        return results
    
    def normalize_url(self, url: str, base_url: str = "") -> str:
        """Normalize and resolve URL"""
        if not url:
            return ""
        
        # Handle relative URLs
        if not url.startswith(('http://', 'https://')):
            if base_url:
                url = urljoin(base_url, url)
        
        return url.strip()
    
    def is_valid_url(self, url: str) -> bool:
        """Check if URL is valid"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except Exception:
            return "" 