"""
Educational Entity Extractor for UniScholar platform.
Specialized extraction for universities, scholarships, programs, events, and funding.
Implements Phase 1 requirements from STUDENT_DATASET_PLAN.md
"""

import re
import logging
from typing import List, Dict, Set, Optional, Any
from datetime import datetime
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from dataclasses import dataclass

from .base import EntityExtractor
from .dynamic_ner import DynamicNERExtractor
from ..core.models import (
    University, Scholarship, AcademicProgram, StudentEvent, Funding,
    QueryIntent
)
from ..core.config import get_config
from ..core.exceptions import ExtractionError


@dataclass
class EducationalExtractionResult:
    """Result of educational entity extraction"""
    universities: List[University]
    scholarships: List[Scholarship]
    programs: List[AcademicProgram]
    events: List[StudentEvent]
    funding: List[Funding]
    total_entities: int
    extraction_time: float


class EducationalExtractor(EntityExtractor):
    """Specialized extractor for educational entities"""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__("educational", config)
        self.config = get_config()
        self.ner_extractor = DynamicNERExtractor(config)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Educational domain patterns from STUDENT_DATASET_PLAN.md
        self.university_patterns = {
            'strong_indicators': [
                r'\b(university|université|universidad|università|universität)\b',
                r'\b(college|collège|colegio|collegio|hochschule)\b',
                r'\b(institute of technology|technical university|polytechnic)\b',
                r'\b(school of medicine|medical school|law school|business school)\b'
            ],
            'domain_patterns': [r'\.edu$', r'\.ac\.', r'\.university$'],
            'context_keywords': [
                'admissions', 'enrollment', 'campus', 'faculty', 'degrees',
                'undergraduate', 'graduate', 'alumni', 'tuition', 'ranking'
            ]
        }
        
        self.scholarship_patterns = {
            'strong_indicators': [
                r'\b(scholarship|scholarships|bourse|beca)\b',
                r'\b(fellowship|fellowships|grant|grants)\b',
                r'\b(financial aid|aide financière|ayuda financiera)\b',
                r'\b(tuition waiver|fee waiver)\b'
            ],
            'amount_patterns': [
                r'\$[\d,]+', r'€[\d,]+', r'£[\d,]+', 
                r'full tuition', r'partial funding', r'up to \$[\d,]+'
            ],
            'context_keywords': [
                'eligible', 'apply', 'deadline', 'criteria', 'award',
                'merit-based', 'need-based', 'renewable', 'application'
            ]
        }

    def extract(self, html_content: str, source_url: str, **kwargs) -> List:
        """Implementation of abstract extract method from base class"""
        extraction_result = self.extract_educational_entities(html_content, source_url)
        
        # Return all entities as a flat list for base class compatibility
        all_entities = []
        all_entities.extend(extraction_result.universities)
        all_entities.extend(extraction_result.scholarships)
        all_entities.extend(extraction_result.programs)
        all_entities.extend(extraction_result.events)
        all_entities.extend(extraction_result.funding)
        
        return all_entities

    def extract_educational_entities(self, html_content: str, source_url: str, 
                                   query_intent: Optional[QueryIntent] = None) -> EducationalExtractionResult:
        """Extract all educational entities from HTML content"""
        start_time = datetime.now()
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract each entity type
            universities = self._extract_universities(soup, source_url, query_intent)
            scholarships = self._extract_scholarships(soup, source_url, query_intent)
            programs = self._extract_programs(soup, source_url, query_intent)
            events = self._extract_events(soup, source_url, query_intent)
            funding = self._extract_funding(soup, source_url, query_intent)
            
            # Calculate stats
            total_entities = len(universities) + len(scholarships) + len(programs) + len(events) + len(funding)
            extraction_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(
                f"Extracted {total_entities} educational entities: "
                f"{len(universities)} universities, {len(scholarships)} scholarships, "
                f"{len(programs)} programs, {len(events)} events, {len(funding)} funding"
            )
            
            return EducationalExtractionResult(
                universities=universities,
                scholarships=scholarships,
                programs=programs,
                events=events,
                funding=funding,
                total_entities=total_entities,
                extraction_time=extraction_time
            )
            
        except Exception as e:
            self.logger.error(f"Educational extraction failed for {source_url}: {e}")
            raise ExtractionError(f"Educational extraction failed: {e}")

    def _extract_universities(self, soup: BeautifulSoup, source_url: str, 
                            query_intent: Optional[QueryIntent] = None) -> List[University]:
        """Extract university entities"""
        universities = []
        text_content = soup.get_text()
        
        for pattern in self.university_patterns['strong_indicators']:
            matches = re.finditer(pattern, text_content, re.IGNORECASE)
            for match in matches:
                context_start = max(0, match.start() - 100)
                context_end = min(len(text_content), match.end() + 100)
                context = text_content[context_start:context_end]
                
                university_name = self._extract_name_from_context(context, match.group())
                
                if university_name and len(university_name) > 5:
                    university = University(
                        name=university_name,
                        official_url=source_url,
                        country=self._extract_country(context),
                        city=self._extract_city(context),
                        type=self._determine_university_type(university_name, context),
                        description=self._extract_description(context),
                        extraction_source=source_url,
                        last_updated=datetime.now()
                    )
                    universities.append(university)
        
        return self._deduplicate_list(universities, lambda x: (x.name.lower(), x.official_url))

    def _extract_scholarships(self, soup: BeautifulSoup, source_url: str, 
                            query_intent: Optional[QueryIntent] = None) -> List[Scholarship]:
        """Extract scholarship entities"""
        scholarships = []
        text_content = soup.get_text()
        
        for pattern in self.scholarship_patterns['strong_indicators']:
            matches = re.finditer(pattern, text_content, re.IGNORECASE)
            for match in matches:
                context_start = max(0, match.start() - 150)
                context_end = min(len(text_content), match.end() + 150)
                context = text_content[context_start:context_end]
                
                scholarship_name = self._extract_name_from_context(context, match.group())
                
                if scholarship_name:
                    scholarship = Scholarship(
                        name=scholarship_name,
                        provider=self._extract_provider(context, soup),
                        official_url=source_url,
                        amount=self._extract_amount(context),
                        application_deadline=self._extract_deadline(context),
                        description=self._extract_description(context),
                        extraction_source=source_url,
                        last_updated=datetime.now()
                    )
                    scholarships.append(scholarship)
        
        return self._deduplicate_list(scholarships, lambda x: (x.name.lower(), x.provider.lower()))

    def _extract_programs(self, soup: BeautifulSoup, source_url: str, 
                        query_intent: Optional[QueryIntent] = None) -> List[AcademicProgram]:
        """Extract academic program entities"""
        programs = []
        # Implement program extraction logic
        return programs

    def _extract_events(self, soup: BeautifulSoup, source_url: str, 
                      query_intent: Optional[QueryIntent] = None) -> List[StudentEvent]:
        """Extract student event entities"""
        events = []
        # Implement event extraction logic
        return events

    def _extract_funding(self, soup: BeautifulSoup, source_url: str, 
                       query_intent: Optional[QueryIntent] = None) -> List[Funding]:
        """Extract funding/grant entities"""
        funding = []
        # Implement funding extraction logic
        return funding

    # Helper methods
    def _extract_name_from_context(self, context: str, matched_indicator: str) -> Optional[str]:
        """Extract entity name from context around matched indicator"""
        words_before = context[:context.find(matched_indicator)].split()[-3:]
        words_after = context[context.find(matched_indicator):].split()[:4]
        
        potential_name = ' '.join(words_before + words_after)
        potential_name = re.sub(r'[^\w\s\-&]', '', potential_name).strip()
        
        if len(potential_name) > 5 and any(word[0].isupper() for word in potential_name.split()):
            return potential_name
        
        return None

    def _extract_country(self, context: str) -> str:
        """Extract country from context"""
        countries = ['USA', 'United States', 'UK', 'United Kingdom', 'Germany', 'France', 
                    'Canada', 'Australia', 'China', 'Japan', 'India', 'Brazil']
        
        for country in countries:
            if country.lower() in context.lower():
                return country
        return ""

    def _extract_city(self, context: str) -> str:
        """Extract city from context"""
        city_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*([A-Z]{2})\b'
        match = re.search(city_pattern, context)
        return match.group(1) if match else ""

    def _determine_university_type(self, name: str, context: str) -> str:
        """Determine university type from name and context"""
        name_lower = name.lower()
        if any(word in name_lower for word in ['technical', 'institute of technology', 'polytechnic']):
            return 'technical'
        elif 'private' in context.lower():
            return 'private'
        elif any(word in context.lower() for word in ['state', 'public', 'national']):
            return 'public'
        return 'university'

    def _extract_provider(self, context: str, soup: BeautifulSoup) -> str:
        """Extract scholarship provider"""
        # Simple extraction - could be enhanced
        return self._extract_name_from_context(context, "") or ""

    def _extract_amount(self, context: str) -> Dict[str, str]:
        """Extract monetary amount from context"""
        amount_pattern = r'(\$|€|£)([\d,]+)'
        match = re.search(amount_pattern, context)
        if match:
            return {"currency": match.group(1), "amount": match.group(2)}
        return {}

    def _extract_deadline(self, context: str) -> str:
        """Extract deadline from context"""
        date_pattern = r'\b(\w+\s+\d{1,2},?\s+\d{4}|\d{1,2}/\d{1,2}/\d{4})\b'
        match = re.search(date_pattern, context)
        return match.group(1) if match else ""

    def _extract_description(self, context: str) -> str:
        """Extract description from context"""
        description = re.sub(r'\s+', ' ', context).strip()
        return description[:500] + '...' if len(description) > 500 else description

    def _deduplicate_list(self, items: List, key_func) -> List:
        """Remove duplicates from list using key function"""
        seen = set()
        unique = []
        
        for item in items:
            key = key_func(item)
            if key not in seen:
                seen.add(key)
                unique.append(item)
        
        return unique 