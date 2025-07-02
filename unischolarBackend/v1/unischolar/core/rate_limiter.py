"""
Rate limiting utilities for UniScholar platform.

This module provides rate limiting functionality to ensure respectful crawling
and avoid overwhelming target servers.
"""

import time
import threading
from typing import Dict, Optional, Any
from dataclasses import dataclass
import logging


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    min_interval: float = 1.0  # Minimum seconds between requests
    max_retries: int = 3      # Maximum retry attempts
    backoff_factor: float = 2.0  # Exponential backoff multiplier
    max_delay: float = 60.0   # Maximum delay in seconds


class RateLimiter:
    """
    Thread-safe rate limiter for web crawling operations.
    
    Supports:
    - Per-domain rate limiting
    - Global rate limiting
    - Exponential backoff
    - Thread-safe operations
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the rate limiter with configuration"""
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Global rate limiting
        self._last_request_time = 0
        self._global_lock = threading.Lock()
        
        # Per-domain rate limiting
        self._domain_last_times: Dict[str, float] = {}
        self._domain_locks: Dict[str, threading.Lock] = {}
        self._domain_lock = threading.Lock()
        
        # Configuration
        rate_config = self.config.get('rate_limiting', {})
        self.rate_config = RateLimitConfig(
            min_interval=rate_config.get('min_interval', 1.0),
            max_retries=rate_config.get('max_retries', 3),
            backoff_factor=rate_config.get('backoff_factor', 2.0),
            max_delay=rate_config.get('max_delay', 60.0)
        )
        
        # Search-specific rate limiting
        search_config = self.config.get('search_rate_limiting', {})
        self.search_min_interval = search_config.get('min_search_interval', 3.0)
        self._last_search_time = 0
        self._search_lock = threading.Lock()
    
    def wait_if_needed(self, domain: Optional[str] = None) -> None:
        """
        Wait if necessary to respect rate limits.
        
        Args:
            domain: Optional domain for per-domain rate limiting
        """
        if domain:
            self._wait_for_domain(domain)
        else:
            self._wait_global()
    
    def _wait_global(self) -> None:
        """Apply global rate limiting"""
        with self._global_lock:
            current_time = time.time()
            time_since_last = current_time - self._last_request_time
            
            if time_since_last < self.rate_config.min_interval:
                sleep_time = self.rate_config.min_interval - time_since_last
                self.logger.debug(f"Global rate limit: waiting {sleep_time:.2f}s")
                time.sleep(sleep_time)
            
            self._last_request_time = time.time()
    
    def _wait_for_domain(self, domain: str) -> None:
        """Apply per-domain rate limiting"""
        # Get or create domain lock
        with self._domain_lock:
            if domain not in self._domain_locks:
                self._domain_locks[domain] = threading.Lock()
                self._domain_last_times[domain] = 0
            domain_lock = self._domain_locks[domain]
        
        # Apply domain-specific rate limiting
        with domain_lock:
            current_time = time.time()
            last_time = self._domain_last_times[domain]
            time_since_last = current_time - last_time
            
            if time_since_last < self.rate_config.min_interval:
                sleep_time = self.rate_config.min_interval - time_since_last
                self.logger.debug(f"Domain {domain} rate limit: waiting {sleep_time:.2f}s")
                time.sleep(sleep_time)
            
            self._domain_last_times[domain] = time.time()
    
    def wait_for_search(self) -> None:
        """Apply search-specific rate limiting"""
        with self._search_lock:
            current_time = time.time()
            time_since_last = current_time - self._last_search_time
            
            if time_since_last < self.search_min_interval:
                sleep_time = self.search_min_interval - time_since_last
                self.logger.info(f"Search rate limit: waiting {sleep_time:.1f}s")
                time.sleep(sleep_time)
            
            self._last_search_time = time.time()
    
    def get_retry_delay(self, attempt: int) -> float:
        """
        Calculate retry delay using exponential backoff.
        
        Args:
            attempt: Current attempt number (0-based)
            
        Returns:
            Delay in seconds
        """
        if attempt == 0:
            return 0
        
        delay = self.rate_config.min_interval * (self.rate_config.backoff_factor ** (attempt - 1))
        return min(delay, self.rate_config.max_delay)
    
    def should_retry(self, attempt: int) -> bool:
        """
        Check if should retry based on attempt count.
        
        Args:
            attempt: Current attempt number (0-based)
            
        Returns:
            True if should retry, False otherwise
        """
        return attempt < self.rate_config.max_retries
    
    def reset_domain(self, domain: str) -> None:
        """Reset rate limiting for a specific domain"""
        with self._domain_lock:
            if domain in self._domain_last_times:
                self._domain_last_times[domain] = 0
                self.logger.debug(f"Reset rate limiting for domain: {domain}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current rate limiter status"""
        current_time = time.time()
        
        return {
            'global_last_request': self._last_request_time,
            'global_time_since_last': current_time - self._last_request_time,
            'search_last_request': self._last_search_time,
            'search_time_since_last': current_time - self._last_search_time,
            'tracked_domains': len(self._domain_last_times),
            'config': {
                'min_interval': self.rate_config.min_interval,
                'search_min_interval': self.search_min_interval,
                'max_retries': self.rate_config.max_retries,
                'backoff_factor': self.rate_config.backoff_factor,
                'max_delay': self.rate_config.max_delay
            }
        } 