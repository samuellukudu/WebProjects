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

# Load spaCy model for NLP processing
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logging.warning("spaCy English model not found. Install with: python -m spacy download en_core_web_sm")
    nlp = None

@dataclass
class QueryIntent:
    """Represents the analyzed intent of a user query"""
    entity_types: Set[str]  # What types of entities they're looking for
    geographic_focus: Set[str]  # Geographic entities mentioned
    domain_focus: Set[str]  # Domain/field entities (e.g., AI, medicine, business)
    organization_types: Set[str]  # Types of organizations (university, company, NGO)
    search_intent: str  # overall intent: academic, business, research, general
    confidence_factors: Dict[str, float]  # Dynamic confidence weightings
    patterns: Dict[str, List[str]]  # Dynamic regex patterns to use

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

class DynamicNERExtractor:
    """Dynamic organization extractor based on query analysis"""
    
    def __init__(self):
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
        
        # Domain-specific mappings
        self.domain_mappings = {
            'education': ['university', 'college', 'school', 'institute', 'academy'],
            'research': ['laboratory', 'research center', 'institute', 'foundation'],
            'business': ['company', 'corporation', 'startup', 'enterprise'],
            'healthcare': ['hospital', 'clinic', 'medical center', 'health system'],
            'technology': ['tech company', 'software', 'ai company', 'startup'],
            'government': ['agency', 'department', 'ministry', 'bureau'],
            'nonprofit': ['foundation', 'charity', 'ngo', 'organization']
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
        for domain in domain_focus:
            if domain == 'education':
                patterns['include_patterns'].extend([
                    r'\b(university|université|universidad|università|universiteit|universität)\b',
                    r'\b(college|école|escuela|scuola|school)\b',
                    r'\b(institute|institut|instituto|istituto)\b',
                    r'\b(academy|académie|academia|accademia)\b'
                ])
                patterns['domain_patterns'].extend([r'\.edu\b', r'\.ac\.'])
                
            elif domain == 'research':
                patterns['include_patterns'].extend([
                    r'\b(research center|research centre|centro de investigación)\b',
                    r'\b(laboratory|laboratoire|laboratorio|lab)\b',
                    r'\b(institute|institut|instituto|istituto)\b'
                ])
                
            elif domain == 'business':
                patterns['include_patterns'].extend([
                    r'\b(company|corporation|corp|inc|ltd)\b',
                    r'\b(startup|enterprise|ventures)\b',
                    r'\b(accelerator|incubator)\b'
                ])
                
            elif domain == 'healthcare':
                patterns['include_patterns'].extend([
                    r'\b(hospital|clinic|medical center)\b',
                    r'\b(health system|healthcare)\b'
                ])
        
        # Geographic patterns
        for location in geographic_focus:
            patterns['boost_patterns'].append(f'\\b{re.escape(location)}\\b')
        
        # Always exclude obvious non-organizations
        patterns['exclude_patterns'].extend([
            r'^(home|about|contact|blog|news)$',
            r'^(privacy|terms|legal|cookies)$',
            r'^(facebook|twitter|linkedin|instagram)$',
            r'^\d+\s+(best|top|free)',
            r'^top\s+\d+',
            r'how to|tips|guide|tutorial'
        ])
        
        return patterns
    
    def extract_organizations_with_intent(self, html_content: str, url: str, 
                                        query_intent: QueryIntent) -> List[DynamicOrganization]:
        """Extract organizations using dynamic patterns based on query intent"""
        soup = BeautifulSoup(html_content, 'html.parser')
        organizations = []
        
        # Extract from different sources
        orgs_from_structured = self._extract_from_structured_data(soup, url, query_intent)
        orgs_from_links = self._extract_from_links(soup, url, query_intent)
        orgs_from_text = self._extract_from_text_content(soup, url, query_intent)
        
        organizations.extend(orgs_from_structured)
        organizations.extend(orgs_from_links)
        organizations.extend(orgs_from_text)
        
        # Score relevance to original query
        organizations = self._score_relevance_to_query(organizations, query_intent)
        
        # Deduplicate and sort by relevance
        unique_orgs = self._deduplicate_organizations(organizations)
        
        return sorted(unique_orgs, key=lambda x: (x.relevance_score, x.confidence_score), reverse=True)
    
    def _extract_from_structured_data(self, soup: BeautifulSoup, source_url: str, 
                                    query_intent: QueryIntent) -> List[DynamicOrganization]:
        """Extract from JSON-LD with dynamic scoring"""
        organizations = []
        
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    data = [data]
                
                for entry in data:
                    if not isinstance(entry, dict):
                        continue
                    
                    org_type_ld = entry.get('@type', '')
                    if 'Organization' in org_type_ld or 'University' in org_type_ld:
                        name = entry.get('name')
                        url = entry.get('url')
                        
                        if name and url:
                            confidence = self._calculate_dynamic_confidence(
                                name, url, entry.get('description', ''), query_intent
                            )
                            
                            if confidence >= 0.3:  # Lower threshold for structured data
                                org_type = self._determine_dynamic_org_type(name, url, query_intent)
                                organizations.append(DynamicOrganization(
                                    name=name,
                                    url=url,
                                    org_type=org_type,
                                    source_url=source_url,
                                    confidence_score=confidence + query_intent.confidence_factors['structured_data_bonus'],
                                    extraction_method="structured_data",
                                    description=entry.get('description', ''),
                                    entity_matches=self._find_entity_matches(name, query_intent)
                                ))
            except Exception as e:
                logging.debug(f"Error parsing JSON-LD: {e}")
        
        return organizations
    
    def _extract_from_links(self, soup: BeautifulSoup, source_url: str,
                          query_intent: QueryIntent) -> List[DynamicOrganization]:
        """Extract from links with dynamic pattern matching"""
        organizations = []
        
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            text = link.get_text(strip=True)
            
            if not text or len(text) < 3:
                continue
                
            # Resolve relative URLs
            full_url = urljoin(source_url, href)
            
            # Check if text matches any include patterns
            if self._matches_include_patterns(text, query_intent.patterns['include_patterns']):
                confidence = self._calculate_dynamic_confidence(text, full_url, '', query_intent)
                
                if confidence >= 0.4:
                    org_type = self._determine_dynamic_org_type(text, full_url, query_intent)
                    organizations.append(DynamicOrganization(
                        name=text,
                        url=full_url,
                        org_type=org_type,
                        source_url=source_url,
                        confidence_score=confidence,
                        extraction_method="link_analysis",
                        entity_matches=self._find_entity_matches(text, query_intent)
                    ))
        
        return organizations
    
    def _extract_from_text_content(self, soup: BeautifulSoup, source_url: str,
                                 query_intent: QueryIntent) -> List[DynamicOrganization]:
        """Extract organizations from text content using NER"""
        organizations = []
        
        if not self.nlp:
            return organizations
            
        # Get main content text
        text_content = soup.get_text()
        doc = self.nlp(text_content[:10000])  # Limit text length for performance
        
        for ent in doc.ents:
            if ent.label_ == 'ORG' and len(ent.text) > 3:
                confidence = self._calculate_dynamic_confidence(ent.text, source_url, '', query_intent)
                
                if confidence >= 0.5:
                    org_type = self._determine_dynamic_org_type(ent.text, source_url, query_intent)
                    organizations.append(DynamicOrganization(
                        name=ent.text,
                        url=source_url,  # Use source URL as fallback
                        org_type=org_type,
                        source_url=source_url,
                        confidence_score=confidence,
                        extraction_method="ner_text_extraction",
                        entity_matches=self._find_entity_matches(ent.text, query_intent)
                    ))
        
        return organizations
    
    def _calculate_dynamic_confidence(self, name: str, url: str, description: str,
                                    query_intent: QueryIntent) -> float:
        """Calculate confidence score using dynamic factors"""
        confidence = query_intent.confidence_factors['base_organization']
        
        name_lower = name.lower()
        url_lower = url.lower()
        desc_lower = description.lower()
        combined_text = f"{name_lower} {url_lower} {desc_lower}"
        
        # Domain matching bonus
        if query_intent.domain_focus:
            for domain in query_intent.domain_focus:
                domain_keywords = self.domain_mappings.get(domain, [])
                if any(keyword in combined_text for keyword in domain_keywords):
                    confidence += query_intent.confidence_factors['domain_match']
                    break
        
        # Geographic matching bonus
        if query_intent.geographic_focus:
            for location in query_intent.geographic_focus:
                if location.lower() in combined_text:
                    confidence += query_intent.confidence_factors['geographic_match']
                    break
        
        # URL domain bonus
        if query_intent.search_intent == 'academic':
            if any(tld in url_lower for tld in ['.edu', '.ac.', '.university']):
                confidence += query_intent.confidence_factors['url_domain_bonus']
        
        # Title matching bonus
        if any(pattern.replace('\\b', '').replace('(', '').replace(')', '') in name_lower 
               for pattern in query_intent.patterns['include_patterns']):
            confidence += query_intent.confidence_factors['title_match_bonus']
        
        # Exclude patterns penalty
        for pattern in query_intent.patterns['exclude_patterns']:
            if re.search(pattern, name_lower, re.IGNORECASE):
                confidence = 0.0
                break
        
        return min(confidence, 1.0)
    
    def _determine_dynamic_org_type(self, name: str, url: str, query_intent: QueryIntent) -> str:
        """Determine organization type based on query intent"""
        name_lower = name.lower()
        url_lower = url.lower()
        combined = f"{name_lower} {url_lower}"
        
        # Use domain focus to prioritize organization types
        if 'education' in query_intent.domain_focus:
            if 'university' in combined:
                return 'university'
            elif 'college' in combined:
                return 'college'
            elif 'institute' in combined:
                return 'institute'
            elif 'school' in combined:
                return 'school'
        
        if 'research' in query_intent.domain_focus:
            if 'laboratory' in combined or 'lab' in combined:
                return 'laboratory'
            elif 'research' in combined:
                return 'research_center'
            elif 'institute' in combined:
                return 'research_institute'
        
        if 'business' in query_intent.domain_focus:
            if 'startup' in combined:
                return 'startup'
            elif 'accelerator' in combined or 'incubator' in combined:
                return 'accelerator'
            elif 'company' in combined or 'corp' in combined:
                return 'company'
        
        # Default fallback
        return 'organization'
    
    def _matches_include_patterns(self, text: str, patterns: List[str]) -> bool:
        """Check if text matches any include patterns"""
        text_lower = text.lower()
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        return False
    
    def _find_entity_matches(self, text: str, query_intent: QueryIntent) -> List[str]:
        """Find which query entities this text matches"""
        matches = []
        text_lower = text.lower()
        
        for entity_type in query_intent.entity_types:
            if entity_type in text_lower:
                matches.append(entity_type)
        
        for domain in query_intent.domain_focus:
            domain_keywords = self.domain_mappings.get(domain, [])
            if any(keyword in text_lower for keyword in domain_keywords):
                matches.append(domain)
        
        for location in query_intent.geographic_focus:
            if location.lower() in text_lower:
                matches.append(location)
        
        return matches
    
    def _score_relevance_to_query(self, organizations: List[DynamicOrganization], 
                                query_intent: QueryIntent) -> List[DynamicOrganization]:
        """Score how relevant each organization is to the original query"""
        for org in organizations:
            relevance = 0.0
            
            # Base relevance from confidence
            relevance += org.confidence_score * 0.5
            
            # Bonus for entity matches
            if org.entity_matches:
                relevance += len(org.entity_matches) * 0.1
            
            # Bonus for domain focus matches
            for domain in query_intent.domain_focus:
                if domain in org.name.lower() or domain in org.description.lower():
                    relevance += 0.2
            
            # Bonus for geographic matches
            for location in query_intent.geographic_focus:
                if location.lower() in org.name.lower() or location.lower() in org.description.lower():
                    relevance += 0.15
            
            org.relevance_score = min(relevance, 1.0)
        
        return organizations
    
    def _deduplicate_organizations(self, organizations: List[DynamicOrganization]) -> List[DynamicOrganization]:
        """Remove duplicate organizations, keeping the highest scoring ones"""
        unique_orgs = {}
        
        for org in organizations:
            # Create key based on name and domain
            domain = urlparse(org.url).netloc.lower()
            key = f"{org.name.lower()}|{domain}"
            
            if key not in unique_orgs or org.relevance_score > unique_orgs[key].relevance_score:
                unique_orgs[key] = org
        
        return list(unique_orgs.values())
    
    def _fallback_query_analysis(self, query: str) -> QueryIntent:
        """Fallback query analysis when spaCy is not available"""
        query_lower = query.lower()
        
        # Basic keyword-based analysis
        entity_types = set()
        domain_focus = set()
        organization_types = set()
        geographic_focus = set()
        
        if any(word in query_lower for word in ['university', 'college', 'academic']):
            domain_focus.add('education')
            organization_types.update(['university', 'college', 'institute'])
        
        if any(word in query_lower for word in ['company', 'startup', 'business']):
            domain_focus.add('business')
            organization_types.update(['company', 'startup'])
        
        search_intent = 'academic' if 'education' in domain_focus else 'general'
        
        return QueryIntent(
            entity_types=entity_types,
            geographic_focus=geographic_focus,
            domain_focus=domain_focus,
            organization_types=organization_types,
            search_intent=search_intent,
            confidence_factors={'base_organization': 0.5},
            patterns={'include_patterns': [], 'exclude_patterns': []}
        ) 