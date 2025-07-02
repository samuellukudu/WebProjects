"""
Post-processing module for cleaning and validating organization data.
Implements data enrichment and post-processing for extracted entities.
"""

import pandas as pd
import re
import logging
import json
import requests
import time
from typing import List, Dict, Tuple, Set, Optional, Any
from urllib.parse import urlparse, urljoin
from dataclasses import dataclass
from collections import Counter
from bs4 import BeautifulSoup

from ..core.config import get_config
from ..core.exceptions import ProcessingError, ValidationError


@dataclass
class ProcessingResult:
    """Result of post-processing operation"""
    input_count: int
    output_count: int
    filtered_count: int
    duplicates_removed: int
    validation_results: Dict[str, Any]
    processing_time: float


class DataPostProcessor:
    """Post-processor for cleaning and validating extracted data"""
    
    def __init__(self):
        self.config = get_config()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def process_organizations(self, organizations: List[Any]) -> ProcessingResult:
        """Process a list of organizations with cleaning and validation"""
        start_time = time.time()
        input_count = len(organizations)
        
        self.logger.info(f"Starting post-processing of {input_count} organizations")
        
        try:
            # Step 1: Basic cleaning
            cleaned_orgs = self._clean_organizations(organizations)
            
            # Step 2: Remove duplicates
            deduplicated_orgs = self._remove_duplicates(cleaned_orgs)
            duplicates_removed = len(cleaned_orgs) - len(deduplicated_orgs)
            
            # Step 3: Validate data
            validated_orgs, validation_results = self._validate_organizations(deduplicated_orgs)
            
            # Step 4: Filter by quality thresholds
            filtered_orgs = self._filter_by_quality(validated_orgs)
            filtered_count = len(validated_orgs) - len(filtered_orgs)
            
            processing_time = time.time() - start_time
            
            result = ProcessingResult(
                input_count=input_count,
                output_count=len(filtered_orgs),
                filtered_count=filtered_count,
                duplicates_removed=duplicates_removed,
                validation_results=validation_results,
                processing_time=processing_time
            )
            
            self.logger.info(
                f"Post-processing completed: {input_count} -> {len(filtered_orgs)} "
                f"(removed {duplicates_removed} duplicates, {filtered_count} low-quality) "
                f"in {processing_time:.2f}s"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Post-processing failed: {e}")
            raise ProcessingError(f"Post-processing failed: {e}")
    
    def _clean_organizations(self, organizations: List[Any]) -> List[Any]:
        """Clean organization data"""
        cleaned = []
        
        for org in organizations:
            try:
                # Clean name
                if hasattr(org, 'name') and org.name:
                    org.name = self._clean_text(org.name)
                
                # Clean and validate URL
                if hasattr(org, 'url') and org.url:
                    org.url = self._clean_url(org.url)
                
                # Clean description
                if hasattr(org, 'description') and org.description:
                    org.description = self._clean_text(org.description, max_length=500)
                
                cleaned.append(org)
                
            except Exception as e:
                self.logger.debug(f"Failed to clean organization {getattr(org, 'name', 'Unknown')}: {e}")
        
        return cleaned
    
    def _clean_text(self, text: str, max_length: int = None) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove non-printable characters
        text = ''.join(char for char in text if char.isprintable())
        
        # Apply length limit
        if max_length and len(text) > max_length:
            text = text[:max_length].rsplit(' ', 1)[0] + '...'
        
        return text
    
    def _clean_url(self, url: str) -> str:
        """Clean and validate URL"""
        if not url:
            return ""
        
        # Remove whitespace
        url = url.strip()
        
        # Add scheme if missing
        if url and not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Validate URL format
        try:
            parsed = urlparse(url)
            if parsed.netloc:
                return url
        except Exception:
            pass
        
        return ""
    
    def _remove_duplicates(self, organizations: List[Any]) -> List[Any]:
        """Remove duplicate organizations"""
        if not self.config.extraction.deduplication_enabled:
            return organizations
        
        unique_orgs = []
        seen_names = set()
        seen_urls = set()
        
        for org in organizations:
            # Create keys for comparison
            name_key = getattr(org, 'name', '').lower().strip()
            url_key = getattr(org, 'url', '').lower().strip()
            
            # Check for duplicates
            is_duplicate = False
            
            if name_key and name_key in seen_names:
                is_duplicate = True
            elif url_key and url_key in seen_urls:
                is_duplicate = True
            
            if not is_duplicate:
                unique_orgs.append(org)
                if name_key:
                    seen_names.add(name_key)
                if url_key:
                    seen_urls.add(url_key)
        
        return unique_orgs
    
    def _validate_organizations(self, organizations: List[Any]) -> Tuple[List[Any], Dict[str, Any]]:
        """Validate organizations and return results"""
        validated = []
        validation_stats = {
            'total_checked': len(organizations),
            'valid_names': 0,
            'valid_urls': 0,
            'valid_confidence': 0,
            'validation_errors': []
        }
        
        for org in organizations:
            is_valid = True
            
            # Validate name
            if not getattr(org, 'name', ''):
                validation_stats['validation_errors'].append(f"Empty name for organization")
                is_valid = False
            else:
                validation_stats['valid_names'] += 1
            
            # Validate URL format
            url = getattr(org, 'url', '')
            if url and self._is_valid_url(url):
                validation_stats['valid_urls'] += 1
            elif url:  # URL exists but invalid
                is_valid = False
                validation_stats['validation_errors'].append(f"Invalid URL: {url}")
            
            # Validate confidence score
            confidence = getattr(org, 'confidence_score', 0)
            if isinstance(confidence, (int, float)) and 0 <= confidence <= 1:
                validation_stats['valid_confidence'] += 1
            else:
                is_valid = False
                validation_stats['validation_errors'].append(f"Invalid confidence score: {confidence}")
            
            if is_valid:
                validated.append(org)
        
        return validated, validation_stats
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def _filter_by_quality(self, organizations: List[Any]) -> List[Any]:
        """Filter organizations by quality thresholds"""
        filtered = []
        
        for org in organizations:
            # Check confidence threshold
            confidence = getattr(org, 'confidence_score', 0)
            if confidence < self.config.extraction.confidence_threshold:
                continue
            
            # Check name length (minimum quality check)
            name = getattr(org, 'name', '')
            if len(name) < 3:
                continue
            
            # Check for spam patterns
            if self._is_spam_content(name):
                continue
            
            filtered.append(org)
        
        return filtered
    
    def _is_spam_content(self, text: str) -> bool:
        """Check if content appears to be spam"""
        if not text:
            return True
        
        text_lower = text.lower()
        
        # Check for common spam patterns
        spam_patterns = [
            r'\b(click here|free download|make money|get rich)\b',
            r'\b(viagra|casino|poker|lottery)\b',
            r'^(www\.|http)',
            r'\d{10,}',  # Long number sequences
        ]
        
        for pattern in spam_patterns:
            if re.search(pattern, text_lower):
                return True
        
        # Check for excessive repetition
        words = text_lower.split()
        if len(words) > 1:
            word_counts = Counter(words)
            max_count = max(word_counts.values())
            if max_count > len(words) // 2:  # More than half the words are the same
                return True
        
        return False
    
    def process_verified_companies_with_homepage_validation(self, input_file: str) -> Dict[str, Any]:
        """Process verified companies file (legacy compatibility method)"""
        try:
            # This is a placeholder for the legacy method
            # In a full implementation, this would load the CSV and process it
            self.logger.info(f"Processing verified companies from {input_file}")
            
            return {
                'status': 'completed',
                'message': f'Processed {input_file} (placeholder implementation)',
                'input_file': input_file
            }
            
        except Exception as e:
            self.logger.error(f"Failed to process verified companies: {e}")
            raise ProcessingError(f"Failed to process verified companies: {e}")