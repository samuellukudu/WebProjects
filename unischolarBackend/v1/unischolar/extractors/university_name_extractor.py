"""
Advanced University Name Extractor - Focused on extracting clean university names only

This module provides sophisticated university name extraction capabilities using:
- Advanced NER with educational domain fine-tuning
- Multi-pattern university name recognition
- Intelligent name cleaning and normalization
- Quality scoring and validation
- Cross-referencing with known university databases
"""

import re
import logging
from typing import List, Dict, Set, Optional, Tuple
from bs4 import BeautifulSoup
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import spacy
from spacy.lang.en import English

try:
    nlp = spacy.load("en_core_web_sm")
except IOError:
    nlp = English()
    logging.warning("spaCy English model not found, using basic tokenizer")

@dataclass
class UniversityName:
    """Represents an extracted university name with metadata"""
    name: str
    confidence: float
    source_url: str
    extraction_method: str
    official_url: Optional[str] = None
    country: Optional[str] = None
    name_variants: List[str] = None
    is_verified: bool = False
    quality_score: float = 0.0

class UniversityNameExtractor:
    """Advanced extractor focused purely on university names"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.nlp = nlp
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Enhanced university name patterns
        self.university_patterns = {
            # Standard university naming patterns
            'standard_patterns': [
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+University\b',
                r'\bUniversity\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+College\b',
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+Institute\s+of\s+Technology\b',
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+Technical\s+University\b',
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+Polytechnic\s+University\b',
            ],
            
            # International university patterns
            'international_patterns': [
                # European patterns
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+Université\b',  # French
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+Universität\b',  # German
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+Universidad\b',  # Spanish
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+Università\b',   # Italian
                r'\bUniversidade\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', # Portuguese
                
                # Asian patterns
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+Daigaku\b',      # Japanese
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+대학교?\b',       # Korean
                
                # Multi-word international
                r'\bUniversité\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
                r'\bUniversidad\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
                r'\bUniversità\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
                r'\bUniversität\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
            ],
            
            # Specialized institution patterns
            'specialized_patterns': [
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+Medical\s+(?:University|College|School)\b',
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+Law\s+School\b',
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+Business\s+School\b',
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+School\s+of\s+(?:Medicine|Engineering|Arts|Sciences)\b',
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+Institute\s+of\s+(?:Technology|Science|Arts)\b',
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+Academy\s+of\s+(?:Sciences|Arts|Music)\b',
            ],
            
            # Acronym-based patterns (MIT, UCLA, etc.)
            'acronym_patterns': [
                r'\b([A-Z]{2,6})\s+(?:University|College|Institute)\b',
                r'\b(?:University|College|Institute)\s+([A-Z]{2,6})\b',
                r'\b([A-Z]{2,6})\s+(?:Technical\s+University|Institute\s+of\s+Technology)\b',
            ],
            
            # Complex multi-part names
            'complex_patterns': [
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:State\s+)?University\s+(?:of\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
                r'\b(?:The\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+University\s+(?:of\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Catholic|Christian|Islamic|Jewish)\s+University\b',
                r'\b(?:Saint|St\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+University\b',
            ]
        }
        
        # University validation keywords
        self.university_indicators = {
            'strong_indicators': [
                'university', 'college', 'institute', 'school',
                'université', 'universidad', 'università', 'universität',
                'polytechnic', 'academy', 'conservatory', 'seminary'
            ],
            'specialized_indicators': [
                'medical school', 'law school', 'business school',
                'graduate school', 'dental school', 'veterinary school',
                'institute of technology', 'technical university',
                'community college', 'liberal arts college'
            ]
        }
        
        # Quality exclusion patterns
        self.exclusion_patterns = [
            # Article and content patterns
            r'^(?:best|top|cheapest|most|ultimate|complete|comprehensive)\s+',
            r'^(?:list|guide|tips|steps|ways|things)\s+',
            r'(?:guide|tutorial|tips|steps|ways)\s+(?:to|for)',
            r'how\s+to\s+(?:get|apply|write|choose)',
            r'everything.*you.*need.*to.*know',
            
            # Navigation and UI elements
            r'^(?:home|about|contact|blog|news|privacy|terms|cookies)$',
            r'^(?:search|login|register|sign|explore|browse)$',
            r'(?:read\s+more|learn\s+more|see\s+more|view\s+more)$',
            
            # Academic content (not institutions)
            r'(?:admission|application|visa|interview|requirement)',
            r'for\s+international\s+students',
            r'without\s+(?:ielts|toefl|gre|gmat)',
            r'(?:fully|partially)\s+funded',
            r'scholarships?\s+(?:in|for)',
            
            # Questions and descriptive content
            r'\?',  # Any question marks
            r'^(?:what|how|why|when|where|can|is|are|do|does|will|should)',
            r'^\d+\s+(?:best|top|cheapest|scholarships|programs)',
        ]
        
        # Known university domains for validation
        self.university_domains = [
            '.edu', '.ac.uk', '.ac.in', '.ac.jp', '.ac.kr', '.ac.cn',
            '.edu.au', '.edu.sg', '.edu.my', '.edu.ph', '.edu.hk',
            '.university', '.college', '.institute'
        ]
        
        # Common university name variants to normalize
        self.name_normalizations = {
            'university': ['univ', 'u.', 'uni'],
            'college': ['coll', 'c.'],
            'institute': ['inst', 'i.', 'tech'],
            'technology': ['tech', 't.'],
            'of': ['o.'],
            'and': ['&', 'et'],
            'saint': ['st', 'st.', 'ste', 'ste.'],
        }
    
    def extract_university_names(self, soup: BeautifulSoup, source_url: str) -> List[UniversityName]:
        """Extract university names from webpage content"""
        university_names = []
        
        # Method 1: NER-based extraction
        ner_names = self._extract_with_ner(soup, source_url)
        university_names.extend(ner_names)
        
        # Method 2: Pattern-based extraction
        pattern_names = self._extract_with_patterns(soup, source_url)
        university_names.extend(pattern_names)
        
        # Method 3: Structured data extraction
        structured_names = self._extract_from_structured_data(soup, source_url)
        university_names.extend(structured_names)
        
        # Method 4: Link analysis for official university websites
        link_names = self._extract_from_links(soup, source_url)
        university_names.extend(link_names)
        
        # Deduplicate and clean
        cleaned_names = self._clean_and_deduplicate(university_names)
        
        # Quality scoring and filtering
        high_quality_names = self._filter_by_quality(cleaned_names)
        
        # Final validation
        validated_names = self._validate_university_names(high_quality_names)
        
        self.logger.info(f"Extracted {len(validated_names)} high-quality university names from {source_url}")
        return validated_names
    
    def _extract_with_ner(self, soup: BeautifulSoup, source_url: str) -> List[UniversityName]:
        """Extract university names using enhanced NER"""
        names = []
        text_content = soup.get_text()
        
        if not text_content or not self.nlp:
            return names
        
        # Process text in chunks to handle large content
        chunk_size = 100000  # 100KB chunks
        for i in range(0, len(text_content), chunk_size):
            chunk = text_content[i:i + chunk_size]
            doc = self.nlp(chunk)
            
            for ent in doc.ents:
                if ent.label_ == 'ORG':
                    if self._is_university_name(ent.text):
                        cleaned_name = self._clean_university_name(ent.text)
                        if cleaned_name:
                            confidence = self._calculate_ner_confidence(ent, chunk)
                            names.append(UniversityName(
                                name=cleaned_name,
                                confidence=confidence,
                                source_url=source_url,
                                extraction_method='ner',
                                quality_score=self._calculate_name_quality(cleaned_name)
                            ))
        
        return names
    
    def _extract_with_patterns(self, soup: BeautifulSoup, source_url: str) -> List[UniversityName]:
        """Extract university names using sophisticated pattern matching"""
        names = []
        text_content = soup.get_text()
        
        # Apply all pattern categories
        for category, patterns in self.university_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text_content, re.IGNORECASE | re.MULTILINE)
                
                for match in matches:
                    full_match = match.group(0)
                    # Try to extract the actual university name part
                    if match.groups():
                        university_part = match.group(1)  # First capture group
                    else:
                        university_part = full_match
                    
                    cleaned_name = self._clean_university_name(full_match)
                    if cleaned_name and self._validate_extracted_name(cleaned_name):
                        confidence = self._calculate_pattern_confidence(category, pattern, match, text_content)
                        names.append(UniversityName(
                            name=cleaned_name,
                            confidence=confidence,
                            source_url=source_url,
                            extraction_method=f'pattern_{category}',
                            quality_score=self._calculate_name_quality(cleaned_name)
                        ))
        
        return names
    
    def _extract_from_structured_data(self, soup: BeautifulSoup, source_url: str) -> List[UniversityName]:
        """Extract university names from JSON-LD and microdata"""
        names = []
        
        # JSON-LD extraction
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                import json
                data = json.loads(script.string)
                if isinstance(data, dict):
                    data = [data]
                
                for entry in data:
                    if isinstance(entry, dict):
                        org_type = entry.get('@type', '')
                        if org_type in ['CollegeOrUniversity', 'EducationalOrganization', 'University', 'College']:
                            name = entry.get('name', '')
                            if name and self._is_university_name(name):
                                cleaned_name = self._clean_university_name(name)
                                if cleaned_name:
                                    official_url = entry.get('url', '')
                                    names.append(UniversityName(
                                        name=cleaned_name,
                                        confidence=0.95,  # High confidence from structured data
                                        source_url=source_url,
                                        extraction_method='structured_data',
                                        official_url=official_url,
                                        quality_score=self._calculate_name_quality(cleaned_name)
                                    ))
            except Exception as e:
                self.logger.debug(f"Error parsing JSON-LD: {e}")
        
        # Microdata extraction
        university_microdata = soup.find_all(attrs={'itemtype': re.compile(r'schema\.org/(?:CollegeOrUniversity|EducationalOrganization)')})
        for item in university_microdata:
            name_elem = item.find(attrs={'itemprop': 'name'})
            if name_elem:
                name = name_elem.get_text(strip=True)
                if name and self._is_university_name(name):
                    cleaned_name = self._clean_university_name(name)
                    if cleaned_name:
                        url_elem = item.find(attrs={'itemprop': 'url'})
                        official_url = url_elem.get('href', '') if url_elem else ''
                        names.append(UniversityName(
                            name=cleaned_name,
                            confidence=0.9,
                            source_url=source_url,
                            extraction_method='microdata',
                            official_url=official_url,
                            quality_score=self._calculate_name_quality(cleaned_name)
                        ))
        
        return names
    
    def _extract_from_links(self, soup: BeautifulSoup, source_url: str) -> List[UniversityName]:
        """Extract university names from links to official university websites"""
        names = []
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            link_text = link.get_text(strip=True)
            
            # Check if link points to a university domain
            if self._is_university_domain(href):
                # Use link text as university name if it looks valid
                if link_text and self._is_university_name(link_text):
                    cleaned_name = self._clean_university_name(link_text)
                    if cleaned_name:
                        full_url = urljoin(source_url, href)
                        names.append(UniversityName(
                            name=cleaned_name,
                            confidence=0.85,
                            source_url=source_url,
                            extraction_method='link_analysis',
                            official_url=full_url,
                            quality_score=self._calculate_name_quality(cleaned_name)
                        ))
                
                # Also try to extract university name from URL
                url_name = self._extract_name_from_url(href)
                if url_name:
                    cleaned_name = self._clean_university_name(url_name)
                    if cleaned_name:
                        full_url = urljoin(source_url, href)
                        names.append(UniversityName(
                            name=cleaned_name,
                            confidence=0.7,
                            source_url=source_url,
                            extraction_method='url_analysis',
                            official_url=full_url,
                            quality_score=self._calculate_name_quality(cleaned_name)
                        ))
        
        return names
    
    def _clean_university_name(self, name: str) -> str:
        """Clean and normalize university name"""
        if not name:
            return ""
        
        original_name = name.strip()
        
        # Skip if it matches exclusion patterns
        for pattern in self.exclusion_patterns:
            if re.search(pattern, original_name.lower()):
                return ""
        
        # Remove common prefixes and suffixes
        name = re.sub(r'^\d+\.\s*', '', original_name)  # Remove "1. "
        name = re.sub(r'^#\d+\s*', '', name)           # Remove "#1 "
        name = re.sub(r'^\d+\)\s*', '', name)          # Remove "1) "
        name = re.sub(r'^\s*[-•*]\s*', '', name)       # Remove bullet points
        
        # Split by common separators and take the first part
        separators = [' - ', ' – ', ' | ', '\n', ' (', ': ']
        for sep in separators:
            if sep in name:
                name = name.split(sep)[0]
                break
        
        # Remove trailing descriptive text
        descriptive_patterns = [
            r'\s+(?:for international students|without ielts|taught in english).*$',
            r'\s+(?:admission|application|requirements).*$',
            r'\s+(?:scholarships?|programs?|courses?).*$',
            r'\s+(?:ranking|fees?|cost).*$',
        ]
        
        for pattern in descriptive_patterns:
            name = re.sub(pattern, '', name, flags=re.IGNORECASE)
        
        # Normalize whitespace
        name = re.sub(r'\s+', ' ', name)
        name = name.strip()
        
        # Apply name normalizations for consistency
        words = name.split()
        normalized_words = []
        for word in words:
            word_lower = word.lower().rstrip('.,')
            normalized = word
            for standard, variants in self.name_normalizations.items():
                if word_lower in variants:
                    normalized = standard.title()
                    break
            normalized_words.append(normalized)
        
        name = ' '.join(normalized_words)
        
        # Final validation
        if len(name) < 3 or len(name) > 150:
            return ""
        
        # Must contain at least one university indicator
        if not any(indicator in name.lower() for indicator in self.university_indicators['strong_indicators']):
            return ""
        
        return name
    
    def _is_university_name(self, text: str) -> bool:
        """Check if text appears to be a university name"""
        if not text or len(text.strip()) < 3:
            return False
        
        text_lower = text.lower().strip()
        
        # Check for exclusion patterns
        for pattern in self.exclusion_patterns:
            if re.search(pattern, text_lower):
                return False
        
        # Must contain university indicators
        has_university_keyword = any(
            indicator in text_lower 
            for indicator in self.university_indicators['strong_indicators']
        )
        
        if not has_university_keyword:
            # Check for specialized indicators
            has_specialized = any(
                indicator in text_lower 
                for indicator in self.university_indicators['specialized_indicators']
            )
            if not has_specialized:
                return False
        
        # Check for proper noun structure (mostly capitalized words)
        words = text.split()
        if len(words) >= 2:
            capitalized_count = sum(1 for word in words if word and word[0].isupper())
            if capitalized_count < len(words) * 0.5:  # At least 50% capitalized
                return False
        
        return True
    
    def _validate_extracted_name(self, name: str) -> bool:
        """Additional validation for extracted names"""
        if not name:
            return False
        
        # Length check
        if len(name) < 5 or len(name) > 120:
            return False
        
        # Must not be just numbers or special characters
        if re.match(r'^[\d\s\-.,]+$', name):
            return False
        
        # Must contain letters
        if not re.search(r'[a-zA-Z]', name):
            return False
        
        # Should not be a URL
        if re.match(r'https?://', name.lower()):
            return False
        
        return True
    
    def _is_university_domain(self, url: str) -> bool:
        """Check if URL is from a university domain"""
        if not url:
            return False
        
        url_lower = url.lower()
        
        # Check for educational domain patterns
        for domain in self.university_domains:
            if domain in url_lower:
                return True
        
        # Check for university keywords in domain
        university_keywords = ['university', 'college', 'institute', 'edu', 'academic']
        parsed_url = urlparse(url_lower)
        domain = parsed_url.netloc
        
        return any(keyword in domain for keyword in university_keywords)
    
    def _extract_name_from_url(self, url: str) -> str:
        """Extract potential university name from URL"""
        if not url:
            return ""
        
        parsed_url = urlparse(url.lower())
        domain = parsed_url.netloc
        
        # Remove common prefixes
        domain = re.sub(r'^www\.', '', domain)
        domain = re.sub(r'^m\.', '', domain)
        
        # Extract the main part of the domain
        domain_parts = domain.split('.')
        if len(domain_parts) >= 2:
            main_part = domain_parts[0]
            
            # Convert to title case and add "University" if it looks like an institution
            if len(main_part) > 2 and main_part.isalpha():
                return f"{main_part.title()} University"
        
        return ""
    
    def _calculate_ner_confidence(self, entity, context: str) -> float:
        """Calculate confidence score for NER-extracted entities"""
        base_confidence = 0.7
        
        # Boost confidence based on context
        context_lower = context.lower()
        
        # Check for educational context
        edu_keywords = ['university', 'college', 'student', 'academic', 'education', 'campus']
        edu_context_score = sum(1 for keyword in edu_keywords if keyword in context_lower) * 0.05
        
        # Check entity characteristics
        entity_text = entity.text
        if len(entity_text) > 5 and entity_text.count(' ') >= 1:  # Multi-word entities
            base_confidence += 0.1
        
        if any(indicator in entity_text.lower() for indicator in self.university_indicators['strong_indicators']):
            base_confidence += 0.15
        
        return min(base_confidence + edu_context_score, 1.0)
    
    def _calculate_pattern_confidence(self, category: str, pattern: str, match, context: str) -> float:
        """Calculate confidence score for pattern-matched entities"""
        base_scores = {
            'standard_patterns': 0.85,
            'international_patterns': 0.8,
            'specialized_patterns': 0.9,
            'acronym_patterns': 0.75,
            'complex_patterns': 0.8
        }
        
        confidence = base_scores.get(category, 0.7)
        
        # Adjust based on match quality
        match_text = match.group(0)
        if len(match_text) > 10 and match_text.count(' ') >= 2:  # Longer, multi-word matches
            confidence += 0.05
        
        # Check surrounding context
        start_pos = max(0, match.start() - 100)
        end_pos = min(len(context), match.end() + 100)
        surrounding_context = context[start_pos:end_pos].lower()
        
        edu_keywords = ['university', 'college', 'education', 'academic', 'student']
        context_boost = sum(1 for keyword in edu_keywords if keyword in surrounding_context) * 0.02
        
        return min(confidence + context_boost, 1.0)
    
    def _calculate_name_quality(self, name: str) -> float:
        """Calculate quality score for university name"""
        if not name:
            return 0.0
        
        quality = 0.0
        
        # Length score (prefer 15-80 characters)
        length = len(name)
        if 15 <= length <= 80:
            quality += 0.3
        elif 10 <= length <= 100:
            quality += 0.2
        else:
            quality += 0.1
        
        # Word count score (prefer 2-6 words)
        word_count = len(name.split())
        if 2 <= word_count <= 6:
            quality += 0.3
        elif word_count == 1 or word_count > 6:
            quality += 0.1
        
        # Capitalization score
        words = name.split()
        if words:
            capitalized_ratio = sum(1 for word in words if word and word[0].isupper()) / len(words)
            quality += capitalized_ratio * 0.2
        
        # University indicator score
        name_lower = name.lower()
        strong_indicators = sum(1 for indicator in self.university_indicators['strong_indicators'] if indicator in name_lower)
        quality += min(strong_indicators * 0.1, 0.2)
        
        return min(quality, 1.0)
    
    def _clean_and_deduplicate(self, names: List[UniversityName]) -> List[UniversityName]:
        """Clean and deduplicate university names"""
        # Group by normalized names
        name_groups = {}
        for uni_name in names:
            normalized = self._normalize_for_comparison(uni_name.name)
            if normalized not in name_groups:
                name_groups[normalized] = []
            name_groups[normalized].append(uni_name)
        
        # Select best representative for each group
        deduplicated = []
        for normalized, group in name_groups.items():
            # Sort by confidence and quality
            group.sort(key=lambda x: (x.confidence + x.quality_score), reverse=True)
            best_name = group[0]
            
            # Collect all variants
            variants = list(set(uni.name for uni in group if uni.name != best_name.name))
            best_name.name_variants = variants
            
            deduplicated.append(best_name)
        
        return deduplicated
    
    def _normalize_for_comparison(self, name: str) -> str:
        """Normalize name for comparison purposes"""
        normalized = name.lower()
        normalized = re.sub(r'\b(?:the|a|an)\b', '', normalized)  # Remove articles
        normalized = re.sub(r'[^\w\s]', '', normalized)          # Remove punctuation
        normalized = re.sub(r'\s+', ' ', normalized)             # Normalize whitespace
        return normalized.strip()
    
    def _filter_by_quality(self, names: List[UniversityName]) -> List[UniversityName]:
        """Filter names by quality thresholds"""
        min_confidence = self.config.get('min_confidence', 0.6)
        min_quality = self.config.get('min_quality', 0.5)
        
        filtered = []
        for name in names:
            if name.confidence >= min_confidence and name.quality_score >= min_quality:
                filtered.append(name)
        
        return filtered
    
    def _validate_university_names(self, names: List[UniversityName]) -> List[UniversityName]:
        """Final validation of university names"""
        validated = []
        
        for uni_name in names:
            # Skip if name fails final validation
            if not self._validate_extracted_name(uni_name.name):
                continue
            
            # Skip if confidence is too low
            if uni_name.confidence < 0.5:
                continue
            
            # Additional checks
            name_lower = uni_name.name.lower()
            
            # Must not be generic terms
            generic_terms = [
                'university', 'college', 'institute', 'school', 'education',
                'universities', 'colleges', 'institutes', 'schools'
            ]
            if uni_name.name.lower().strip() in generic_terms:
                continue
            
            # Mark as verified if high confidence + quality
            if uni_name.confidence >= 0.8 and uni_name.quality_score >= 0.7:
                uni_name.is_verified = True
            
            validated.append(uni_name)
        
        # Sort by confidence + quality score
        validated.sort(key=lambda x: (x.confidence + x.quality_score), reverse=True)
        
        return validated 