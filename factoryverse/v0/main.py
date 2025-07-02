import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import time
from duckduckgo_search import DDGS
import logging
import argparse
import random
from langdetect import detect, LangDetectException
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import spacy
import json
from dataclasses import dataclass
from typing import List, Dict, Set, Optional
from collections import defaultdict
from post_processor import DataPostProcessor

# Load spaCy English model globally
nlp = spacy.load("en_core_web_sm")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

# User agents for rotation
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0',
]

@dataclass
class Organization:
    name: str
    url: str
    org_type: str  # 'university', 'company', 'institute', 'research_center'
    source_url: str
    confidence_score: float
    extraction_method: str
    country: Optional[str] = None
    description: Optional[str] = None

@dataclass
class GeneralContent:
    title: str
    url: str
    content_type: str  # 'blog_post', 'navigation', 'directory', 'news'
    source_url: str
    description: Optional[str] = None

@dataclass
class QueryIntent:
    """Represents analyzed user query intent"""
    entity_types: Set[str]
    geographic_focus: Set[str]
    domain_focus: Set[str]
    organization_types: Set[str]
    search_intent: str
    confidence_factors: Dict[str, float]
    patterns: Dict[str, List[str]]

class OrganizationExtractor:
    def __init__(self, config_path: str = "verification_config.json"):
        self.config = self.load_config(config_path)
        self.current_query_intent = None
        
        # Domain-specific mappings for dynamic extraction
        self.domain_mappings = {
            'education': ['university', 'college', 'school', 'institute', 'academy'],
            'research': ['laboratory', 'research center', 'institute', 'foundation'],
            'business': ['company', 'corporation', 'startup', 'enterprise'],
            'healthcare': ['hospital', 'clinic', 'medical center', 'health system'],
            'technology': ['tech company', 'software', 'ai company', 'startup'],
            'government': ['agency', 'department', 'ministry', 'bureau'],
            'nonprofit': ['foundation', 'charity', 'ngo', 'organization']
        }
        
        # Base patterns (will be overridden by dynamic analysis)
        self.university_patterns = []
        self.research_patterns = []
        self.exclude_patterns = []
        
    def analyze_query(self, query: str) -> QueryIntent:
        """Analyze user query to understand intent and generate dynamic patterns"""
        doc = nlp(query.lower())
        
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
        
        # Analyze keywords for domain intent
        query_lower = query.lower()
        for domain, keywords in self.domain_mappings.items():
            if any(keyword in query_lower for keyword in keywords):
                domain_focus.add(domain)
                organization_types.update(keywords)
        
        # Additional academic detection
        academic_terms = ['university', 'universities', 'college', 'institute', 'academic', 'phd', 'research']
        if any(term in query_lower for term in academic_terms):
            domain_focus.add('education')
            organization_types.update(['university', 'college', 'institute', 'academy'])
        
        # Additional business detection  
        business_terms = ['startup', 'company', 'companies', 'accelerator', 'incubator', 'business']
        if any(term in query_lower for term in business_terms):
            domain_focus.add('business')
            organization_types.update(['company', 'startup', 'accelerator', 'incubator'])
        
        # Determine search intent
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
        """Determine overall search intent"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['university', 'college', 'phd', 'academic', 'research']):
            return 'academic'
        elif any(word in query_lower for word in ['startup', 'company', 'business', 'accelerator']):
            return 'business'
        elif any(word in query_lower for word in ['research', 'laboratory', 'institute', 'science']):
            return 'research'
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
    
    def set_query_intent(self, query_intent: QueryIntent):
        """Set current query intent and update patterns"""
        self.current_query_intent = query_intent
        
        # Update patterns for this query
        self.university_patterns = []
        self.research_patterns = []
        self.exclude_patterns = query_intent.patterns['exclude_patterns']
        
        # Separate patterns by type
        for pattern in query_intent.patterns['include_patterns']:
            if any(word in pattern for word in ['university', 'college', 'school', 'academy']):
                self.university_patterns.append(pattern)
            elif any(word in pattern for word in ['research', 'laboratory', 'institute']):
                self.research_patterns.append(pattern)
        
        logging.info(f"🎯 Query Intent Analysis:")
        logging.info(f"   Search Intent: {query_intent.search_intent}")
        logging.info(f"   Domain Focus: {', '.join(query_intent.domain_focus)}")
        logging.info(f"   Geographic Focus: {', '.join(query_intent.geographic_focus)}")
        logging.info(f"   Generated {len(query_intent.patterns['include_patterns'])} include patterns")
    
    def load_config(self, config_path: str) -> dict:
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.warning(f"Config file {config_path} not found. Using defaults.")
            return {
                'entity_types': ['ORG'],
                'contextual_keywords': ['university', 'college', 'institute', 'research', 'phd', 'doctorate']
            }
    
    def is_organization_name(self, name: str, url: str = "") -> tuple[bool, str, float]:
        """
        Determine if a name represents an actual organization using dynamic analysis.
        Returns (is_org, org_type, confidence_score)
        """
        name_clean = name.strip()
        name_lower = name_clean.lower()
        url_lower = url.lower()
        
        # Skip if too short or too long
        if len(name_clean) < 3 or len(name_clean) > 150:
            return False, "", 0.0
        
        # Check exclusion patterns first
        for pattern in self.exclude_patterns:
            if re.search(pattern, name_lower, re.IGNORECASE):
                return False, "", 0.0
        
        # Use dynamic confidence calculation if query intent is available
        if self.current_query_intent:
            confidence = self._calculate_dynamic_confidence(name, url, "", self.current_query_intent)
            org_type = self._determine_dynamic_org_type(name, url, self.current_query_intent)
            return confidence >= 0.5, org_type, confidence
        
        # Fallback to static analysis
        return self._static_organization_analysis(name_clean, name_lower)
    
    def _calculate_dynamic_confidence(self, name: str, url: str, description: str,
                                    query_intent: QueryIntent) -> float:
        """Calculate confidence using dynamic factors from query intent"""
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
        for pattern in query_intent.patterns['include_patterns']:
            if re.search(pattern, name_lower, re.IGNORECASE):
                confidence += query_intent.confidence_factors['title_match_bonus']
                break
        
        # NER enhancement
        doc = nlp(name)
        org_entities = [ent for ent in doc.ents if ent.label_ in ['ORG', 'PERSON']]
        if org_entities:
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def _determine_dynamic_org_type(self, name: str, url: str, query_intent: QueryIntent) -> str:
        """Determine organization type based on query intent and content"""
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
    
    def _static_organization_analysis(self, name_clean: str, name_lower: str) -> tuple[bool, str, float]:
        """Fallback static analysis when no query intent is available"""
        # Use spaCy NER to identify organizations
        doc = nlp(name_clean)
        org_entities = [ent for ent in doc.ents if ent.label_ in ['ORG', 'PERSON']]
        
        confidence = 0.0
        org_type = ""
        
        # Check for university patterns
        university_keywords = ['university', 'college', 'institute', 'school', 'academy']
        if any(keyword in name_lower for keyword in university_keywords):
            confidence += 0.8
            org_type = "university"
        
        # Check for research patterns
        if not org_type:
            research_keywords = ['research', 'laboratory', 'lab', 'foundation']
            if any(keyword in name_lower for keyword in research_keywords):
                confidence += 0.7
                org_type = "research_center"
        
        # Boost confidence if NER detected organization
        if org_entities:
            confidence += 0.6
            if not org_type:
                org_type = "organization"
        
        # Check for proper names (capitalized words)
        words = name_clean.split()
        capitalized_words = sum(1 for word in words if word[0].isupper() and len(word) > 2)
        if capitalized_words >= 2:
            confidence += 0.3
        
        return confidence >= 0.5, org_type, confidence
    
    def extract_organizations_from_soup(self, soup: BeautifulSoup, source_url: str) -> List[Organization]:
        """Extract organizations from parsed HTML"""
        organizations = []
        
        # Extract from structured data (JSON-LD)
        orgs_from_structured = self.extract_from_structured_data(soup, source_url)
        organizations.extend(orgs_from_structured)
        
        # Extract from links with context
        orgs_from_links = self.extract_from_links(soup, source_url)
        organizations.extend(orgs_from_links)
        
        # Extract from tables and lists
        orgs_from_tables = self.extract_from_tables_lists(soup, source_url)
        organizations.extend(orgs_from_tables)
        
        # Deduplicate based on name and URL
        unique_orgs = {}
        for org in organizations:
            key = f"{org.name.lower()}|{org.url}"
            if key not in unique_orgs or org.confidence_score > unique_orgs[key].confidence_score:
                unique_orgs[key] = org
        
        return list(unique_orgs.values())
    
    def extract_from_structured_data(self, soup: BeautifulSoup, source_url: str) -> List[Organization]:
        """Extract organizations from JSON-LD structured data"""
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
                    if org_type_ld in ["CollegeOrUniversity", "EducationalOrganization", "Organization"]:
                        name = entry.get('name')
                        url = entry.get('url')
                        
                        if name and url:
                            is_org, org_type, confidence = self.is_organization_name(name, url)
                            if is_org:
                                organizations.append(Organization(
                                    name=name,
                                    url=url,
                                    org_type=org_type,
                                    source_url=source_url,
                                    confidence_score=confidence + 0.2,  # Bonus for structured data
                                    extraction_method="structured_data",
                                    description=entry.get('description')
                                ))
            except Exception as e:
                logging.debug(f"Error parsing JSON-LD: {e}")
        
        return organizations
    
    def extract_from_links(self, soup: BeautifulSoup, source_url: str) -> List[Organization]:
        """Extract organizations from links with context analysis"""
        organizations = []
        base_domain = urlparse(source_url).netloc
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').strip()
            text = link.get_text(strip=True)
            
            if not href or not text:
                continue
            
            # Skip internal navigation
            if href.startswith('#') or href.startswith('mailto:') or href.startswith('tel:'):
                continue
            
            # Convert relative URLs to absolute
            full_url = urljoin(source_url, href)
            link_domain = urlparse(full_url).netloc
            
            # Skip same-domain links for now (they're usually navigation)
            if link_domain == base_domain:
                continue
            
            # Check if the link text represents an organization
            is_org, org_type, confidence = self.is_organization_name(text, full_url)
            
            if is_org:
                # Get context from parent elements
                context = self.get_link_context(link)
                
                # Boost confidence if in academic context
                if any(keyword in context.lower() for keyword in ['phd', 'doctorate', 'research', 'academic']):
                    confidence += 0.2
                
                organizations.append(Organization(
                    name=text,
                    url=full_url,
                    org_type=org_type,
                    source_url=source_url,
                    confidence_score=confidence,
                    extraction_method="link_analysis",
                    description=context
                ))
        
        return organizations
    
    def extract_from_tables_lists(self, soup: BeautifulSoup, source_url: str) -> List[Organization]:
        """Extract organizations from tables and lists"""
        organizations = []
        
        # Extract from tables
        for table in soup.find_all('table'):
            for row in table.find_all('tr'):
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 1:
                    cell = cells[0]
                    text = cell.get_text(strip=True)
                    
                    # Look for links in the cell
                    links = cell.find_all('a', href=True)
                    for link in links:
                        href = urljoin(source_url, link.get('href', ''))
                        link_text = link.get_text(strip=True)
                        
                        # Use the link text as the primary name
                        name = link_text if link_text else text
                        is_org, org_type, confidence = self.is_organization_name(name, href)
                        
                        if is_org:
                            organizations.append(Organization(
                                name=name,
                                url=href,
                                org_type=org_type,
                                source_url=source_url,
                                confidence_score=confidence,
                                extraction_method="table_extraction"
                            ))
        
        # Extract from lists
        for ul in soup.find_all(['ul', 'ol']):
            for li in ul.find_all('li'):
                text = li.get_text(strip=True)
                
                # Look for links in the list item
                links = li.find_all('a', href=True)
                for link in links:
                    href = urljoin(source_url, link.get('href', ''))
                    link_text = link.get_text(strip=True)
                    
                    name = link_text if link_text else text
                    is_org, org_type, confidence = self.is_organization_name(name, href)
                    
                    if is_org:
                        organizations.append(Organization(
                            name=name,
                            url=href,
                            org_type=org_type,
                            source_url=source_url,
                            confidence_score=confidence,
                            extraction_method="list_extraction"
                        ))
        
        return organizations
    
    def get_link_context(self, link_element) -> str:
        """Get contextual text around a link"""
        context_parts = []
        
        # Get text from parent elements
        for parent in [link_element.parent, link_element.parent.parent if link_element.parent else None]:
            if parent:
                text = parent.get_text(strip=True)
                if text and len(text) < 500:  # Avoid huge blocks
                    context_parts.append(text)
        
        return " ".join(context_parts)
    
    def classify_general_content(self, title: str, url: str, source_url: str) -> Optional[GeneralContent]:
        """Classify non-organization content"""
        title_lower = title.lower()
        
        # Blog posts and articles
        if any(pattern in title_lower for pattern in ['best', 'top', 'guide', 'how to', 'tips']):
            return GeneralContent(
                title=title,
                url=url,
                content_type="blog_post",
                source_url=source_url,
                description="General article or blog post"
            )
        
        # Navigation elements
        if any(pattern in title_lower for pattern in ['home', 'about', 'contact', 'menu']):
            return GeneralContent(
                title=title,
                url=url,
                content_type="navigation",
                source_url=source_url,
                description="Website navigation element"
            )
        
        # Directory or listing pages
        if any(pattern in title_lower for pattern in ['programs', 'courses', 'list', 'directory']):
            return GeneralContent(
                title=title,
                url=url,
                content_type="directory",
                source_url=source_url,
                description="Directory or listing page"
            )
        
        return None

class WebScraper:
    def __init__(self, request_delay: float = 1.0, max_retries: int = 3):
        self.request_delay = request_delay
        self.max_retries = max_retries
        self.robot_parsers = {}
        self.per_domain_lock = threading.Lock()
        self.per_domain_last_time = {}
        self.extractor = OrganizationExtractor()
        
    def can_fetch(self, url: str) -> bool:
        """Check if URL can be fetched according to robots.txt"""
        parsed_uri = urlparse(url)
        domain = f"{parsed_uri.scheme}://{parsed_uri.netloc}"
        
        if domain not in self.robot_parsers:
            rp = RobotFileParser()
            rp.set_url(urljoin(domain, 'robots.txt'))
            try:
                rp.read()
                self.robot_parsers[domain] = rp
            except Exception as e:
                logging.warning(f"Could not read robots.txt for {domain}: {e}")
                self.robot_parsers[domain] = None
        
        rp = self.robot_parsers.get(domain)
        return rp is None or rp.can_fetch('OrganizationScraper/1.0', url)
    
    def fetch_url(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a URL with proper rate limiting and retries"""
        if not self.can_fetch(url):
            logging.info(f"Disallowed by robots.txt: {url}")
            return None
        
        # Rate limiting
        parsed_uri = urlparse(url)
        domain = f"{parsed_uri.scheme}://{parsed_uri.netloc}"
        
        with self.per_domain_lock:
            last_time = self.per_domain_last_time.get(domain, 0)
            now = time.time()
            wait_time = self.request_delay - (now - last_time)
            if wait_time > 0:
                time.sleep(wait_time)
            self.per_domain_last_time[domain] = time.time()
        
        # Fetch with retries
        for attempt in range(self.max_retries):
            try:
                headers = {'User-Agent': random.choice(USER_AGENTS)}
                response = requests.get(url, timeout=10, headers=headers)
                response.raise_for_status()
                return BeautifulSoup(response.content, 'html.parser')
            except Exception as e:
                logging.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
        
        logging.error(f"All attempts failed for {url}")
        return None
    
    def scrape_url(self, url: str) -> tuple[List[Organization], List[GeneralContent]]:
        """Scrape a URL and return organizations and general content separately"""
        soup = self.fetch_url(url)
        if not soup:
            return [], []
        
        organizations = self.extractor.extract_organizations_from_soup(soup, url)
        
        # Also collect general content for reference
        general_content = []
        for link in soup.find_all('a', href=True):
            text = link.get_text(strip=True)
            href = urljoin(url, link.get('href', ''))
            
            if text and not self.extractor.is_organization_name(text, href)[0]:
                content = self.extractor.classify_general_content(text, href, url)
                if content:
                    general_content.append(content)
        
        return organizations, general_content

def search_and_save(query: str, filename: str = "search_results.csv", max_results: int = 30):
    """Perform DuckDuckGo search and save initial results with query metadata"""
    logging.info(f"Searching for: '{query}'")
    results = []
    
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    'title': r.get('title'),
                    'abstract': r.get('body'),
                    'url': r.get('href'),
                    'original_query': query  # Store original query for dynamic processing
                })
        
        df = pd.DataFrame(results)
        df.to_csv(filename, index=False, encoding='utf-8')
        logging.info(f"Saved {len(results)} search results to {filename}")
        
    except Exception as e:
        logging.error(f"Search failed: {e}")

def extract_query_from_results(search_results_csv: str = "search_results.csv") -> Optional[str]:
    """Extract original query from search results file"""
    try:
        df = pd.read_csv(search_results_csv)
        if 'original_query' in df.columns and not df.empty:
            return df['original_query'].iloc[0]
    except Exception as e:
        logging.warning(f"Could not extract query from {search_results_csv}: {e}")
    return None

def process_search_results(
    search_results_csv: str = "search_results.csv",
    organizations_csv: str = "verified_companies.csv",
    general_content_csv: str = "general_content.csv",
    failed_urls_csv: str = "failed_urls.csv",
    workers: int = 5,
    original_query: str = None
):
    """Process search results and separate organizations from general content"""
    
    try:
        df = pd.read_csv(search_results_csv)
    except FileNotFoundError:
        logging.error(f"Search results file {search_results_csv} not found")
        return
    
    scraper = WebScraper()
    
    # Analyze query intent for dynamic extraction
    if not original_query:
        original_query = extract_query_from_results(search_results_csv)
    
    if original_query:
        logging.info(f"🔍 Analyzing query intent for: '{original_query}'")
        query_intent = scraper.extractor.analyze_query(original_query)
        scraper.extractor.set_query_intent(query_intent)
    else:
        logging.warning("⚠️ No query found - using static extraction patterns")
    organizations = []
    general_content = []
    failed_urls = []
    
    def process_url(url):
        try:
            orgs, content = scraper.scrape_url(url)
            return orgs, content, None
        except Exception as e:
            logging.error(f"Failed to process {url}: {e}")
            return [], [], url
    
    # Process URLs with threading
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_url = {executor.submit(process_url, row['url']): row['url'] 
                        for _, row in df.iterrows() if pd.notna(row['url'])}
        
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                orgs, content, failed_url = future.result()
                
                if failed_url:
                    failed_urls.append({'url': failed_url})
                else:
                    organizations.extend(orgs)
                    general_content.extend(content)
                    
                logging.info(f"Processed {url}: {len(orgs)} organizations, {len(content)} content items")
                
            except Exception as e:
                logging.error(f"Error processing {url}: {e}")
                failed_urls.append({'url': url})
    
    # Save organizations (only actual organizations)
    if organizations:
        org_data = []
        for org in organizations:
            org_data.append({
                'organization_name': org.name,
                'url': org.url,
                'type': org.org_type,
                'source_url': org.source_url,
                'confidence_score': org.confidence_score,
                'extraction_method': org.extraction_method,
                'description': org.description
            })
        
        org_df = pd.DataFrame(org_data)
        # Sort by confidence score descending
        org_df = org_df.sort_values('confidence_score', ascending=False)
        org_df.to_csv(organizations_csv, index=False, encoding='utf-8')
        logging.info(f"Saved {len(org_data)} organizations to {organizations_csv}")
    
    # Save general content (for reference/further processing)
    if general_content:
        content_data = []
        for content in general_content:
            content_data.append({
                'title': content.title,
                'url': content.url,
                'content_type': content.content_type,
                'source_url': content.source_url,
                'description': content.description
            })
        
        content_df = pd.DataFrame(content_data)
        content_df.to_csv(general_content_csv, index=False, encoding='utf-8')
        logging.info(f"Saved {len(content_data)} general content items to {general_content_csv}")
    
    # Save failed URLs
    if failed_urls:
        failed_df = pd.DataFrame(failed_urls)
        failed_df.to_csv(failed_urls_csv, index=False, encoding='utf-8')
        logging.info(f"Saved {len(failed_urls)} failed URLs to {failed_urls_csv}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Web scraper for finding organizations")
    parser.add_argument("--search", type=str, help="Search query for finding organizations")
    parser.add_argument("--process", action="store_true", help="Process existing search results")
    parser.add_argument("--post-process", action="store_true", help="Run post-processing on verified companies")
    parser.add_argument("--workers", type=int, default=5, help="Number of worker threads")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests (seconds)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('scraper.log'),
            logging.StreamHandler()
        ]
    )
    
    if args.search:
        logging.info(f"Starting search for: {args.search}")
        search_and_save(args.search)
        
        # After search, automatically process results with query intent
        logging.info("Processing search results...")
        process_search_results(workers=args.workers, original_query=args.search)
        
        # After processing, automatically run post-processing with homepage validation
        logging.info("Running post-processing with homepage validation...")
        processor = DataPostProcessor()
        results = processor.process_verified_companies_with_homepage_validation()
        
        # Generate and save report
        report = processor.generate_report(results)
        with open('homepage_validation_report.md', 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Replace original file with clean version
        import shutil
        shutil.copy('verified_companies_clean.csv', 'verified_companies.csv')
        
        logging.info("✅ Complete pipeline with homepage validation finished successfully!")
        print(f"\n🎉 PIPELINE WITH HOMEPAGE VALIDATION COMPLETED!")
        print(f"📊 Results: {results['valid_organizations']} organizations, {results['reclassified_entries']} reclassified")
        print(f"📈 Validation success rate: {results['validation_success_rate']:.1f}%")
        
    elif args.process:
        logging.info("Processing existing search results...")
        process_search_results(workers=args.workers)
        
        # Automatically run post-processing with homepage validation after normal processing
        logging.info("Running post-processing with homepage validation...")
        processor = DataPostProcessor()
        results = processor.process_verified_companies_with_homepage_validation()
        
        # Generate and save report
        report = processor.generate_report(results)
        with open('homepage_validation_report.md', 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Replace original file with clean version
        import shutil
        shutil.copy('verified_companies_clean.csv', 'verified_companies.csv')
        
        logging.info("✅ Processing with homepage validation completed!")
        print(f"\n🎉 PROCESSING WITH HOMEPAGE VALIDATION COMPLETED!")
        print(f"📊 Results: {results['valid_organizations']} organizations, {results['reclassified_entries']} reclassified")
        print(f"📈 Validation success rate: {results['validation_success_rate']:.1f}%")
        
    elif args.post_process:
        logging.info("Running post-processing with homepage validation...")
        processor = DataPostProcessor()
        results = processor.process_verified_companies_with_homepage_validation()
        
        # Generate and save report
        report = processor.generate_report(results)
        with open('homepage_validation_report.md', 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Replace original file with clean version
        import shutil
        shutil.copy('verified_companies_clean.csv', 'verified_companies.csv')
        
        logging.info("✅ Homepage validation completed!")
        print(f"\n🎉 HOMEPAGE VALIDATION COMPLETED!")
        print(f"📊 Results: {results['valid_organizations']} organizations, {results['reclassified_entries']} reclassified")
        print(f"📈 Validation success rate: {results['validation_success_rate']:.1f}%")
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()