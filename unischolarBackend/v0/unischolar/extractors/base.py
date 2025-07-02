"""
Base extractor class for UniScholar platform.

Provides common functionality and interface for all extractors.
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

from ..core.models import QueryIntent
from ..core.config import get_config
from ..core.exceptions import ExtractionError


class BaseExtractor(ABC):
    """Base class for all data extractors"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = get_config()
        self.custom_config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
    @abstractmethod
    def extract(self, html_content: str, source_url: str, **kwargs) -> List[Any]:
        """Extract entities from HTML content"""
        pass
    
    def preprocess_html(self, html_content: str) -> BeautifulSoup:
        """Preprocess HTML content before extraction"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'aside']):
                element.decompose()
            
            return soup
        except Exception as e:
            raise ExtractionError(f"Failed to parse HTML: {e}")
    
    def clean_text(self, text: str, max_length: Optional[int] = None) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Apply length limit
        if max_length and len(text) > max_length:
            text = text[:max_length].rsplit(' ', 1)[0] + '...'
        
        return text.strip()
    
    def extract_url_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except Exception:
            return ""
    
    def is_valid_url(self, url: str) -> bool:
        """Check if URL is valid"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def normalize_url(self, url: str, base_url: str) -> str:
        """Normalize and resolve relative URLs"""
        try:
            if not url:
                return ""
            
            # Handle relative URLs
            if not url.startswith(('http://', 'https://')):
                url = urljoin(base_url, url)
            
            return url.strip()
        except Exception:
            return url
    
    def extract_structured_data(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract JSON-LD structured data"""
        structured_data = []
        
        # Find JSON-LD scripts
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                import json
                data = json.loads(script.string)
                if isinstance(data, list):
                    structured_data.extend(data)
                else:
                    structured_data.append(data)
            except Exception as e:
                self.logger.debug(f"Failed to parse JSON-LD: {e}")
        
        return structured_data
    
    def extract_meta_data(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract meta data from HTML head"""
        meta_data = {}
        
        # Extract title
        title = soup.find('title')
        if title:
            meta_data['title'] = self.clean_text(title.get_text())
        
        # Extract meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            
            if name and content:
                meta_data[name.lower()] = self.clean_text(content)
        
        return meta_data
    
    def calculate_confidence_score(self, indicators: Dict[str, int], 
                                 weights: Dict[str, float]) -> float:
        """Calculate confidence score based on indicators and weights"""
        total_score = 0.0
        total_weight = 0.0
        
        for indicator, count in indicators.items():
            weight = weights.get(indicator, 0.0)
            total_score += min(count, 3) * weight  # Cap individual contributions
            total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        # Normalize to 0-1 range
        normalized_score = total_score / total_weight
        return min(normalized_score, 1.0)
    
    def filter_by_confidence(self, entities: List[Any], 
                           min_confidence: Optional[float] = None) -> List[Any]:
        """Filter entities by confidence threshold"""
        if min_confidence is None:
            min_confidence = self.config.extraction.confidence_threshold
        
        return [entity for entity in entities 
                if hasattr(entity, 'confidence_score') and 
                entity.confidence_score >= min_confidence]
    
    def deduplicate_entities(self, entities: List[Any]) -> List[Any]:
        """Remove duplicate entities based on name/URL similarity"""
        if not entities or not self.config.extraction.deduplication_enabled:
            return entities
        
        unique_entities = []
        seen_names = set()
        seen_urls = set()
        
        for entity in entities:
            name_key = getattr(entity, 'name', '').lower().strip()
            url_key = getattr(entity, 'url', '').lower().strip()
            
            # Skip if we've seen similar name or URL
            if name_key in seen_names or url_key in seen_urls:
                continue
            
            unique_entities.append(entity)
            if name_key:
                seen_names.add(name_key)
            if url_key:
                seen_urls.add(url_key)
        
        return unique_entities
    
    def log_extraction_stats(self, entities: List[Any], source_url: str):
        """Log extraction statistics"""
        if entities:
            avg_confidence = sum(getattr(e, 'confidence_score', 0) for e in entities) / len(entities)
            self.logger.info(
                f"Extracted {len(entities)} entities from {source_url} "
                f"(avg confidence: {avg_confidence:.2f})"
            )
        else:
            self.logger.debug(f"No entities extracted from {source_url}")


class EntityExtractor(BaseExtractor):
    """Base class for specific entity extractors"""
    
    def __init__(self, entity_type: str, config: Optional[Dict] = None):
        super().__init__(config)
        self.entity_type = entity_type
        
    def extract_with_intent(self, html_content: str, source_url: str, 
                          query_intent: Optional[QueryIntent] = None) -> List[Any]:
        """Extract entities with query intent context"""
        entities = self.extract(html_content, source_url)
        
        if query_intent:
            # Apply intent-based filtering and scoring
            entities = self.apply_intent_filtering(entities, query_intent)
            entities = self.apply_intent_scoring(entities, query_intent)
        
        return entities
    
    def apply_intent_filtering(self, entities: List[Any], 
                             query_intent: QueryIntent) -> List[Any]:
        """Filter entities based on query intent"""
        # Default implementation - can be overridden
        return entities
    
    def apply_intent_scoring(self, entities: List[Any], 
                           query_intent: QueryIntent) -> List[Any]:
        """Apply intent-based scoring to entities"""
        # Default implementation - can be overridden
        return entities 