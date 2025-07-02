"""
Academic Web Crawler for UniScholar platform.

This module implements web crawling specifically for academic content,
including universities, scholarships, programs, events, and funding opportunities.
"""

import requests
import time
import logging
import threading
import random
import json
import re
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
from typing import List, Dict, Set, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False

from .base import BaseCrawler
from ..core.models import University, Scholarship, AcademicProgram, StudentEvent, Funding, Organization, GeneralContent
from ..extractors.dynamic_ner import DynamicNERExtractor
from ..extractors.search_ner import SearchNERProcessor, SearchNERResult
from ..core.exceptions import CrawlerError
from ..enhancers.query_understanding import AdvancedQueryAnalyzer, IntelligentResultRanker, QueryContext
from ..extractors.educational_extractor import EducationalExtractor
from ..extractors.university_name_extractor import UniversityNameExtractor, UniversityName
from ..crawlers.enhanced_university_crawler import EnhancedUniversityCrawler, UniversityDiscoveryResult
from ..core.config import get_config
from ..core.rate_limiter import RateLimiter

# User agents for rotation
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0',
]

@dataclass
class CrawlResult:
    """Result of a crawling operation"""
    organizations: List[Organization]
    general_content: List[GeneralContent]
    failed_urls: List[str]
    query_intent: Optional[object] = None

class AcademicWebCrawler(BaseCrawler):
    """
    Enhanced Academic Web Crawler with advanced university name extraction
    
    Key Features:
    - Advanced university name extraction using multiple methods
    - Intelligent source prioritization for university discovery
    - Enhanced recognition system with query understanding
    - Rate limiting and respectful crawling
    - Comprehensive quality scoring and validation
    """
    
    # Class-level rate limiting for search requests
    _last_search_time = 0
    _search_lock = threading.Lock()
    _min_search_interval = 3.0  # Minimum seconds between searches
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.config = get_config()
        self.rate_limiter = RateLimiter(config)
        
        # Enhanced extractors and crawlers
        self.ner_processor = SearchNERProcessor(config)
        self.educational_extractor = EducationalExtractor(config)
        self.university_name_extractor = UniversityNameExtractor(config)
        self.enhanced_university_crawler = EnhancedUniversityCrawler(config)
        
        # Advanced query understanding and ranking
        self.query_analyzer = AdvancedQueryAnalyzer(config)
        self.result_ranker = IntelligentResultRanker(config)
        
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # University extraction modes
        self.extraction_modes = {
            'comprehensive': True,  # Use all extraction methods
            'university_focused': True,  # Focus specifically on university names
            'quality_priority': True,   # Prioritize high-quality sources
            'intelligent_ranking': True  # Use advanced ranking system
        }
        
        self.robot_parsers = {}
        self.per_domain_lock = threading.Lock()
        self.per_domain_last_time = {}
        
        # Configure rate limiting parameters
        search_config = config.get('search_rate_limiting', {}) if config else {}
        self.min_search_interval = search_config.get('min_search_interval', 3.0)
        self.search_initial_delay = search_config.get('initial_delay', 2.0)
        self.search_max_delay = search_config.get('max_delay', 60.0)
        self.search_backoff_factor = search_config.get('backoff_factor', 2.0)
        self.search_max_retries = search_config.get('max_retries', 5)
        
        # Update class-level search interval
        AcademicWebCrawler._min_search_interval = self.min_search_interval
        
        # Setup session with academic-friendly headers
        self.session.headers.update({
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
    
    def _apply_global_search_rate_limit(self):
        """Apply global rate limiting for search requests"""
        with self._search_lock:
            current_time = time.time()
            time_since_last = current_time - self._last_search_time
            
            if time_since_last < self._min_search_interval:
                sleep_time = self._min_search_interval - time_since_last
                logging.info(f"⏳ Global search rate limit: waiting {sleep_time:.1f}s")
                time.sleep(sleep_time)
            
            self._last_search_time = time.time()
    
    def crawl(self, query: str, max_results: int = 30) -> CrawlResult:
        """Main crawling method implementation"""
        return self.search_and_crawl(query, max_results)
    
    def search_and_crawl(self, query: str, max_results: int = 30) -> CrawlResult:
        """Perform search and crawl the results for academic content with enhanced university name extraction"""
        if not DDGS_AVAILABLE:
            raise CrawlerError("DuckDuckGo search not available. Install with: pip install duckduckgo-search")
        
        logging.info(f"🔍 Searching for: '{query}'")
        
        # Step 1: Advanced query analysis
        query_context = self.query_analyzer.analyze_query(query)
        
        # Step 2: Analyze query intent for academic focus
        query_intent = self.educational_extractor.ner_extractor.analyze_query(query)
        
        # Step 3: Perform search
        search_results = self._perform_search(query, max_results)
        
        # Step 4: University-focused discovery (NEW ENHANCEMENT)
        university_result = None
        if self.extraction_modes.get('university_focused', True) and search_results:
            try:
                # Extract country from query context for targeted discovery
                target_country = None
                if hasattr(query_context, 'geographic_info') and query_context.geographic_info.get('countries'):
                    target_country = query_context.geographic_info['countries'][0]
                
                university_result = self.enhanced_university_crawler.discover_universities(
                    search_results, 
                    target_country
                )
                logging.info(f"🎓 University Discovery: Found {len(university_result.universities)} universities "
                           f"from {university_result.total_sources_crawled} sources")
                
                # Log discovery method breakdown
                for method, count in university_result.discovery_methods.items():
                    logging.info(f"   📊 {method}: {count} universities")
                    
            except Exception as e:
                logging.error(f"⚠️ University discovery failed: {e}")
                university_result = None
        
        # Step 5: Apply NER to search results and query
        ner_result = self.ner_processor.process_search_results(query, search_results)
        
        # Step 6: Intelligent result ranking
        ranked_results = self.result_ranker.rank_results(search_results, query_context, ner_result)
        
        # Step 7: Filter and reorder results based on comprehensive scoring
        enhanced_results = self._enhance_results_with_recognition(search_results, ranked_results, query_context)
        
        # Log insights from advanced analysis
        self._log_advanced_insights(query_context, ner_result, ranked_results[:5], university_result)
        
        # Step 8: Apply NER-based filtering
        filtered_results = self._filter_results_by_ner(enhanced_results, ner_result)
        
        # Step 9: Crawl the filtered and ranked results
        result = self._crawl_urls(filtered_results, query_intent, ner_result)
        
        # Step 10: Merge university discovery results (NEW ENHANCEMENT)
        if university_result and university_result.universities:
            discovered_orgs = self.enhanced_university_crawler.convert_to_organizations(university_result.universities)
            
            # Add university discovery results to main result
            result.organizations.extend(discovered_orgs)
            
            # Final deduplication
            result.organizations = self._deduplicate_all_organizations(result.organizations)
            
            logging.info(f"🔗 Enhanced Result: {len(result.organizations)} total organizations "
                        f"(including {len(discovered_orgs)} from university discovery)")
        
        result.query_intent = query_intent
        
        return result
    
    def _perform_search(self, query: str, max_results: int) -> List[Dict]:
        """Perform DuckDuckGo search with rate limiting and retry mechanisms"""
        # Apply global search rate limit first
        self._apply_global_search_rate_limit()
        
        results = []
        
        for attempt in range(self.search_max_retries):
            try:
                # Apply progressive delay to avoid rate limiting
                if attempt > 0:
                    delay = min(self.search_initial_delay * (self.search_backoff_factor ** (attempt - 1)), self.search_max_delay)
                    logging.info(f"⏳ Rate limit delay: {delay:.1f}s (attempt {attempt + 1}/{self.search_max_retries})")
                    time.sleep(delay)
                
                logging.info(f"🔍 Searching attempt {attempt + 1}: '{query}' (max_results={max_results})")
                
                # Perform search with timeout
                with DDGS() as ddgs:
                    search_start = time.time()
                    
                    # Let duckduckgo_search handle backend switching automatically
                    for r in ddgs.text(query, max_results=max_results):
                        results.append({
                            'title': r.get('title'),
                            'abstract': r.get('body'),
                            'url': r.get('href'),
                            'original_query': query
                        })
                
                search_time = time.time() - search_start
                logging.info(f"📊 Found {len(results)} search results in {search_time:.1f}s")
                
                # Success - return results
                if results:
                    return results
                else:
                    logging.warning(f"⚠️ No results returned on attempt {attempt + 1}")
                    if attempt < self.search_max_retries - 1:
                        continue  # Retry with delay
                    
            except Exception as e:
                error_msg = str(e)
                
                # Check if this is a rate limit error
                is_rate_limit = any(indicator in error_msg.lower() for indicator in [
                    'ratelimit', 'rate limit', '202', 'too many requests', 'quota exceeded'
                ])
                
                if is_rate_limit:
                    logging.warning(f"⚠️ Rate limit detected on attempt {attempt + 1}: {error_msg}")
                    if attempt < self.search_max_retries - 1:
                        continue  # Retry with exponential backoff
                else:
                    logging.error(f"❌ Search error on attempt {attempt + 1}: {error_msg}")
                    if attempt < self.search_max_retries - 1:
                        continue  # Retry for other errors too
        
        # All attempts failed
        logging.error(f"❌ Search failed after {self.search_max_retries} attempts.")
        logging.info("💡 Rate limiting suggestions:")
        logging.info("   • Wait 5-10 minutes before trying again")
        logging.info("   • Use more specific search terms")
        logging.info("   • Try searching for a different topic")
        logging.info("   • Consider running searches at different times of day")
        
        # Instead of raising an error, return empty results to allow graceful degradation
        return []
    
    def _crawl_urls(self, search_results: List[Dict], query_intent=None, ner_result=None) -> CrawlResult:
        """Crawl a list of URLs and extract academic content"""
        organizations = []
        general_content = []
        failed_urls = []
        
        def process_url(result):
            url = result['url']
            try:
                orgs, content = self.scrape_url(url, ner_result)
                return orgs, content, None
            except Exception as e:
                logging.error(f"❌ Failed to process {url}: {e}")
                return [], [], url
        
        # Process URLs with threading
        with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
            future_to_result = {
                executor.submit(process_url, result): result 
                for result in search_results
            }
            
            for future in as_completed(future_to_result):
                result = future_to_result[future]
                url = result['url']
                
                try:
                    orgs, content, failed_url = future.result()
                    
                    if failed_url:
                        failed_urls.append(failed_url)
                    else:
                        organizations.extend(orgs)
                        general_content.extend(content)
                        
                    logging.info(f"✅ Processed {url}: {len(orgs)} organizations, {len(content)} content items")
                    
                except Exception as e:
                    logging.error(f"❌ Error processing {url}: {e}")
                    failed_urls.append(url)
        
        # After processing direct URLs, also scrape universities from blog posts
        logging.info(f"🔗 Processing {len(general_content)} general content items for university lists...")
        blog_organizations = self._scrape_universities_from_blog_posts(general_content)
        
        if blog_organizations:
            logging.info(f"📊 Found {len(blog_organizations)} additional universities from blog posts!")
            organizations.extend(blog_organizations)
        
        # Final deduplication across all sources
        unique_organizations = {}
        for org in organizations:
            key = f"{org.name.lower().strip()}|{org.url}"
            if key not in unique_organizations or org.confidence_score > unique_organizations[key].confidence_score:
                unique_organizations[key] = org
        
        final_organizations = list(unique_organizations.values())
        logging.info(f"📈 Total unique organizations after deduplication: {len(final_organizations)}")
        
        return CrawlResult(
            organizations=final_organizations,
            general_content=general_content,
            failed_urls=failed_urls
        )
    
    def scrape_url(self, url: str, ner_result: SearchNERResult = None) -> Tuple[List[Organization], List[GeneralContent]]:
        """Scrape a single URL and extract organizations and content"""
        soup = self.fetch_url(url)
        if not soup:
            return [], []
        
        # Extract organizations using enhanced NER if available
        if ner_result:
            organizations = self._enhance_extraction_with_ner(soup, url, ner_result)
        else:
            organizations = self._extract_organizations_from_soup(soup, url)
        
        # Extract general content for reference
        general_content = self._extract_general_content(soup, url)
        
        return organizations, general_content
    
    def fetch_url(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a URL with proper rate limiting and retries"""
        if not self.can_fetch(url):
            logging.info(f"🚫 Disallowed by robots.txt: {url}")
            return None
        
        # Rate limiting
        self._apply_rate_limit(url)
        
        # Fetch with retries
        for attempt in range(self.max_retries):
            try:
                headers = {'User-Agent': random.choice(USER_AGENTS)}
                response = requests.get(url, timeout=self.session_timeout, headers=headers)
                response.raise_for_status()
                return BeautifulSoup(response.content, 'html.parser')
            except Exception as e:
                logging.warning(f"⚠️ Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
        
        logging.error(f"❌ All attempts failed for {url}")
        return None
    
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
                logging.debug(f"Could not read robots.txt for {domain}: {e}")
                self.robot_parsers[domain] = None
        
        rp = self.robot_parsers.get(domain)
        return rp is None or rp.can_fetch('UniScholar/1.0', url)
    
    def _apply_rate_limit(self, url: str):
        """Apply per-domain rate limiting"""
        parsed_uri = urlparse(url)
        domain = f"{parsed_uri.scheme}://{parsed_uri.netloc}"
        
        with self.per_domain_lock:
            last_time = self.per_domain_last_time.get(domain, 0)
            now = time.time()
            wait_time = self.request_delay - (now - last_time)
            if wait_time > 0:
                time.sleep(wait_time)
            self.per_domain_last_time[domain] = time.time()
    
    def _extract_organizations_from_soup(self, soup: BeautifulSoup, source_url: str) -> List[Organization]:
        """Extract organizations from parsed HTML using academic focus"""
        organizations = []
        
        # Extract from structured data (JSON-LD)
        orgs_from_structured = self._extract_from_structured_data(soup, source_url)
        organizations.extend(orgs_from_structured)
        
        # Extract from links with academic context
        orgs_from_links = self._extract_from_links(soup, source_url)
        organizations.extend(orgs_from_links)
        
        # Extract from tables and lists (common in academic directories)
        orgs_from_tables = self._extract_from_tables_lists(soup, source_url)
        organizations.extend(orgs_from_tables)
        
        # Deduplicate based on name and URL
        unique_orgs = {}
        for org in organizations:
            key = f"{org.name.lower()}|{org.url}"
            if key not in unique_orgs or org.confidence_score > unique_orgs[key].confidence_score:
                unique_orgs[key] = org
        
        return list(unique_orgs.values())
    
    def _extract_from_structured_data(self, soup: BeautifulSoup, source_url: str) -> List[Organization]:
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
                            confidence = self._calculate_academic_confidence(name, url, entry.get('description', ''))
                            if confidence >= 0.5:
                                organizations.append(Organization(
                                    name=name,
                                    url=url,
                                    org_type=self._determine_academic_org_type(name, url),
                                    source_url=source_url,
                                    confidence_score=confidence + 0.2,  # Bonus for structured data
                                    extraction_method="structured_data",
                                    description=entry.get('description')
                                ))
            except Exception as e:
                logging.debug(f"Error parsing JSON-LD: {e}")
        
        return organizations
    
    def _extract_from_links(self, soup: BeautifulSoup, source_url: str) -> List[Organization]:
        """Extract organizations from links with academic context analysis"""
        organizations = []
        base_domain = urlparse(source_url).netloc
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').strip()
            text = link.get_text(strip=True)
            
            if not href or not text:
                continue
            
            # Skip internal navigation and non-web links
            if href.startswith('#') or href.startswith('mailto:') or href.startswith('tel:'):
                continue
            
            # Skip javascript:void(0) and other JavaScript URLs
            if href.startswith('javascript:'):
                logging.debug(f"🚫 Skipping JavaScript URL: {href} for text: {text}")
                
                # Try to find alternative data attributes that might contain real URLs
                actual_url = self._find_alternative_url_in_link(link, source_url)
                if actual_url:
                    href = actual_url
                    logging.info(f"✅ Found alternative URL: {actual_url} for text: {text}")
                else:
                    # Skip this link entirely if no alternative URL found
                    continue
            
            # Convert relative URLs to absolute
            full_url = urljoin(source_url, href)
            
            # Validate that we have a proper HTTP/HTTPS URL
            if not self._is_valid_http_url(full_url):
                logging.debug(f"🚫 Skipping invalid URL: {full_url} for text: {text}")
                continue
            
            link_domain = urlparse(full_url).netloc
            
            # Skip same-domain links (usually navigation)
            if link_domain == base_domain:
                continue
            
            # Check if the link text represents an academic organization
            confidence = self._calculate_academic_confidence(text, full_url, "")
            
            if confidence >= 0.7:  # Raised threshold to match stricter validation
                # Get context from parent elements
                context = self._get_link_context(link)
                
                # No artificial confidence boost - rely on strict confidence scoring
                organizations.append(Organization(
                    name=text,
                    url=full_url,
                    org_type=self._determine_academic_org_type(text, full_url),
                    source_url=source_url,
                    confidence_score=confidence,
                    extraction_method="link_analysis",
                    description=context
                ))
        
        return organizations
    
    def _find_alternative_url_in_link(self, link_element, source_url: str) -> Optional[str]:
        """
        Try to find alternative URL data attributes when href is javascript:void(0)
        
        Many websites store actual URLs in data attributes when using JavaScript navigation
        """
        # Common data attributes that might contain URLs
        url_attributes = [
            'data-href', 'data-url', 'data-link', 'data-target', 'data-goto',
            'data-redirect', 'data-navigate', 'data-page', 'data-destination',
            'onclick'  # Sometimes onclick contains URL info
        ]
        
        for attr in url_attributes:
            value = link_element.get(attr, '').strip()
            if value:
                # Handle onclick attributes that might contain URLs
                if attr == 'onclick':
                    # Look for URL patterns in onclick JavaScript
                    import re
                    url_match = re.search(r"(?:window\.location|location\.href|window\.open)\s*=?\s*['\"]([^'\"]+)['\"]", value)
                    if url_match:
                        potential_url = url_match.group(1)
                        # Convert relative URL to absolute
                        if potential_url.startswith('/'):
                            return urljoin(source_url, potential_url)
                        elif potential_url.startswith('http'):
                            return potential_url
                else:
                    # For data attributes, convert relative URLs to absolute
                    if value.startswith('/'):
                        return urljoin(source_url, value)
                    elif value.startswith('http'):
                        return value
        
        return None
    
    def _is_valid_http_url(self, url: str) -> bool:
        """
        Validate that a URL is a proper HTTP/HTTPS URL
        """
        try:
            parsed = urlparse(url)
            return (
                parsed.scheme in ('http', 'https') and
                parsed.netloc and
                not url.startswith('javascript:') and
                not url.startswith('mailto:') and
                not url.startswith('tel:') and
                not url.startswith('#')
            )
        except Exception:
            return False
    
    def _extract_from_tables_lists(self, soup: BeautifulSoup, source_url: str) -> List[Organization]:
        """Extract organizations from tables and lists (common in academic directories)"""
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
                        href = link.get('href', '').strip()
                        link_text = link.get_text(strip=True)
                        
                        # Skip javascript:void(0) and other JavaScript URLs
                        if href.startswith('javascript:'):
                            logging.debug(f"🚫 Skipping JavaScript URL in table: {href} for text: {link_text}")
                            
                            # Try to find alternative data attributes that might contain real URLs
                            actual_url = self._find_alternative_url_in_link(link, source_url)
                            if actual_url:
                                href = actual_url
                                logging.info(f"✅ Found alternative URL in table: {actual_url} for text: {link_text}")
                            else:
                                # Skip this link entirely if no alternative URL found
                                continue
                        
                        # Convert relative URLs to absolute
                        full_url = urljoin(source_url, href)
                        
                        # Validate that we have a proper HTTP/HTTPS URL
                        if not self._is_valid_http_url(full_url):
                            logging.debug(f"🚫 Skipping invalid URL in table: {full_url} for text: {link_text}")
                            continue
                        
                        name = link_text if link_text else text
                        confidence = self._calculate_academic_confidence(name, full_url, "")
                        
                        if confidence >= 0.7:  # Raised threshold to match stricter validation
                            organizations.append(Organization(
                                name=name,
                                url=full_url,
                                org_type=self._determine_academic_org_type(name, full_url),
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
                    href = link.get('href', '').strip()
                    link_text = link.get_text(strip=True)
                    
                    # Skip javascript:void(0) and other JavaScript URLs
                    if href.startswith('javascript:'):
                        logging.debug(f"🚫 Skipping JavaScript URL in list: {href} for text: {link_text}")
                        
                        # Try to find alternative data attributes that might contain real URLs
                        actual_url = self._find_alternative_url_in_link(link, source_url)
                        if actual_url:
                            href = actual_url
                            logging.info(f"✅ Found alternative URL in list: {actual_url} for text: {link_text}")
                        else:
                            # Skip this link entirely if no alternative URL found
                            continue
                    
                    # Convert relative URLs to absolute
                    full_url = urljoin(source_url, href)
                    
                    # Validate that we have a proper HTTP/HTTPS URL
                    if not self._is_valid_http_url(full_url):
                        logging.debug(f"🚫 Skipping invalid URL in list: {full_url} for text: {link_text}")
                        continue
                    
                    name = link_text if link_text else text
                    confidence = self._calculate_academic_confidence(name, full_url, "")
                    
                    if confidence >= 0.7:  # Raised threshold to match stricter validation
                        organizations.append(Organization(
                            name=name,
                            url=full_url,
                            org_type=self._determine_academic_org_type(name, full_url),
                            source_url=source_url,
                            confidence_score=confidence,
                            extraction_method="list_extraction"
                        ))
        
        return organizations
    
    def _extract_general_content(self, soup: BeautifulSoup, source_url: str) -> List[GeneralContent]:
        """Extract general content for reference"""
        general_content = []
        
        for link in soup.find_all('a', href=True):
            text = link.get_text(strip=True)
            href = link.get('href', '').strip()
            
            # Skip javascript:void(0) and other JavaScript URLs
            if href.startswith('javascript:'):
                logging.debug(f"🚫 Skipping JavaScript URL in general content: {href} for text: {text}")
                # For general content, we don't try to find alternatives since we're looking for non-academic content
                continue
            
            # Convert relative URLs to absolute
            full_url = urljoin(source_url, href)
            
            # Validate that we have a proper HTTP/HTTPS URL
            if not self._is_valid_http_url(full_url):
                logging.debug(f"🚫 Skipping invalid URL in general content: {full_url} for text: {text}")
                continue
            
            if text and self._calculate_academic_confidence(text, full_url, "") < 0.5:
                content = self._classify_general_content(text, full_url, source_url)
                if content:
                    general_content.append(content)
        
        return general_content
    
    def _scrape_universities_from_blog_posts(self, general_content: List[GeneralContent]) -> List[Organization]:
        """Scrape universities mentioned in blog posts and articles"""
        organizations = []
        
        for content in general_content:
            # Only process blog posts that likely contain university lists
            if content.content_type == "blog_post" and self._is_university_list_article(content.title):
                logging.info(f"🔗 Following blog post for universities: {content.title}")
                
                # Fetch and parse the blog post
                soup = self.fetch_url(content.url)
                if soup:
                    # Extract universities from this blog post
                    blog_orgs = self._extract_universities_from_blog_content(soup, content.url, content.title)
                    organizations.extend(blog_orgs)
                    
                    logging.info(f"📊 Extracted {len(blog_orgs)} universities from blog: {content.title}")
        
        return organizations
    
    def _is_university_list_article(self, title: str) -> bool:
        """Check if an article likely contains a list of universities"""
        title_lower = title.lower()
        
        university_list_indicators = [
            # Best/Top patterns
            r'best.*universities',
            r'top.*universities',
            r'best.*colleges',
            r'top.*colleges',
            r'best.*schools',
            r'top.*schools',
            r'\d+.*best.*universities',
            r'\d+.*top.*universities',
            
            # Rankings patterns (expanded)
            r'ranking.*universities',
            r'rankings.*universities',
            r'university.*rankings',
            r'college.*rankings',
            r'ranked.*universities',
            r'ranking.*colleges',
            r'rankings.*of.*colleges',
            r'ranking.*of.*universities',
            r'\d+.*ranked.*universities',
            r'world.*university.*rankings',
            r'global.*university.*rankings',
            r'national.*university.*rankings',
            r'international.*university.*rankings',
            r'university.*ranking.*\d+',
            r'college.*ranking.*\d+',
            r'ranked:.*universities',
            r'rankings:.*universities',
            
            # Cost/Affordability patterns (NEW)
            r'cheapest.*countries.*for.*\w+',
            r'cheapest.*universities',
            r'cheapest.*colleges',
            r'cheapest.*universities.*in.*\w+',
            r'cheapest.*colleges.*in.*\w+',
            r'cheapest.*universities.*for.*\w+',
            r'cheapest.*country.*to.*study',
            r'cheapest.*country.*for.*\w+.*students',
            r'most.*affordable.*universities',
            r'most.*affordable.*colleges',
            r'affordable.*universities.*in',
            r'affordable.*colleges.*in',
            r'budget.*universities',
            r'budget.*colleges',
            r'budget.*friendly.*universities',
            r'low.*cost.*universities',
            r'low.*cost.*colleges',
            r'inexpensive.*universities',
            r'cheapest.*places.*to.*study',
            r'cheapest.*countries.*to.*study',
            r'affordable.*countries.*for.*students',
            r'budget.*countries.*for.*education',
            r'cheapest.*study.*abroad',
            r'affordable.*study.*abroad',
            r'low.*tuition.*universities',
            r'tuition.*free.*universities',
            r'free.*universities',
            r'cheapest.*degrees',
            r'affordable.*education.*in',
            r'universities.*without.*ielts',
            r'cheapest.*universities.*without.*\w+',
            r'affordable.*universities.*without.*\w+',
            
            # Subject-specific patterns  
            r'universities.*for.*computer science',
            r'colleges.*for.*computer science',
            r'universities.*for.*engineering',
            r'colleges.*for.*engineering',
            r'universities.*for.*business',
            r'colleges.*for.*business',
            r'rankings.*computer.*science',
            r'rankings.*engineering',
            r'rankings.*business',
            r'cheapest.*computer.*science.*degrees',
            r'affordable.*engineering.*programs',
            r'budget.*business.*schools',
            
            # Geographic patterns
            r'universities.*in.*california',
            r'colleges.*in.*california',
            r'universities.*in.*usa',
            r'universities.*in.*america',
            r'universities.*worldwide',
            r'global.*universities',
            r'cheapest.*countries.*in.*europe',
            r'affordable.*countries.*in.*asia',
            r'budget.*universities.*in.*\w+',
            
            # List/Guide patterns
            r'list.*of.*universities',
            r'guide.*to.*universities',
            r'complete.*list.*universities',
            r'comprehensive.*list.*universities',
            r'guide.*to.*affordable.*universities',
            r'list.*of.*cheap.*universities'
        ]
        
        return any(re.search(pattern, title_lower) for pattern in university_list_indicators)
    
    def _extract_universities_from_blog_content(self, soup: BeautifulSoup, source_url: str, article_title: str) -> List[Organization]:
        """Extract universities specifically from blog post content - STRICT validation"""
        organizations = []
        
        # Check headings (often contain university names)
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            text = heading.get_text(strip=True)
            
            # STRICT validation for headings
            if not self._looks_like_university_name(text):
                continue
                
            # Additional validation: ensure this isn't article structure
            if any(phrase in text.lower() for phrase in [
                'frequently asked', 'courses and fees', 'eligibility criteria',
                'how much does', 'what are the', 'which university',
                'top ranked', 'list of', 'requirements'
            ]):
                continue
            
            # Try to find an associated link
            link = heading.find('a', href=True)
            url = urljoin(source_url, link.get('href', '')) if link else ""
            
            confidence = self._calculate_academic_confidence(text, url, "")
            # Remove artificial bonus - use strict confidence only
            if confidence >= 0.7:  # Raised threshold for headings
                organizations.append(Organization(
                    name=text,
                    url=url,
                    org_type=self._determine_academic_org_type(text, url),
                    source_url=source_url,
                    confidence_score=confidence,
                    extraction_method="blog_content_heading",
                    description=f"Found in article: {article_title}"
                ))
        
        # Check list items (many "best universities" articles use lists)
        for li in soup.find_all('li'):
            text = li.get_text(strip=True)
            
            # STRICT validation for list items
            if not self._looks_like_university_name(text):
                continue
            
            # Extract and clean university name
            university_name = self._clean_university_name_from_list_item(text)
            
            # Skip if cleaning returned empty string or failed validation
            if not university_name or not self._looks_like_university_name(university_name):
                continue
            
            # Try to find an associated link
            link = li.find('a', href=True)
            url = urljoin(source_url, link.get('href', '')) if link else ""
            
            confidence = self._calculate_academic_confidence(university_name, url, "")
            # Remove artificial bonus - use strict confidence only
            if confidence >= 0.7:  # Raised threshold for list items
                organizations.append(Organization(
                    name=university_name,
                    url=url,
                    org_type=self._determine_academic_org_type(university_name, url),
                    source_url=source_url,
                    confidence_score=confidence,
                    extraction_method="blog_content_list",
                    description=f"Found in article: {article_title}"
                ))
        
        # Check strong/bold text (often used for university names)
        for strong in soup.find_all(['strong', 'b']):
            text = strong.get_text(strip=True)
            
            # STRICT validation for emphasized text
            if not self._looks_like_university_name(text):
                continue
            
            # Look for nearby links
            url = ""
            parent = strong.parent
            if parent:
                link = parent.find('a', href=True)
                if link:
                    url = urljoin(source_url, link.get('href', ''))
            
            confidence = self._calculate_academic_confidence(text, url, "")
            # Remove artificial bonus - use strict confidence only
            if confidence >= 0.7:  # Raised threshold for emphasized text
                organizations.append(Organization(
                    name=text,
                    url=url,
                    org_type=self._determine_academic_org_type(text, url),
                    source_url=source_url,
                    confidence_score=confidence,
                    extraction_method="blog_content_emphasis",
                    description=f"Found in article: {article_title}"
                ))
        
        # Deduplicate based on name
        unique_orgs = {}
        for org in organizations:
            key = org.name.lower().strip()
            if key not in unique_orgs or org.confidence_score > unique_orgs[key].confidence_score:
                unique_orgs[key] = org
        
        return list(unique_orgs.values())
    
    def _looks_like_university_name(self, text: str) -> bool:
        """Check if text looks like a university name - STRICT validation"""
        text_lower = text.lower().strip()
        
        # Skip if too short or too long
        if len(text) < 5 or len(text) > 100:
            return False
        
        # FIRST: Immediately reject obvious non-university content
        reject_patterns = [
            # Questions and FAQ patterns
            r'^\s*(what|how|why|when|where|can|is|are|do|does|will|should|which)',
            r'\?',  # Any question marks
            
            # Article titles and blog content
            r'^\s*(best|top|cheapest|most|ultimate|complete)',
            r'^\s*\d+\s+(best|top|cheapest|most)',
            r'^\s*(list|guide|tips|steps|ways|things)',
            r'(guide|tutorial|tips|steps|ways)\s+(to|for)',
            r'how\s+to\s+(get|apply|write|choose)',
            r'everything.*you.*need.*to.*know',
            
            # Navigation and website elements  
            r'^\s*(home|about|contact|blog|news|privacy|terms|cookies)$',
            r'^\s*(search|login|register|sign|explore|browse)$',
            r'^\s*(facebook|twitter|linkedin|instagram|youtube)$',
            r'(stories|ambassador|property|calculator|predictor)$',
            r'(read\s+more|learn\s+more|see\s+more|view\s+more)$',
            r'(click\s+here|more\s+info|website|homepage)$',
            
            # Course and service content
            r'^\s*(courses?|programs?|degrees?|classes?)\s+(in|for|at)',
            r'^\s*(exam|test|coaching|preparation|knockout)',
            r'(cut\s*off|merit\s*list|result|counselling)',
            r'(application\s*form|date\s*sheet|syllabus)',
            r'(eligibility|criteria|requirements|fees?|cost)',
            
            # Academic content descriptions (not institutions)
            r'(admission|application|visa|interview)',
            r'for\s+international\s+students',
            r'without\s+(ielts|toefl|gre|gmat)',
            r'(fully|partially)\s+funded',
            r'scholarships?\s+(in|for)',
            
            # Generic descriptions
            r'^\d+\.$',  # Just numbers like "1."
            r'^\d+\s+(scholarships?|programs?|courses?)',
            r'(leave\s+a\s+comment|cancel\s+reply)',
            r'(previous\s+post|next\s+post)$',
            r'(make\s+your|sort\s+out|start\s+your)',
            
            # Subject areas (not institution names)
            r'^\s*(medicine|engineering|arts|business|design|commerce)\s+(universities|colleges)',
            r'^\s*(natural\s+sciences|social\s+sciences)\s+(universities|colleges)',
        ]
        
        for pattern in reject_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return False
        
        # SECOND: Must have strong institutional indicators
        # Require proper institutional naming patterns
        institutional_patterns = [
            r'\b(university|college|institute|academy)\b',
            r'\b(university|college|institute)\s+of\s+[A-Z]',
            r'^[A-Z][a-z]+\s+(University|College|Institute)',
        ]
        
        has_institutional_keyword = any(re.search(pattern, text_lower) for pattern in institutional_patterns)
        
        # THIRD: Check for proper noun structure
        words = text.split()
        capitalized_words = len([w for w in words if len(w) > 2 and w[0].isupper()])
        
        # Must have institutional keyword AND proper capitalization
        return has_institutional_keyword and capitalized_words >= 2
    
    def _clean_university_name_from_list_item(self, text: str) -> str:
        """Clean university name from list item text (remove rankings, etc.)"""
        original_text = text.strip()
        
        # Skip if it looks like an article title rather than a university name
        article_title_patterns = [
            r'^\d+\s+(cheapest|best|top|affordable|free)',
            r'(scholarships?|programs?|courses?)\s+(in|for|at)',
            r'how to (get|apply|write)',
            r'(tips|guide|ways|steps) (for|to)',
            r'(fully|partially) funded',
            r'without (ielts|toefl|gre|gmat)',
            r'international students'
        ]
        
        for pattern in article_title_patterns:
            if re.search(pattern, original_text.lower()):
                return ""  # Return empty string to indicate this should be skipped
        
        # Remove common prefixes like "1. " or "#5 "
        text = re.sub(r'^\d+\.\s*', '', text)
        text = re.sub(r'^#\d+\s*', '', text)
        text = re.sub(r'^\d+\)\s*', '', text)
        text = re.sub(r'^=\d+\.\s*', '', text)  # Handle "=8. University..."
        
        # Split by common separators and take the first part (usually the university name)
        separators = [' - ', ' – ', ' | ', '\n', ' (']
        for sep in separators:
            if sep in text:
                text = text.split(sep)[0]
                break
        
        # Remove trailing descriptive text that's clearly not part of the university name
        text = re.sub(r'\s+(for international students|without ielts|taught in english).*$', '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def _calculate_academic_confidence(self, name: str, url: str, description: str) -> float:
        """Calculate confidence score for academic organizations - STRICT filtering for actual universities only"""
        confidence = 0.0
        name_lower = name.lower().strip()
        url_lower = url.lower()
        desc_lower = description.lower()
        
        # FIRST: Immediately exclude obvious non-university content
        exclude_patterns = [
            # FAQ and question patterns
            r'^(what|how|why|when|where|can|is|are|do|does|will|should)',
            r'\?',  # Any text with question marks
            
            # Blog post and article patterns
            r'^(best|top|cheapest|most|ultimate|complete|comprehensive)',
            r'^(list|guide|tips|steps|ways|things)',
            r'^(\d+\s+)?(best|top|cheapest|most)',
            r'(guide|tutorial|tips|steps|ways|things)\s+(to|for)',
            r'(everything|all|complete).*you.*need.*to.*know',
            r'how\s+to\s+(get|apply|write|choose|find)',
            
            # Navigation and website elements
            r'^(home|about|contact|blog|news|privacy|terms|cookies)$',
            r'^(search|login|register|sign|explore|browse)$',
            r'^(facebook|twitter|linkedin|instagram|youtube)$',
            r'(stories|ambassador|property|calculator|predictor)$',
            
            # Course and service listings
            r'^(courses?|programs?|degrees?|classes?)\s+(in|for|at)',
            r'^(exam|test|coaching|preparation|knockout)',
            r'(cut\s*off|merit\s*list|result|counselling|application\s*form)',
            r'(date\s*sheet|syllabus|question\s*papers?|e-books)',
            
            # Academic content that's not an institution
            r'(eligibility|criteria|requirements|fees?|cost|scholarship)',
            r'(admission|application|visa|interview)',
            r'(in\s+(usa|uk|canada|australia|germany|china|india))',
            r'for\s+international\s+students',
            r'without\s+(ielts|toefl|gre|gmat)',
            
            # Generic descriptive text
            r'(make\s+your|sort\s+out|start\s+your)',
            r'(industry\s+report|sample\s+papers)',
            r'(participate|participating|previous\s+year)',
            
            # Subject-specific but not institution names
            r'^(medicine|engineering|arts|business|design|commerce)\s+(universities|colleges)',
            r'^(natural\s+sciences|social\s+sciences|engineering)\s+(universities|colleges)',
        ]
        
        for pattern in exclude_patterns:
            if re.search(pattern, name_lower, re.IGNORECASE):
                return 0.0  # Immediately reject
        
        # SECOND: Check if this looks like an actual institution name
        # Require strong evidence that this is an actual university
        
        # Check for proper institutional naming patterns
        institutional_patterns = [
            r'^[A-Z][a-z]+\s+(University|College|Institute)(\s+of\s+[A-Z])?',  # "Harvard University", "MIT Institute"
            r'^University\s+of\s+[A-Z]',  # "University of California"
            r'^[A-Z][a-z]+\s+[A-Z][a-z]+\s+(University|College|Institute)',  # "Stanford Medical University"
            r'^[A-Z]{2,}\s+(University|College|Institute)',  # "MIT University", "UCLA College"
        ]
        
        is_institutional_name = any(re.search(pattern, name) for pattern in institutional_patterns)
        
        # Check for strong university indicators in URL domain
        university_domains = [
            r'\.edu$', r'\.ac\.',  # Educational domains
            r'university\.', r'college\.', r'institute\.',  # Institution domains
        ]
        
        has_university_domain = any(re.search(pattern, url_lower) for pattern in university_domains)
        
        # Check if name contains proper institutional keywords (but not in article context)
        institutional_keywords = ['university', 'college', 'institute', 'academy']
        has_institutional_keyword = any(keyword in name_lower for keyword in institutional_keywords)
        
        # THIRD: Build confidence score with strict requirements
        if is_institutional_name:
            confidence += 0.6  # Strong evidence of institutional name
        elif has_institutional_keyword and not any(word in name_lower for word in ['best', 'top', 'list', 'guide']):
            confidence += 0.3  # Has keyword but not in article context
        
        if has_university_domain:
            confidence += 0.4  # Strong domain evidence
        
        # Check for proper capitalization indicating a formal name
        words = name.split()
        if len(words) >= 2:
            capitalized_words = sum(1 for word in words if word[0].isupper() and len(word) > 2)
            if capitalized_words >= 2:
                confidence += 0.2
        
        # FOURTH: Additional strict validation
        # Must meet minimum threshold AND pass additional checks
        if confidence >= 0.5:
            # Extra validation: reject if it looks like content rather than institution
            content_indicators = [
                len(name) > 100,  # Too long to be an institution name
                name.count(',') > 2,  # Too many commas
                name.count(':') > 0,  # Likely article title or description
                ' - ' in name,  # Often indicates article/blog structure
                name.endswith('?'),  # Question
                name.lower().startswith(('how ', 'what ', 'why ', 'when ', 'where ')),
            ]
            
            if any(content_indicators):
                confidence = 0.0
        
        # FIFTH: Require minimum standards
        # Only consider as potential university if confidence is reasonable AND passes basic checks
        if confidence < 0.5:
            return 0.0
        
        # Final domain validation - prefer proper educational domains
        if has_university_domain:
            confidence = min(confidence + 0.1, 1.0)
        
        return min(confidence, 1.0)
    
    def _determine_academic_org_type(self, name: str, url: str) -> str:
        """Determine the type of academic organization"""
        name_lower = name.lower()
        url_lower = url.lower()
        combined = f"{name_lower} {url_lower}"
        
        if 'university' in combined:
            return 'university'
        elif 'college' in combined:
            return 'college'
        elif 'institute' in combined:
            return 'institute'
        elif 'school' in combined:
            return 'school'
        elif 'research' in combined or 'laboratory' in combined:
            return 'research_center'
        elif 'scholarship' in combined or 'fellowship' in combined:
            return 'scholarship_provider'
        else:
            return 'academic_organization'
    
    def _get_link_context(self, link_element) -> str:
        """Get contextual text around a link"""
        context_parts = []
        
        # Get text from parent elements
        for parent in [link_element.parent, link_element.parent.parent if link_element.parent else None]:
            if parent:
                text = parent.get_text(strip=True)
                if text and len(text) < 500:  # Avoid huge blocks
                    context_parts.append(text)
        
        return " ".join(context_parts)
    
    def _classify_general_content(self, title: str, url: str, source_url: str) -> Optional[GeneralContent]:
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
    
    def _enhance_results_with_recognition(self, search_results: List[Dict], 
                                        ranked_results: List, query_context: QueryContext) -> List[Dict]:
        """Enhance search results with recognition-based scoring and reordering"""
        # Create a mapping of URLs to relevance scores
        url_to_score = {result.url: result for result in ranked_results}
        
        # Enhance each search result with recognition insights
        enhanced_results = []
        for result in search_results:
            url = result.get('url', '')
            relevance_data = url_to_score.get(url)
            
            if relevance_data:
                # Add comprehensive scoring to the result
                result['recognition_score'] = relevance_data.overall_score
                result['confidence'] = relevance_data.confidence
                result['relevance_explanation'] = relevance_data.explanation
                result['component_scores'] = relevance_data.component_scores
                
                # Enhanced priority scoring
                priority_score = self._calculate_priority_score(result, query_context, relevance_data)
                result['priority_score'] = priority_score
                
                enhanced_results.append(result)
            else:
                # Fallback scoring for results without recognition data
                result['recognition_score'] = 0.3
                result['confidence'] = 0.0
                result['priority_score'] = 0.3
                enhanced_results.append(result)
        
        # Sort by priority score (highest first)
        enhanced_results.sort(key=lambda x: x.get('priority_score', 0), reverse=True)
        
        # Filter out very low quality results
        quality_threshold = 0.2
        filtered_results = [
            result for result in enhanced_results 
            if result.get('recognition_score', 0) >= quality_threshold
        ]
        
        logging.info(f"🎯 Recognition-enhanced filtering: {len(filtered_results)}/{len(enhanced_results)} results passed quality threshold")
        
        return filtered_results
    
    def _calculate_priority_score(self, result: Dict, query_context: QueryContext, 
                                relevance_data) -> float:
        """Calculate priority score combining multiple factors"""
        base_score = relevance_data.overall_score
        
        # Boost for query type alignment
        url = result.get('url', '').lower()
        title = result.get('title', '').lower()
        
        # Type-specific boosts
        type_boost = 0.0
        if query_context.query_type == 'funding_search':
            if any(word in url + title for word in ['scholarship', 'grant', 'funding', 'financial']):
                type_boost = 0.2
        elif query_context.query_type == 'admission_info':
            if any(word in url + title for word in ['admission', 'apply', 'requirements', 'entry']):
                type_boost = 0.2
        elif query_context.query_type == 'comparison_search':
            if any(word in url + title for word in ['ranking', 'best', 'top', 'compare']):
                type_boost = 0.15
        
        # Academic level alignment boost
        level_boost = 0.0
        content = f"{title} {result.get('abstract', '')}".lower()
        for level in query_context.academic_level:
            level_keywords = self._get_level_keywords_for_priority(level)
            if any(keyword in content for keyword in level_keywords):
                level_boost += 0.1
        
        level_boost = min(level_boost, 0.2)  # Cap the boost
        
        # Geographic alignment boost
        geo_boost = 0.0
        if query_context.target_countries:
            for country in query_context.target_countries:
                country_terms = [country.replace('_', ' '), country.replace('_', '')]
                if any(term in content for term in country_terms):
                    geo_boost = 0.15
                    break
        
        # User profile alignment boost
        profile_boost = 0.0
        if query_context.user_profile == 'prospective_student':
            if any(word in content for word in ['admission', 'apply', 'application', 'prospective']):
                profile_boost = 0.1
        elif query_context.user_profile == 'researcher':
            if any(word in content for word in ['research', 'faculty', 'phd', 'graduate']):
                profile_boost = 0.1
        
        # Calculate final priority score
        priority_score = base_score + type_boost + level_boost + geo_boost + profile_boost
        
        return min(priority_score, 1.0)  # Cap at 1.0
    
    def _get_level_keywords_for_priority(self, level: str) -> List[str]:
        """Get keywords for academic level for priority scoring"""
        level_keywords = {
            'undergraduate': ['bachelor', 'undergraduate', 'bachelors', 'first degree'],
            'graduate': ['master', 'graduate', 'masters', 'postgraduate'],
            'doctoral': ['phd', 'doctorate', 'doctoral', 'doctor'],
            'professional': ['professional', 'mba', 'law', 'medical']
        }
        return level_keywords.get(level, [])
    
    def _log_advanced_insights(self, query_context: QueryContext, ner_result, ranked_results: List, university_result=None):
        """Log comprehensive insights from advanced analysis including university discovery"""
        logging.info("🧠 Advanced Recognition Insights:")
        
        # Query understanding insights
        logging.info(f"   📝 Query Analysis:")
        logging.info(f"      Language: {query_context.language}")
        logging.info(f"      Type: {query_context.query_type}")
        logging.info(f"      Specificity: {query_context.search_specificity:.2f}")
        logging.info(f"      User Profile: {query_context.user_profile}")
        
        if query_context.academic_level:
            logging.info(f"      Academic Levels: {', '.join(query_context.academic_level)}")
        if query_context.academic_fields:
            logging.info(f"      Academic Fields: {', '.join(query_context.academic_fields)}")
        if query_context.target_countries:
            logging.info(f"      Target Countries: {', '.join(query_context.target_countries)}")
        
        # University discovery insights (NEW)
        if university_result:
            logging.info(f"   🎓 University Discovery:")
            logging.info(f"      Total Universities: {len(university_result.universities)}")
            logging.info(f"      High Confidence: {university_result.high_confidence_count}")
            logging.info(f"      Verified Universities: {university_result.verified_count}")
            logging.info(f"      Sources Crawled: {university_result.total_sources_crawled}")
            
            # Show discovery method breakdown
            if university_result.discovery_methods:
                methods_str = ", ".join([f"{method}:{count}" for method, count in university_result.discovery_methods.items()])
                logging.info(f"      Methods: {methods_str}")
            
            # Show top universities
            top_unis = sorted(university_result.universities, key=lambda x: x.confidence, reverse=True)[:3]
            if top_unis:
                logging.info(f"      Top Universities:")
                for i, uni in enumerate(top_unis, 1):
                    logging.info(f"        {i}. {uni.name} (Conf: {uni.confidence:.3f}, Quality: {uni.quality_score:.3f})")
        
        # NER insights (brief)
        if ner_result:
            entities = ner_result.query_entities
            logging.info(f"   🔍 Entity Extraction:")
            logging.info(f"      Universities: {len(entities.universities)}")
            logging.info(f"      Programs: {len(entities.programs)}")
            logging.info(f"      Locations: {len(entities.locations)}")
            logging.info(f"      Intent: {ner_result.intent_analysis.get('primary_intent', 'unknown')}")
        
        # Top ranked results insights
        if ranked_results:
            logging.info(f"   🏆 Top Recognition Results:")
            for i, result in enumerate(ranked_results[:3], 1):
                logging.info(f"      {i}. Score: {result.overall_score:.3f} | {result.url[:60]}...")
                if result.explanation:
                    logging.info(f"         Reasons: {', '.join(result.explanation[:2])}")
        
        # Query expansion insights
        if query_context.synonyms or query_context.related_terms:
            expansion_terms = list(query_context.synonyms)[:3] + list(query_context.related_terms)[:3]
            if expansion_terms:
                logging.info(f"   🔄 Query Expansion: {', '.join(expansion_terms[:5])}")

    def _log_ner_insights(self, ner_result: SearchNERResult) -> None:
        """Log insights from NER analysis"""
        logging.info("🧠 NER Analysis Results:")
        
        # Query entity analysis
        query_entities = ner_result.query_entities
        logging.info(f"   📝 Query Entities:")
        logging.info(f"      Universities: {len(query_entities.universities)}")
        logging.info(f"      Scholarships: {len(query_entities.scholarships)}")
        logging.info(f"      Programs: {len(query_entities.programs)}")
        logging.info(f"      Locations: {len(query_entities.locations)}")
        logging.info(f"      Subjects: {len(query_entities.subjects)}")
        logging.info(f"      Deadlines: {len(query_entities.deadlines)}")
        
        # Intent analysis
        intent = ner_result.intent_analysis
        logging.info(f"   🎯 Primary Intent: {intent.get('primary_intent', 'unknown')} (confidence: {intent.get('confidence', 0):.2f})")
        
        # Top relevance scores
        top_relevant = sorted(ner_result.relevance_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        logging.info(f"   📊 Top Relevant Results:")
        for url, score in top_relevant:
            logging.info(f"      {score:.2f}: {url[:60]}...")
        
        # Entity matches
        if ner_result.entity_matches:
            logging.info(f"   🔗 Entity Matches Found: {len(ner_result.entity_matches)}")
    
    def _filter_results_by_ner(self, search_results: List[Dict], ner_result: SearchNERResult) -> List[Dict]:
        """Filter and reorder search results based on NER relevance scores"""
        # Create a mapping of URLs to relevance scores
        url_scores = ner_result.relevance_scores
        
        # Filter out results with very low relevance (< 0.1)
        min_relevance = 0.1
        filtered_results = []
        
        for result in search_results:
            url = result.get('url', '')
            relevance_score = url_scores.get(url, 0.0)
            
            if relevance_score >= min_relevance:
                # Add relevance score to result for later use
                result['ner_relevance_score'] = relevance_score
                filtered_results.append(result)
            else:
                logging.debug(f"   🚫 Filtered out low relevance result: {url} (score: {relevance_score:.3f})")
        
        # Sort by relevance score (highest first)
        filtered_results.sort(key=lambda x: x.get('ner_relevance_score', 0), reverse=True)
        
        logging.info(f"   ✅ Filtered results: {len(filtered_results)}/{len(search_results)} passed relevance filter")
        
        return filtered_results

    def _enhance_extraction_with_ner(self, soup: BeautifulSoup, source_url: str, ner_result: SearchNERResult) -> List[Organization]:
        """Enhance organization extraction using NER insights"""
        organizations = []
        
        # Get NER entities for this URL
        url_entities = None
        for url, entities in ner_result.search_entities:
            if url == source_url:
                url_entities = entities
                break
        
        if not url_entities:
            # Fall back to regular extraction
            return self._extract_organizations_from_soup(soup, source_url)
        
        # Use NER entities to guide extraction
        organizations.extend(self._extract_from_ner_universities(soup, source_url, url_entities.universities))
        organizations.extend(self._extract_from_ner_programs(soup, source_url, url_entities.programs))
        organizations.extend(self._extract_from_ner_scholarships(soup, source_url, url_entities.scholarships))
        
        # Also run regular extraction and combine
        regular_orgs = self._extract_organizations_from_soup(soup, source_url)
        organizations.extend(regular_orgs)
        
        # Enhanced confidence scoring based on NER matches
        for org in organizations:
            org.confidence_score = self._calculate_ner_enhanced_confidence(
                org, url_entities, ner_result.query_entities
            )
        
        return organizations
    
    def _extract_from_ner_universities(self, soup: BeautifulSoup, source_url: str, universities: List) -> List[Organization]:
        """Extract universities based on NER-identified university entities"""
        organizations = []
        
        for university_entity in universities:
            university_name = university_entity.text.strip()
            
            # Look for links containing this university name
            university_links = soup.find_all('a', string=re.compile(re.escape(university_name), re.IGNORECASE))
            
            for link in university_links:
                href = link.get('href', '')
                if href and not href.startswith('javascript:'):
                    full_url = urljoin(source_url, href)
                    
                    if self._is_valid_http_url(full_url):
                        org = Organization(
                            name=university_name,
                            url=full_url,
                            org_type='university',
                            source_url=source_url,
                            confidence_score=0.9,  # High confidence from NER
                            extraction_method='ner_guided',
                            description=f"University identified by NER from {university_entity.source}"
                        )
                        organizations.append(org)
                        break  # Only add one link per university
        
        return organizations
    
    def _extract_from_ner_programs(self, soup: BeautifulSoup, source_url: str, programs: List) -> List[Organization]:
        """Extract programs based on NER-identified program entities"""
        organizations = []
        
        for program_entity in programs:
            program_name = program_entity.text.strip()
            
            # Look for context around program mentions
            program_text = soup.get_text()
            if program_name.lower() in program_text.lower():
                org = Organization(
                    name=f"Program: {program_name}",
                    url=source_url,  # Use source URL as program URL
                    org_type='program',
                    source_url=source_url,
                    confidence_score=0.7,
                    extraction_method='ner_program',
                    description=f"Academic program identified by NER: {program_name}"
                )
                organizations.append(org)
        
        return organizations
    
    def _extract_from_ner_scholarships(self, soup: BeautifulSoup, source_url: str, scholarships: List) -> List[Organization]:
        """Extract scholarships based on NER-identified scholarship entities"""
        organizations = []
        
        for scholarship_entity in scholarships:
            scholarship_name = scholarship_entity.text.strip()
            
            # Look for links or detailed information about this scholarship
            scholarship_links = soup.find_all('a', string=re.compile(re.escape(scholarship_name), re.IGNORECASE))
            
            target_url = source_url  # Default to source URL
            for link in scholarship_links:
                href = link.get('href', '')
                if href and not href.startswith('javascript:'):
                    target_url = urljoin(source_url, href)
                    break
            
            org = Organization(
                name=f"Scholarship: {scholarship_name}",
                url=target_url,
                org_type='scholarship',
                source_url=source_url,
                confidence_score=0.8,
                extraction_method='ner_scholarship',
                description=f"Scholarship opportunity identified by NER: {scholarship_name}"
            )
            organizations.append(org)
        
        return organizations
    
    def _calculate_ner_enhanced_confidence(self, org: Organization, url_entities, query_entities) -> float:
        """Calculate enhanced confidence score using NER insights"""
        base_confidence = org.confidence_score
        
        # Boost confidence if organization matches query entities
        query_university_names = {entity.text.lower() for entity in query_entities.universities}
        query_program_names = {entity.text.lower() for entity in query_entities.programs}
        query_scholarship_names = {entity.text.lower() for entity in query_entities.scholarships}
        
        org_name_lower = org.name.lower()
        
        # Check for matches
        university_match = any(name in org_name_lower for name in query_university_names)
        program_match = any(name in org_name_lower for name in query_program_names)
        scholarship_match = any(name in org_name_lower for name in query_scholarship_names)
        
        if university_match:
            base_confidence += 0.2
        if program_match:
            base_confidence += 0.15
        if scholarship_match:
            base_confidence += 0.15
        
        # Boost confidence for NER-guided extractions
        if org.extraction_method.startswith('ner'):
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)  # Cap at 1.0
    
    def _deduplicate_all_organizations(self, organizations: List[Organization]) -> List[Organization]:
        """Comprehensive deduplication of organizations from all sources"""
        if not organizations:
            return []
        
        # Group organizations by normalized name
        name_groups = {}
        
        for org in organizations:
            # Create normalized key for comparison
            normalized_name = re.sub(r'[^\w\s]', '', org.name.lower())
            normalized_name = re.sub(r'\b(?:the|university|college|institute)\b', '', normalized_name)
            normalized_name = re.sub(r'\s+', ' ', normalized_name).strip()
            
            # Also consider URL as part of the key to distinguish institutions with similar names
            url_key = urlparse(org.url).netloc.lower() if org.url else ''
            composite_key = f"{normalized_name}|{url_key}"
            
            if composite_key not in name_groups:
                name_groups[composite_key] = []
            name_groups[composite_key].append(org)
        
        # Select the best representative from each group
        deduplicated = []
        
        for group in name_groups.values():
            if len(group) == 1:
                deduplicated.append(group[0])
            else:
                # Sort by confidence score and choose the best
                group.sort(key=lambda x: (x.confidence_score, len(x.name)), reverse=True)
                best_org = group[0]
                
                # Merge information from other entries if beneficial
                for other in group[1:]:
                    # Use longer, more descriptive name if available
                    if len(other.name) > len(best_org.name) and other.confidence_score >= 0.7:
                        best_org.name = other.name
                    
                    # Use better URL if available
                    if not best_org.url and other.url:
                        best_org.url = other.url
                    elif other.url and 'edu' in other.url and 'edu' not in best_org.url:
                        best_org.url = other.url  # Prefer .edu domains
                
                deduplicated.append(best_org)
        
        # Final sort by confidence score
        deduplicated.sort(key=lambda x: x.confidence_score, reverse=True)
        
        logging.info(f"🔄 Deduplication: {len(organizations)} → {len(deduplicated)} organizations")
        
        return deduplicated 