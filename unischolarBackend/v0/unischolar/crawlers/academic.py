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
from ..core.exceptions import CrawlerError

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
    """Specialized crawler for academic content"""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.extractor = DynamicNERExtractor(config)
        self.robot_parsers = {}
        self.per_domain_lock = threading.Lock()
        self.per_domain_last_time = {}
        
        # Setup session with academic-friendly headers
        self.session.headers.update({
            'User-Agent': random.choice(USER_AGENTS)
        })
    
    def crawl(self, query: str, max_results: int = 30) -> CrawlResult:
        """Main crawling method implementation"""
        return self.search_and_crawl(query, max_results)
    
    def search_and_crawl(self, query: str, max_results: int = 30) -> CrawlResult:
        """Perform search and crawl the results for academic content"""
        if not DDGS_AVAILABLE:
            raise CrawlerError("DuckDuckGo search not available. Install with: pip install duckduckgo-search")
        
        logging.info(f"🔍 Searching for: '{query}'")
        
        # Analyze query intent for academic focus
        query_intent = self.extractor.analyze_query(query)
        self.extractor.set_query_intent if hasattr(self.extractor, 'set_query_intent') else None
        
        # Perform search
        search_results = self._perform_search(query, max_results)
        
        # Crawl the search results
        crawl_result = self._crawl_urls(search_results, query_intent)
        crawl_result.query_intent = query_intent
        
        return crawl_result
    
    def _perform_search(self, query: str, max_results: int) -> List[Dict]:
        """Perform DuckDuckGo search and return results"""
        results = []
        
        try:
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    results.append({
                        'title': r.get('title'),
                        'abstract': r.get('body'),
                        'url': r.get('href'),
                        'original_query': query
                    })
            
            logging.info(f"📊 Found {len(results)} search results")
            return results
            
        except Exception as e:
            logging.error(f"❌ Search failed: {e}")
            raise CrawlerError(f"Search failed: {e}")
    
    def _crawl_urls(self, search_results: List[Dict], query_intent=None) -> CrawlResult:
        """Crawl a list of URLs and extract academic content"""
        organizations = []
        general_content = []
        failed_urls = []
        
        def process_url(result):
            url = result['url']
            try:
                orgs, content = self.scrape_url(url)
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
    
    def scrape_url(self, url: str) -> Tuple[List[Organization], List[GeneralContent]]:
        """Scrape a single URL and extract organizations and content"""
        soup = self.fetch_url(url)
        if not soup:
            return [], []
        
        # Extract organizations using the dynamic NER extractor
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
            
            # Convert relative URLs to absolute
            full_url = urljoin(source_url, href)
            link_domain = urlparse(full_url).netloc
            
            # Skip same-domain links (usually navigation)
            if link_domain == base_domain:
                continue
            
            # Check if the link text represents an academic organization
            confidence = self._calculate_academic_confidence(text, full_url, "")
            
            if confidence >= 0.5:
                # Get context from parent elements
                context = self._get_link_context(link)
                
                # Boost confidence if in academic context
                if any(keyword in context.lower() for keyword in ['phd', 'doctorate', 'research', 'academic', 'university']):
                    confidence += 0.2
                
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
                        href = urljoin(source_url, link.get('href', ''))
                        link_text = link.get_text(strip=True)
                        
                        name = link_text if link_text else text
                        confidence = self._calculate_academic_confidence(name, href, "")
                        
                        if confidence >= 0.5:
                            organizations.append(Organization(
                                name=name,
                                url=href,
                                org_type=self._determine_academic_org_type(name, href),
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
                    confidence = self._calculate_academic_confidence(name, href, "")
                    
                    if confidence >= 0.5:
                        organizations.append(Organization(
                            name=name,
                            url=href,
                            org_type=self._determine_academic_org_type(name, href),
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
            href = urljoin(source_url, link.get('href', ''))
            
            if text and self._calculate_academic_confidence(text, href, "") < 0.5:
                content = self._classify_general_content(text, href, source_url)
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
        """Extract universities specifically from blog post content"""
        organizations = []
        
        # Look for university names in various elements
        # Check headings (often contain university names)
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            text = heading.get_text(strip=True)
            if self._looks_like_university_name(text):
                # Try to find an associated link
                link = heading.find('a', href=True)
                url = urljoin(source_url, link.get('href', '')) if link else ""
                
                confidence = self._calculate_academic_confidence(text, url, "")
                if confidence >= 0.5:
                    organizations.append(Organization(
                        name=text,
                        url=url,
                        org_type=self._determine_academic_org_type(text, url),
                        source_url=source_url,
                        confidence_score=confidence + 0.1,  # Bonus for being in article
                        extraction_method="blog_content_heading",
                        description=f"Found in article: {article_title}"
                    ))
        
        # Check list items (many "best universities" articles use lists)
        for li in soup.find_all('li'):
            text = li.get_text(strip=True)
            if self._looks_like_university_name(text):
                # Extract just the university name part (remove ranking numbers, etc.)
                university_name = self._clean_university_name_from_list_item(text)
                
                # Skip if cleaning returned empty string (indicating it should be filtered out)
                if not university_name:
                    continue
                
                # Try to find an associated link
                link = li.find('a', href=True)
                url = urljoin(source_url, link.get('href', '')) if link else ""
                
                confidence = self._calculate_academic_confidence(university_name, url, "")
                if confidence >= 0.5:
                    organizations.append(Organization(
                        name=university_name,
                        url=url,
                        org_type=self._determine_academic_org_type(university_name, url),
                        source_url=source_url,
                        confidence_score=confidence + 0.1,  # Bonus for being in article
                        extraction_method="blog_content_list",
                        description=f"Found in article: {article_title}"
                    ))
        
        # Check strong/bold text (often used for university names)
        for strong in soup.find_all(['strong', 'b']):
            text = strong.get_text(strip=True)
            if self._looks_like_university_name(text):
                # Look for nearby links
                url = ""
                parent = strong.parent
                if parent:
                    link = parent.find('a', href=True)
                    if link:
                        url = urljoin(source_url, link.get('href', ''))
                
                confidence = self._calculate_academic_confidence(text, url, "")
                if confidence >= 0.5:
                    organizations.append(Organization(
                        name=text,
                        url=url,
                        org_type=self._determine_academic_org_type(text, url),
                        source_url=source_url,
                        confidence_score=confidence + 0.1,  # Bonus for being in article
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
        """Check if text looks like a university name"""
        text_lower = text.lower().strip()
        
        # Skip if too short or too long
        if len(text) < 5 or len(text) > 100:
            return False
        
        # Skip obvious non-university content
        skip_patterns = [
            r'^\d+\.$',  # Just numbers
            r'^(read more|learn more|see more|view more)$',
            r'^(click here|more info|website|homepage)$',
            r'^(about|contact|admissions|apply)$',
            r'(student|professor|dean) said',
            r'^(the|a|an)\s+\w+\s+(said|says|explained)',
            
            # Skip article titles and navigation
            r'^\d+\s+(cheapest|best|top|affordable)',  # "17 Cheapest...", "10 Best..."
            r'^(cheapest|best|top|affordable)\s+\d+',  # "Best 10...", "Cheapest 5..."
            r'privacy policy$',
            r'contact us$',
            r'^home$',
            r'^about us$',
            r'^menu$',
            r'leave a comment',
            r'cancel reply',
            r'previous post$',
            r'next post$',
            r'^read more',
            r'scholarships?\s+(in|for)',  # "Scholarships in Germany"
            r'^\d+\s+(scholarships?|programs?|courses?)',  # "5 Scholarships", "10 Programs"
            r'(free|fully|partially)\s+funded',
            r'^\d+.*\s+(tips|guide|ways|steps)',  # "10 Tips", "5 Ways"
            r'how to (get|write|apply)',
            r'step by step',
            r'statement of purpose',
            r'visa interview',
            r'summer school$',
            r'list of scholarships$'
        ]
        
        for pattern in skip_patterns:
            if re.search(pattern, text_lower):
                return False
        
        # Look for university indicators
        university_indicators = [
            r'\buniversity\b',
            r'\bcollege\b',
            r'\binstitute\b',
            r'\bschool\b',
            r'\bacademy\b',
            r'\btech\b',
            r'\bstate\b.*\buniversity\b',
            r'\buniversity\b.*\bof\b'
        ]
        
        has_university_indicator = any(re.search(pattern, text_lower) for pattern in university_indicators)
        
        # Also accept proper nouns that might be universities
        words = text.split()
        has_proper_nouns = len([w for w in words if w[0].isupper()]) >= 2
        
        return has_university_indicator or has_proper_nouns
    
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
        """Calculate confidence score for academic organizations"""
        confidence = 0.0
        name_lower = name.lower()
        url_lower = url.lower()
        desc_lower = description.lower()
        combined_text = f"{name_lower} {url_lower} {desc_lower}"
        
        # Strong academic indicators
        academic_keywords = [
            'university', 'college', 'institute', 'school', 'academy',
            'research', 'laboratory', 'academic', 'education',
            'scholarship', 'fellowship', 'grant', 'phd', 'doctorate'
        ]
        
        for keyword in academic_keywords:
            if keyword in combined_text:
                confidence += 0.3
                break
        
        # Domain bonuses
        if any(tld in url_lower for tld in ['.edu', '.ac.', '.university']):
            confidence += 0.4
        
        # Educational organization patterns
        if any(pattern in name_lower for pattern in ['university of', 'college of', 'institute of']):
            confidence += 0.3
        
        # Check proper capitalization (sign of organization name)
        words = name.split()
        capitalized_words = sum(1 for word in words if word[0].isupper() and len(word) > 2)
        if capitalized_words >= 2:
            confidence += 0.2
        
        # Exclude obvious non-organizations (enhanced patterns from original code)
        exclude_patterns = [
            r'^(home|about|contact|blog|news)$',
            r'^(privacy|terms|legal|cookies)$',
            r'^(facebook|twitter|linkedin|instagram)$',
            r'^\d+\s+(best|top|free)',
            r'^top\s+\d+',
            r'best\s+\d+\s+(universities|colleges|schools)',
            r'top\s+\d+\s+(universities|colleges|schools)',
            r'how to|tips|guide|tutorial',
            r'best.*universities.*in',
            r'top.*universities.*for',
            r'ranking.*universities',
            r'list.*of.*universities',
            r'complete.*guide.*to',
            r'everything.*you.*need.*to.*know',
            r'ultimate.*guide',
            r'\d+.*things.*to.*know',
            r'what.*you.*need.*to.*know'
        ]
        
        for pattern in exclude_patterns:
            if re.search(pattern, name_lower, re.IGNORECASE):
                confidence = 0.0
                break
        
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