"""
Dynamic Named Entity Recognition-based Organization Extractor
Analyzes user queries to understand intent and adapts extraction patterns accordingly.
"""

import spacy
import re
import json
import logging
from typing import List, Dict, Tuple, Set, Optional
from urllib.parse import urlparse, urljoin
from dataclasses import dataclass
from collections import Counter, defaultdict
import requests
from bs4 import BeautifulSoup

from .base import EntityExtractor
from ..core.models import QueryIntent, Organization
from ..core.exceptions import ExtractionError

# Load spaCy model for NLP processing
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logging.warning("spaCy English model not found. Install with: python -m spacy download en_core_web_sm")
    nlp = None

@dataclass
class DynamicOrganization:
    """Organization with dynamic confidence scoring"""
    name: str
    url: str
    org_type: str
    source_url: str
    confidence_score: float
    extraction_method: str
    description: str = ""
    relevance_score: float = 0.0  # How relevant to the original query
    entity_matches: List[str] = None  # Which query entities this matches

class DynamicNERExtractor(EntityExtractor):
    """Dynamic organization extractor based on query analysis"""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__("organization", config)
        self.nlp = nlp
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Base entity type mappings
        self.entity_type_mappings = {
            'ORG': ['organization', 'company', 'institution'],
            'PERSON': ['researcher', 'academic', 'founder'],
            'GPE': ['location', 'country', 'city'],
            'MONEY': ['funding', 'investment', 'budget'],
            'DATE': ['established', 'founded', 'since']
        }
        
        # Academic-focused domain mappings
        self.domain_mappings = {
            'education': ['university', 'college', 'school', 'institute', 'academy'],
            'research': ['laboratory', 'research center', 'institute', 'foundation'],
            'scholarships': ['scholarship', 'fellowship', 'grant', 'financial aid'],
            'programs': ['program', 'major', 'degree', 'course', 'curriculum'],
            'events': ['conference', 'workshop', 'seminar', 'competition', 'fair'],
            'funding': ['funding', 'grant', 'research grant', 'travel grant']
        }
        
        # Academic entity type patterns
        self.academic_patterns = {
            'university': [
                r'\b(university|université|universidad|università|universität)\b',
                r'\b(college|collège|colegio|collegio|hochschule)\b',
                r'\b(institute of technology|technical university|polytechnic)\b',
                r'\b(school of medicine|medical school|law school|business school)\b'
            ],
            'scholarship': [
                r'\b(scholarship|scholarships|bourse|beca)\b',
                r'\b(fellowship|fellowships|grant|grants)\b',
                r'\b(financial aid|aide financière|ayuda financiera)\b',
                r'\b(tuition waiver|fee waiver)\b'
            ],
            'program': [
                r'\b(bachelor|ba|bs|bsc|license|licenciatura)\b',
                r'\b(master|ma|ms|msc|mba|mfa|mastère)\b',
                r'\b(phd|doctorate|doctoral|ph\.d\.)\b',
                r'\b(certificate|diploma|certification)\b'
            ],
            'event': [
                r'\b(conference|workshop|seminar|symposium)\b',
                r'\b(competition|contest|hackathon)\b',
                r'\b(fair|expo|exhibition)\b',
                r'\b(webinar|training|bootcamp)\b'
            ],
            'funding': [
                r'\b(research grant|travel grant|project funding)\b',
                r'\b(stipend|fellowship|bursary)\b',
                r'\b(funding opportunity|grant program)\b'
            ]
        }
        
    def analyze_query(self, query: str) -> QueryIntent:
        """Analyze user query to understand intent and generate dynamic patterns"""
        if not self.nlp:
            return self._fallback_query_analysis(query)
            
        doc = self.nlp(query.lower())
        
        # Extract entities
        entity_types = set()
        geographic_focus = set()
        domain_focus = set()
        organization_types = set()
        
        for ent in doc.ents:
            if ent.label_ == 'ORG':
                entity_types.add('organization')
            elif ent.label_ == 'GPE':
                geographic_focus.add(ent.text)
            elif ent.label_ in ['PERSON', 'MONEY', 'DATE']:
                entity_types.add(ent.label_.lower())
                
        # Analyze keywords for domain intent
        query_words = query.lower().split()
        for domain, keywords in self.domain_mappings.items():
            if any(keyword in query.lower() for keyword in keywords):
                domain_focus.add(domain)
                organization_types.update(keywords)
        
        # Detect search intent
        search_intent = self._determine_search_intent(query, domain_focus)
        
        # Generate dynamic confidence factors
        confidence_factors = self._generate_confidence_factors(
            entity_types, domain_focus, geographic_focus, search_intent
        )
        
        # Generate dynamic patterns
        patterns = self._generate_dynamic_patterns(
            entity_types, domain_focus, organization_types, geographic_focus
        )
        
        return QueryIntent(
            entity_types=entity_types,
            geographic_focus=geographic_focus,
            domain_focus=domain_focus,
            organization_types=organization_types,
            search_intent=search_intent,
            confidence_factors=confidence_factors,
            patterns=patterns
        )
    
    def _determine_search_intent(self, query: str, domain_focus: Set[str]) -> str:
        """Determine the overall search intent"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['university', 'college', 'phd', 'academic', 'research']):
            return 'academic'
        elif any(word in query_lower for word in ['startup', 'company', 'business', 'accelerator']):
            return 'business'
        elif any(word in query_lower for word in ['research', 'laboratory', 'institute', 'science']):
            return 'research'
        elif any(word in query_lower for word in ['hospital', 'clinic', 'medical', 'health']):
            return 'healthcare'
        elif 'education' in domain_focus:
            return 'academic'
        elif 'business' in domain_focus:
            return 'business'
        else:
            return 'general'
    
    def _generate_confidence_factors(self, entity_types: Set[str], domain_focus: Set[str], 
                                   geographic_focus: Set[str], search_intent: str) -> Dict[str, float]:
        """Generate dynamic confidence factors based on query analysis"""
        factors = {
            'base_organization': 0.5,
            'domain_match': 0.0,
            'geographic_match': 0.0,
            'entity_type_match': 0.0,
            'structured_data_bonus': 0.2,
            'url_domain_bonus': 0.0,
            'title_match_bonus': 0.0
        }
        
        # Adjust based on search intent
        if search_intent == 'academic':
            factors.update({
                'domain_match': 0.4,
                'url_domain_bonus': 0.3,  # .edu domains
                'title_match_bonus': 0.3
            })
        elif search_intent == 'business':
            factors.update({
                'domain_match': 0.3,
                'url_domain_bonus': 0.2,
                'title_match_bonus': 0.2
            })
        elif search_intent == 'research':
            factors.update({
                'domain_match': 0.4,
                'url_domain_bonus': 0.3,
                'title_match_bonus': 0.3
            })
        
        # Boost geographic matching if location is specified
        if geographic_focus:
            factors['geographic_match'] = 0.2
            
        # Boost entity type matching if specific types mentioned
        if entity_types:
            factors['entity_type_match'] = 0.2
            
        return factors
    
    def _generate_dynamic_patterns(self, entity_types: Set[str], domain_focus: Set[str],
                                 organization_types: Set[str], geographic_focus: Set[str]) -> Dict[str, List[str]]:
        """Generate dynamic regex patterns based on query analysis"""
        patterns = {
            'include_patterns': [],
            'exclude_patterns': [],
            'boost_patterns': [],
            'domain_patterns': []
        }
        
        # Generate include patterns based on domain focus
        if 'education' in domain_focus:
            patterns['include_patterns'].extend([
                r'\b(university|college|institute|school|academy)\b',
                r'\b(education|academic|phd|graduate|undergraduate)\b'
            ])
            patterns['domain_patterns'].extend([r'\.edu$', r'\.ac\.'])
            
        if 'business' in domain_focus:
            patterns['include_patterns'].extend([
                r'\b(company|corporation|startup|enterprise|business)\b',
                r'\b(inc|ltd|llc|corp)\b'
            ])
            
        if 'research' in domain_focus:
            patterns['include_patterns'].extend([
                r'\b(research|laboratory|institute|center|foundation)\b',
                r'\b(science|scientific|innovation)\b'
            ])
        
        # Add geographic patterns
        for location in geographic_focus:
            patterns['boost_patterns'].append(f"\\b{re.escape(location)}\\b")
        
        # Add organization type patterns
        for org_type in organization_types:
            patterns['boost_patterns'].append(f"\\b{re.escape(org_type)}\\b")
        
        return patterns

    def extract(self, html_content: str, source_url: str, 
                query_intent: Optional[QueryIntent] = None) -> List[DynamicOrganization]:
        """Extract organizations with dynamic intent-based patterns"""
        try:
            soup = self.preprocess_html(html_content)
            organizations = []
            
            # Extract from different sources
            if self.config.extraction.enable_structured_data:
                organizations.extend(self._extract_from_structured_data(soup, source_url, query_intent))
            
            organizations.extend(self._extract_from_links(soup, source_url, query_intent))
            organizations.extend(self._extract_from_text_content(soup, source_url, query_intent))
            
            # Apply query-specific scoring and filtering
            if query_intent:
                organizations = self._score_relevance_to_query(organizations, query_intent)
            
            # Deduplicate and filter
            organizations = self._deduplicate_organizations(organizations)
            organizations = self.filter_by_confidence(organizations)
            
            self.log_extraction_stats(organizations, source_url)
            return organizations
            
        except Exception as e:
            self.logger.error(f"Extraction failed for {source_url}: {e}")
            raise ExtractionError(f"Failed to extract organizations: {e}")
    
    def _extract_from_structured_data(self, soup: BeautifulSoup, source_url: str, 
                                    query_intent: Optional[QueryIntent] = None) -> List[DynamicOrganization]:
        """Extract organizations from structured data (JSON-LD, microdata)"""
        organizations = []
        structured_data = self.extract_structured_data(soup)
        
        for data in structured_data:
            if isinstance(data, dict):
                org_type = data.get('@type', '').lower()
                
                # Check if it's an organization type
                if any(org_word in org_type for org_word in ['organization', 'university', 'college', 'company']):
                    name = data.get('name', '')
                    url = data.get('url', '') or data.get('sameAs', '')
                    description = data.get('description', '')
                    
                    if name:
                        confidence = self._calculate_dynamic_confidence(name, url, description, query_intent)
                        org_type_determined = self._determine_dynamic_org_type(name, url, query_intent)
                        
                        organizations.append(DynamicOrganization(
                            name=self.clean_text(name),
                            url=self.normalize_url(url, source_url),
                            org_type=org_type_determined,
                            source_url=source_url,
                            confidence_score=confidence,
                            extraction_method="structured_data",
                            description=self.clean_text(description),
                            entity_matches=self._find_entity_matches(name, query_intent) if query_intent else []
                        ))
        
        return organizations
    
    def _extract_from_links(self, soup: BeautifulSoup, source_url: str,
                          query_intent: Optional[QueryIntent] = None) -> List[DynamicOrganization]:
        """Extract organizations from links with intent-based filtering"""
        organizations = []
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            text = self.clean_text(link.get_text())
            
            if not text or len(text) < 3:
                continue
            
            # Apply intent-based filtering
            if query_intent and not self._matches_include_patterns(text, query_intent.patterns.get('include_patterns', [])):
                continue
            
            url = self.normalize_url(href, source_url)
            confidence = self._calculate_dynamic_confidence(text, url, "", query_intent)
            
            if confidence >= self.config.extraction.confidence_threshold:
                org_type = self._determine_dynamic_org_type(text, url, query_intent)
                
                organizations.append(DynamicOrganization(
                    name=text,
                    url=url,
                    org_type=org_type,
                    source_url=source_url,
                    confidence_score=confidence,
                    extraction_method="link_extraction",
                    entity_matches=self._find_entity_matches(text, query_intent) if query_intent else []
                ))
        
        return organizations
    
    def _extract_from_text_content(self, soup: BeautifulSoup, source_url: str,
                                 query_intent: Optional[QueryIntent] = None) -> List[DynamicOrganization]:
        """Extract organizations from text content using NER"""
        organizations = []
        
        if not self.nlp:
            return organizations
        
        # Get main text content
        text_content = soup.get_text()
        text_content = self.clean_text(text_content, max_length=5000)  # Limit for performance
        
        # Process with spaCy
        doc = self.nlp(text_content)
        
        for ent in doc.ents:
            if ent.label_ == 'ORG':
                name = self.clean_text(ent.text)
                
                # Apply intent-based filtering
                if query_intent and not self._matches_include_patterns(name, query_intent.patterns.get('include_patterns', [])):
                    continue
                
                confidence = self._calculate_dynamic_confidence(name, "", "", query_intent)
                
                if confidence >= self.config.extraction.confidence_threshold:
                    org_type = self._determine_dynamic_org_type(name, "", query_intent)
                    
                    organizations.append(DynamicOrganization(
                        name=name,
                        url="",  # No direct URL from text extraction
                        org_type=org_type,
                        source_url=source_url,
                        confidence_score=confidence,
                        extraction_method="text_ner",
                        entity_matches=self._find_entity_matches(name, query_intent) if query_intent else []
                    ))
        
        return organizations
    
    def _calculate_dynamic_confidence(self, name: str, url: str, description: str,
                                    query_intent: Optional[QueryIntent] = None) -> float:
        """Calculate confidence score with dynamic weighting based on query intent"""
        indicators = {}
        
        # Basic organization indicators
        text_combined = f"{name} {url} {description}".lower()
        
        # Count domain-specific indicators
        if query_intent:
            for domain in query_intent.domain_focus:
                if domain in self.domain_mappings:
                    count = sum(1 for keyword in self.domain_mappings[domain] 
                               if keyword in text_combined)
                    if count > 0:
                        indicators[f'{domain}_indicators'] = count
        
        # URL domain indicators
        if url:
            domain = self.extract_url_domain(url)
            if '.edu' in domain or '.ac.' in domain:
                indicators['academic_domain'] = 1
            if any(word in domain for word in ['research', 'institute', 'lab']):
                indicators['research_domain'] = 1
        
        # Geographic indicators
        if query_intent:
            for location in query_intent.geographic_focus:
                if location.lower() in text_combined:
                    indicators['geographic_match'] = indicators.get('geographic_match', 0) + 1
        
        # Get confidence factors
        factors = query_intent.confidence_factors if query_intent else {
            'base_organization': 0.5,
            'domain_match': 0.3,
            'geographic_match': 0.2
        }
        
        return self.calculate_confidence_score(indicators, factors)
    
    def _determine_dynamic_org_type(self, name: str, url: str, query_intent: Optional[QueryIntent] = None) -> str:
        """Determine organization type with query intent context"""
        text_combined = f"{name} {url}".lower()
        
        # Use query intent to bias classification
        if query_intent:
            if query_intent.search_intent == 'academic':
                if any(word in text_combined for word in ['university', 'college', 'school', 'institute']):
                    return 'university'
                elif any(word in text_combined for word in ['research', 'laboratory', 'center']):
                    return 'research_center'
            elif query_intent.search_intent == 'business':
                if any(word in text_combined for word in ['company', 'corporation', 'startup', 'enterprise']):
                    return 'company'
        
        # Fallback to general classification
        if any(word in text_combined for word in ['university', 'college']):
            return 'university'
        elif any(word in text_combined for word in ['company', 'corporation']):
            return 'company'
        elif any(word in text_combined for word in ['research', 'institute']):
            return 'research_center'
        else:
            return 'organization'
    
    def _matches_include_patterns(self, text: str, patterns: List[str]) -> bool:
        """Check if text matches any include patterns"""
        if not patterns:
            return True  # No patterns means include all
        
        text_lower = text.lower()
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        return False
    
    def _find_entity_matches(self, text: str, query_intent: QueryIntent) -> List[str]:
        """Find which query entities this text matches"""
        matches = []
        text_lower = text.lower()
        
        # Check against domain focus
        for domain in query_intent.domain_focus:
            if domain in self.domain_mappings:
                for keyword in self.domain_mappings[domain]:
                    if keyword in text_lower:
                        matches.append(f"domain:{domain}")
                        break
        
        # Check against geographic focus
        for location in query_intent.geographic_focus:
            if location.lower() in text_lower:
                matches.append(f"location:{location}")
        
        # Check against organization types
        for org_type in query_intent.organization_types:
            if org_type in text_lower:
                matches.append(f"org_type:{org_type}")
        
        return list(set(matches))  # Remove duplicates
    
    def _score_relevance_to_query(self, organizations: List[DynamicOrganization], 
                                query_intent: QueryIntent) -> List[DynamicOrganization]:
        """Score relevance of organizations to the original query"""
        for org in organizations:
            relevance_score = 0.0
            
            # Base relevance from entity matches
            if org.entity_matches:
                relevance_score += len(org.entity_matches) * 0.2
            
            # Boost for domain alignment
            org_text = f"{org.name} {org.org_type}".lower()
            for domain in query_intent.domain_focus:
                if domain in self.domain_mappings:
                    matches = sum(1 for keyword in self.domain_mappings[domain] 
                                 if keyword in org_text)
                    relevance_score += matches * 0.3
            
            # Boost for geographic alignment
            for location in query_intent.geographic_focus:
                if location.lower() in org_text:
                    relevance_score += 0.2
            
            org.relevance_score = min(relevance_score, 1.0)
        
        # Sort by relevance score
        organizations.sort(key=lambda x: (x.relevance_score, x.confidence_score), reverse=True)
        return organizations
    
    def _deduplicate_organizations(self, organizations: List[DynamicOrganization]) -> List[DynamicOrganization]:
        """Remove duplicate organizations based on name and URL similarity"""
        if not organizations or not self.config.extraction.deduplication_enabled:
            return organizations
        
        unique_orgs = []
        seen_names = set()
        seen_urls = set()
        
        for org in organizations:
            name_key = org.name.lower().strip()
            url_key = org.url.lower().strip() if org.url else ""
            
            # Skip if we've seen similar name or URL
            if (name_key in seen_names) or (url_key and url_key in seen_urls):
                continue
            
            unique_orgs.append(org)
            seen_names.add(name_key)
            if url_key:
                seen_urls.add(url_key)
        
        return unique_orgs
    
    def _fallback_query_analysis(self, query: str) -> QueryIntent:
        """Fallback query analysis when spaCy is not available"""
        query_lower = query.lower()
        
        # Simple keyword-based analysis
        entity_types = set()
        geographic_focus = set()
        domain_focus = set()
        organization_types = set()
        
        # Detect domains
        for domain, keywords in self.domain_mappings.items():
            if any(keyword in query_lower for keyword in keywords):
                domain_focus.add(domain)
                organization_types.update(keywords)
        
        # Simple intent detection
        search_intent = 'general'
        if any(word in query_lower for word in ['university', 'college', 'academic']):
            search_intent = 'academic'
        elif any(word in query_lower for word in ['company', 'business', 'startup']):
            search_intent = 'business'
        
        return QueryIntent(
            entity_types=entity_types,
            geographic_focus=geographic_focus,
            domain_focus=domain_focus,
            organization_types=organization_types,
            search_intent=search_intent,
            confidence_factors={'base_organization': 0.5},
            patterns={'include_patterns': [], 'exclude_patterns': []}
        ) 