#!/usr/bin/env python3
"""
Crawlee-inspired structured crawler for extracting academic institutions and organizations.
This provides more intelligent crawling with proper URL management and extraction patterns.
"""

import asyncio
import aiohttp
import json
import csv
import logging
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from dataclasses import dataclass, asdict
from typing import List, Dict, Set, Optional, Callable
import re
import time
from datetime import datetime
import hashlib

@dataclass
class CrawlRequest:
    url: str
    label: str = "DEFAULT"
    user_data: Dict = None
    headers: Dict = None
    priority: int = 0
    retries: int = 0
    max_retries: int = 3

@dataclass
class CrawlResult:
    url: str
    status_code: int
    html: str
    headers: Dict
    request: CrawlRequest
    timestamp: datetime

class RequestQueue:
    def __init__(self, max_size: int = 10000):
        self.queue: List[CrawlRequest] = []
        self.processed_urls: Set[str] = set()
        self.max_size = max_size
    
    def add_request(self, request: CrawlRequest) -> bool:
        """Add request to queue if not already processed and queue not full"""
        if request.url in self.processed_urls or len(self.queue) >= self.max_size:
            return False
        
        # Insert based on priority (higher priority first)
        inserted = False
        for i, existing_req in enumerate(self.queue):
            if request.priority > existing_req.priority:
                self.queue.insert(i, request)
                inserted = True
                break
        
        if not inserted:
            self.queue.append(request)
        
        return True
    
    def get_next_request(self) -> Optional[CrawlRequest]:
        """Get next request from queue"""
        if self.queue:
            request = self.queue.pop(0)
            self.processed_urls.add(request.url)
            return request
        return None
    
    def is_empty(self) -> bool:
        return len(self.queue) == 0
    
    def size(self) -> int:
        return len(self.queue)

class AcademicCrawler:
    def __init__(self, 
                 max_concurrent: int = 5,
                 request_delay: float = 1.0,
                 session_timeout: int = 30):
        self.max_concurrent = max_concurrent
        self.request_delay = request_delay
        self.session_timeout = session_timeout
        self.request_queue = RequestQueue()
        self.handlers: Dict[str, Callable] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        self.results: List[Dict] = []
        
        # Academic patterns for better detection
        self.academic_patterns = {
            'university_keywords': [
                r'\b(university|université|universidad|università|universiteit|universität)\b',
                r'\b(college|école|escuela|scuola)\b',
                r'\b(institute|institut|instituto|istituto)\b',
                r'\b(academy|académie|academia|accademia)\b'
            ],
            'academic_domains': [
                r'\.edu$', r'\.edu\.',
                r'\.ac\.', r'\.edu\.', 
                r'university\.', r'college\.',
                r'uni\.', r'univ\.'
            ],
            'department_patterns': [
                r'faculty\s+of', r'school\s+of', r'department\s+of',
                r'institute\s+of', r'center\s+for', r'centre\s+for'
            ]
        }
        
        self.exclude_patterns = [
            r'^(home|about|contact|blog)$',
            r'facebook\.com', r'twitter\.com', r'linkedin\.com',
            r'^\d+\s+(best|top|tips)', r'how\s+to'
        ]
    
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(limit=self.max_concurrent)
        timeout = aiohttp.ClientTimeout(total=self.session_timeout)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'AcademicCrawler/1.0 (+https://example.com/bot)'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def add_handler(self, label: str, handler: Callable):
        """Add a handler function for specific request labels"""
        self.handlers[label] = handler
    
    def add_requests(self, requests: List[CrawlRequest]):
        """Add multiple requests to the queue"""
        for request in requests:
            self.request_queue.add_request(request)
    
    def is_academic_url(self, url: str, text: str = "") -> bool:
        """Check if URL/text suggests academic content"""
        url_lower = url.lower()
        text_lower = text.lower()
        combined = f"{url_lower} {text_lower}"
        
        # Check for academic domain patterns
        for pattern in self.academic_patterns['academic_domains']:
            if re.search(pattern, url_lower):
                return True
        
        # Check for university keywords
        for pattern in self.academic_patterns['university_keywords']:
            if re.search(pattern, combined, re.IGNORECASE):
                return True
        
        return False
    
    def should_exclude(self, url: str, text: str = "") -> bool:
        """Check if URL/text should be excluded"""
        combined = f"{url.lower()} {text.lower()}"
        
        for pattern in self.exclude_patterns:
            if re.search(pattern, combined, re.IGNORECASE):
                return True
        
        return False
    
    async def fetch_page(self, request: CrawlRequest) -> Optional[CrawlResult]:
        """Fetch a single page"""
        if not self.session:
            raise RuntimeError("Crawler not properly initialized. Use 'async with' syntax.")
        
        try:
            headers = request.headers or {}
            async with self.session.get(request.url, headers=headers) as response:
                html = await response.text()
                return CrawlResult(
                    url=request.url,
                    status_code=response.status,
                    html=html,
                    headers=dict(response.headers),
                    request=request,
                    timestamp=datetime.now()
                )
        except Exception as e:
            logging.error(f"Failed to fetch {request.url}: {e}")
            if request.retries < request.max_retries:
                request.retries += 1
                self.request_queue.add_request(request)
            return None
    
    async def process_request(self, request: CrawlRequest):
        """Process a single request"""
        result = await self.fetch_page(request)
        if not result:
            return
        
        # Apply rate limiting
        await asyncio.sleep(self.request_delay)
        
        # Call appropriate handler
        handler = self.handlers.get(request.label, self.default_handler)
        await handler(result)
    
    async def default_handler(self, result: CrawlResult):
        """Default handler for processing crawl results"""
        soup = BeautifulSoup(result.html, 'html.parser')
        
        # Extract organizations from the page
        organizations = self.extract_organizations(soup, result.url)
        
        for org in organizations:
            self.results.append(org)
        
        # Find new URLs to crawl
        new_requests = self.extract_new_requests(soup, result.url, result.request.label)
        
        for new_request in new_requests:
            self.request_queue.add_request(new_request)
    
    def extract_organizations(self, soup: BeautifulSoup, source_url: str) -> List[Dict]:
        """Extract academic organizations from parsed HTML"""
        organizations = []
        
        # Extract from structured data
        orgs_from_structured = self.extract_from_json_ld(soup, source_url)
        organizations.extend(orgs_from_structured)
        
        # Extract from navigation and content links
        orgs_from_links = self.extract_from_links(soup, source_url)
        organizations.extend(orgs_from_links)
        
        # Extract from tables and lists
        orgs_from_tables = self.extract_from_tables_lists(soup, source_url)
        organizations.extend(orgs_from_tables)
        
        return organizations
    
    def extract_from_json_ld(self, soup: BeautifulSoup, source_url: str) -> List[Dict]:
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
                    
                    org_type = entry.get('@type', '')
                    if org_type in ["CollegeOrUniversity", "EducationalOrganization", "Organization"]:
                        name = entry.get('name')
                        url = entry.get('url')
                        
                        if name and url:
                            organizations.append({
                                'name': name,
                                'url': url,
                                'type': 'university' if 'University' in org_type else 'organization',
                                'source_url': source_url,
                                'extraction_method': 'structured_data',
                                'confidence': 0.9,
                                'description': entry.get('description', ''),
                                'location': entry.get('address', {}).get('addressLocality', '') if isinstance(entry.get('address'), dict) else ''
                            })
            except json.JSONDecodeError:
                continue
        
        return organizations
    
    def extract_from_links(self, soup: BeautifulSoup, source_url: str) -> List[Dict]:
        """Extract organizations from links"""
        organizations = []
        base_domain = urlparse(source_url).netloc
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').strip()
            text = link.get_text(strip=True)
            
            if not href or not text or len(text) < 3:
                continue
            
            # Convert to absolute URL
            full_url = urljoin(source_url, href)
            link_domain = urlparse(full_url).netloc
            
            # Skip same-domain navigation links
            if link_domain == base_domain:
                continue
            
            # Check if this looks like an academic organization
            if self.is_academic_url(full_url, text) and not self.should_exclude(full_url, text):
                confidence = self.calculate_academic_confidence(text, full_url)
                
                if confidence >= 0.5:
                    organizations.append({
                        'name': text,
                        'url': full_url,
                        'type': self.determine_org_type(text, full_url),
                        'source_url': source_url,
                        'extraction_method': 'link_analysis',
                        'confidence': confidence,
                        'description': self.get_link_context(link),
                        'location': ''
                    })
        
        return organizations
    
    def extract_from_tables_lists(self, soup: BeautifulSoup, source_url: str) -> List[Dict]:
        """Extract organizations from tables and lists"""
        organizations = []
        
        # Process tables
        for table in soup.find_all('table'):
            # Look for university/college listings in tables
            for row in table.find_all('tr'):
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 1:
                    for cell in cells:
                        links = cell.find_all('a', href=True)
                        for link in links:
                            text = link.get_text(strip=True)
                            href = urljoin(source_url, link.get('href', ''))
                            
                            if self.is_academic_url(href, text) and not self.should_exclude(href, text):
                                confidence = self.calculate_academic_confidence(text, href)
                                
                                if confidence >= 0.6:  # Higher threshold for table data
                                    organizations.append({
                                        'name': text,
                                        'url': href,
                                        'type': self.determine_org_type(text, href),
                                        'source_url': source_url,
                                        'extraction_method': 'table_extraction',
                                        'confidence': confidence,
                                        'description': cell.get_text(strip=True)[:200],
                                        'location': ''
                                    })
        
        # Process lists
        for ul in soup.find_all(['ul', 'ol']):
            for li in ul.find_all('li'):
                links = li.find_all('a', href=True)
                for link in links:
                    text = link.get_text(strip=True)
                    href = urljoin(source_url, link.get('href', ''))
                    
                    if self.is_academic_url(href, text) and not self.should_exclude(href, text):
                        confidence = self.calculate_academic_confidence(text, href)
                        
                        if confidence >= 0.6:
                            organizations.append({
                                'name': text,
                                'url': href,
                                'type': self.determine_org_type(text, href),
                                'source_url': source_url,
                                'extraction_method': 'list_extraction',
                                'confidence': confidence,
                                'description': li.get_text(strip=True)[:200],
                                'location': ''
                            })
        
        return organizations
    
    def calculate_academic_confidence(self, text: str, url: str) -> float:
        """Calculate confidence score for academic organization"""
        confidence = 0.0
        text_lower = text.lower()
        url_lower = url.lower()
        
        # University/college keywords
        university_keywords = ['university', 'college', 'institute', 'school', 'academy']
        for keyword in university_keywords:
            if keyword in text_lower:
                confidence += 0.3
            if keyword in url_lower:
                confidence += 0.2
        
        # Academic domain
        if any(domain in url_lower for domain in ['.edu', '.ac.']):
            confidence += 0.4
        
        # Proper name structure (capitalized words)
        words = text.split()
        if len(words) >= 2 and sum(1 for word in words if word[0].isupper()) >= 2:
            confidence += 0.2
        
        # Academic context keywords
        academic_context = ['research', 'faculty', 'department', 'phd', 'graduate']
        if any(keyword in text_lower for keyword in academic_context):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def determine_org_type(self, text: str, url: str) -> str:
        """Determine organization type"""
        text_lower = text.lower()
        url_lower = url.lower()
        
        if 'university' in text_lower or 'university' in url_lower:
            return 'university'
        elif 'college' in text_lower or 'college' in url_lower:
            return 'college'
        elif 'institute' in text_lower or 'institute' in url_lower:
            return 'institute'
        elif 'school' in text_lower or 'school' in url_lower:
            return 'school'
        elif 'academy' in text_lower or 'academy' in url_lower:
            return 'academy'
        else:
            return 'organization'
    
    def get_link_context(self, link) -> str:
        """Get context around a link"""
        context_parts = []
        
        # Get text from parent elements
        for parent in [link.parent, link.parent.parent if link.parent else None]:
            if parent:
                text = parent.get_text(strip=True)
                if text and len(text) < 300:
                    context_parts.append(text)
        
        return " ".join(context_parts)
    
    def extract_new_requests(self, soup: BeautifulSoup, source_url: str, current_label: str) -> List[CrawlRequest]:
        """Extract new URLs to crawl"""
        new_requests = []
        
        # Find university directory/listing pages
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            text = link.get_text(strip=True).lower()
            
            # Look for university directory pages
            if any(keyword in text for keyword in ['universities', 'colleges', 'directory', 'list of']):
                full_url = urljoin(source_url, href)
                if self.is_valid_crawl_url(full_url):
                    new_requests.append(CrawlRequest(
                        url=full_url,
                        label='UNIVERSITY_DIRECTORY',
                        priority=5  # High priority for directory pages
                    ))
        
        return new_requests
    
    def is_valid_crawl_url(self, url: str) -> bool:
        """Check if URL is valid for crawling"""
        parsed = urlparse(url)
        
        # Must have valid scheme and netloc
        if not parsed.scheme or not parsed.netloc:
            return False
        
        # Skip certain file types
        skip_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.png', '.gif', '.zip']
        if any(url.lower().endswith(ext) for ext in skip_extensions):
            return False
        
        # Skip social media
        social_domains = ['facebook.com', 'twitter.com', 'linkedin.com', 'instagram.com']
        if any(domain in parsed.netloc for domain in social_domains):
            return False
        
        return True
    
    async def run(self, max_requests: int = 100):
        """Run the crawler"""
        processed_count = 0
        
        while not self.request_queue.is_empty() and processed_count < max_requests:
            # Process requests concurrently
            tasks = []
            for _ in range(min(self.max_concurrent, self.request_queue.size())):
                request = self.request_queue.get_next_request()
                if request:
                    task = asyncio.create_task(self.process_request(request))
                    tasks.append(task)
                    processed_count += 1
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            
            logging.info(f"Processed {processed_count} requests, {self.request_queue.size()} remaining in queue")
    
    def save_results(self, filename: str = "crawled_organizations.csv"):
        """Save results to CSV file"""
        if not self.results:
            logging.warning("No results to save")
            return
        
        # Remove duplicates
        unique_results = {}
        for result in self.results:
            key = f"{result['name'].lower()}|{result['url']}"
            if key not in unique_results or result['confidence'] > unique_results[key]['confidence']:
                unique_results[key] = result
        
        # Sort by confidence
        sorted_results = sorted(unique_results.values(), key=lambda x: x['confidence'], reverse=True)
        
        # Save to CSV
        fieldnames = ['name', 'url', 'type', 'source_url', 'extraction_method', 
                     'confidence', 'description', 'location']
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for result in sorted_results:
                writer.writerow(result)
        
        logging.info(f"Saved {len(sorted_results)} unique organizations to {filename}")

async def main():
    """Main function for running the crawler"""
    
    # Initial seed URLs for academic content
    seed_urls = [
        "https://www.topuniversities.com/universities",
        "https://www.timeshighereducation.com/world-university-rankings",
        "https://www.uni.lu/en/",
        "https://studyabroad.shiksha.com/universities-in-luxembourg",
        "https://www.educations.com/countries/luxembourg/institutions",
    ]
    
    # Create initial requests
    initial_requests = [
        CrawlRequest(url=url, label="UNIVERSITY_DIRECTORY", priority=10)
        for url in seed_urls
    ]
    
    async with AcademicCrawler(max_concurrent=3, request_delay=2.0) as crawler:
        # Add custom handler for university directory pages
        async def university_directory_handler(result: CrawlResult):
            await crawler.default_handler(result)
            logging.info(f"Processed university directory: {result.url}")
        
        crawler.add_handler("UNIVERSITY_DIRECTORY", university_directory_handler)
        
        # Add initial requests
        crawler.add_requests(initial_requests)
        
        # Run crawler
        await crawler.run(max_requests=50)  # Limit for testing
        
        # Save results
        crawler.save_results("academic_organizations.csv")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    asyncio.run(main()) 