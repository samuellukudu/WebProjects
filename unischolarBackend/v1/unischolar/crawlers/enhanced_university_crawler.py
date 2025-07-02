"""
Enhanced University Crawler - Specialized for University Discovery

This crawler is optimized specifically for finding and extracting university names from:
- Educational directories and ranking sites
- University listing pages
- Academic association websites
- Government education portals
- International education databases
"""

import logging
import re
import time
from typing import List, Dict, Set, Optional, Tuple
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import requests
from dataclasses import dataclass, field

from .base import BaseCrawler
from ..extractors.university_name_extractor import UniversityNameExtractor, UniversityName
from ..core.models import Organization
from ..core.config import get_config


@dataclass
class UniversityDiscoveryResult:
    """Results from university discovery crawling"""
    universities: List[UniversityName] = field(default_factory=list)
    source_urls: List[str] = field(default_factory=list)
    discovery_methods: Dict[str, int] = field(default_factory=dict)
    total_sources_crawled: int = 0
    high_confidence_count: int = 0
    verified_count: int = 0


class EnhancedUniversityCrawler(BaseCrawler):
    """Specialized crawler for university discovery and name extraction"""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.university_extractor = UniversityNameExtractor(config)
        self.config = get_config()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # University-rich source types
        self.university_source_types = {
            'ranking_sites': [
                'timeshighereducation.com', 'topuniversities.com', 'usnews.com',
                'shanghairanking.com', 'webometrics.info', 'uniranks.com',
                'studyportals.com', 'educations.com', 'mastersportal.com'
            ],
            'government_portals': [
                '.gov', '.edu', '.ac.', 'education.gov', 'studyinaustralia.gov.au',
                'study.eu', 'campusfrance.org', 'daad.de', 'britishcouncil.org'
            ],
            'educational_directories': [
                'petersons.com', 'collegenavigator.gov', 'commonapp.org',
                'admissions.university', 'universitiesuk.ac.uk', 'aau.edu',
                'aplu.org', 'nces.ed.gov', 'college-insight.org'
            ],
            'international_databases': [
                'whed.net', 'iau-aiu.net', 'unesco.org', 'enic-naric.net',
                'eurydice.eacea.ec.europa.eu', 'eua.eu', 'apru.org'
            ]
        }
        
        # Enhanced patterns for university-specific content
        self.university_content_patterns = {
            'list_indicators': [
                r'(?:top|best|ranking|list)\s+(?:\d+\s+)?universities',
                r'universities\s+(?:in|by|ranking|list)',
                r'college\s+(?:directory|guide|list|ranking)',
                r'higher\s+education\s+institutions',
                r'academic\s+institutions\s+(?:in|by)',
                r'university\s+profiles?\s+(?:in|by)',
            ],
            'directory_indicators': [
                r'university\s+search',
                r'find\s+(?:universities|colleges)',
                r'institution\s+(?:directory|database|search)',
                r'college\s+finder',
                r'university\s+(?:browser|explorer|portal)',
            ],
            'official_indicators': [
                r'accredited\s+(?:universities|institutions)',
                r'recognized\s+(?:universities|institutions)',
                r'ministry\s+of\s+education',
                r'department\s+of\s+education',
                r'higher\s+education\s+(?:commission|authority)',
            ]
        }
        
        # University list page patterns
        self.university_list_selectors = [
            # Common list structures
            'ul li a[href*="university"]',
            'ul li a[href*="college"]',
            'ol li a[href*="edu"]',
            'div[class*="university"] a',
            'div[class*="college"] a',
            'div[class*="institution"] a',
            
            # Table structures
            'table tr td a[href*="university"]',
            'table tr td a[href*="college"]',
            'tbody tr td a[href*="edu"]',
            
            # Card/grid structures
            'div[class*="card"] a[href*="university"]',
            'div[class*="item"] a[href*="university"]',
            'div[class*="result"] a[href*="university"]',
            
            # Ranking/directory specific
            'div[class*="ranking"] a',
            'div[class*="directory"] a',
            'div[class*="profile"] a[href*="university"]',
        ]
        
        # High-quality source domains
        self.high_quality_domains = {
            'government': ['.gov', '.edu', '.ac.'],
            'official_orgs': [
                'unesco.org', 'iau-aiu.net', 'whed.net', 'enic-naric.net',
                'eua.eu', 'apru.org', 'universitas21.com'
            ],
            'established_rankings': [
                'timeshighereducation.com', 'topuniversities.com',
                'usnews.com', 'shanghairanking.com', 'webometrics.info'
            ]
        }
    
    def crawl(self, search_results: List[Dict], target_country: Optional[str] = None) -> UniversityDiscoveryResult:
        """
        Main crawling method required by BaseCrawler.
        
        Args:
            search_results: List of search result dictionaries
            target_country: Optional country filter for targeted discovery
            
        Returns:
            UniversityDiscoveryResult containing discovered universities
        """
        return self.discover_universities(search_results, target_country)
    
    def discover_universities(self, search_results: List[Dict], target_country: Optional[str] = None) -> UniversityDiscoveryResult:
        """Main method to discover universities from search results"""
        result = UniversityDiscoveryResult()
        
        # Phase 1: Prioritize and filter sources
        prioritized_sources = self._prioritize_university_sources(search_results)
        
        # Phase 2: Extract universities from prioritized sources
        for source_info in prioritized_sources:
            try:
                url = source_info['url']
                self.logger.info(f"🎯 Crawling university source: {url}")
                
                soup = self.fetch_url(url)
                if soup:
                    # Extract universities using multiple methods
                    universities = self._extract_universities_comprehensive(soup, url, target_country)
                    result.universities.extend(universities)
                    result.source_urls.append(url)
                    result.total_sources_crawled += 1
                    
                    # Track extraction methods
                    for uni in universities:
                        method = uni.extraction_method
                        result.discovery_methods[method] = result.discovery_methods.get(method, 0) + 1
                    
                    self.logger.info(f"📊 Found {len(universities)} universities from {url}")
                    
                    # Respectful crawling delay
                    time.sleep(self.config.get('search_delay', 2))
                
            except Exception as e:
                self.logger.error(f"Error crawling {source_info['url']}: {e}")
                continue
        
        # Phase 3: Post-process results
        result = self._post_process_discovery_results(result)
        
        self.logger.info(f"🎉 University Discovery Complete: {len(result.universities)} total, "
                        f"{result.high_confidence_count} high-confidence, "
                        f"{result.verified_count} verified")
        
        return result
    
    def _prioritize_university_sources(self, search_results: List[Dict]) -> List[Dict]:
        """Prioritize sources based on their likelihood to contain university lists"""
        scored_sources = []
        
        for result in search_results:
            url = result.get('url', '')
            title = result.get('title', '').lower()
            abstract = result.get('abstract', '').lower()
            
            score = 0.0
            source_type = 'general'
            
            # Score based on domain quality
            domain_score, domain_type = self._score_domain_quality(url)
            score += domain_score
            if domain_type != 'general':
                source_type = domain_type
            
            # Score based on content indicators
            content_score, content_type = self._score_content_indicators(title, abstract)
            score += content_score
            if content_type != 'general':
                source_type = content_type
            
            # Score based on URL patterns
            url_score = self._score_url_patterns(url)
            score += url_score
            
            scored_sources.append({
                'url': url,
                'title': result.get('title', ''),
                'score': score,
                'source_type': source_type,
                'original_result': result
            })
        
        # Sort by score (highest first) and return top sources
        scored_sources.sort(key=lambda x: x['score'], reverse=True)
        
        # Take top sources but ensure diversity
        max_sources = self.config.get('max_university_sources', 20)
        prioritized = self._ensure_source_diversity(scored_sources[:max_sources * 2])[:max_sources]
        
        self.logger.info(f"🔍 Prioritized {len(prioritized)} university sources from {len(search_results)} search results")
        return prioritized
    
    def _score_domain_quality(self, url: str) -> Tuple[float, str]:
        """Score URL based on domain quality for university content"""
        score = 0.0
        source_type = 'general'
        url_lower = url.lower()
        
        # Government and educational domains (highest priority)
        for domain in self.high_quality_domains['government']:
            if domain in url_lower:
                return 1.0, 'government'
        
        # Official organizations
        for domain in self.high_quality_domains['official_orgs']:
            if domain in url_lower:
                return 0.9, 'official_org'
        
        # Established ranking sites
        for domain in self.high_quality_domains['established_rankings']:
            if domain in url_lower:
                return 0.8, 'ranking_site'
        
        # Educational directories
        for domain in self.university_source_types['educational_directories']:
            if domain in url_lower:
                score = max(score, 0.7)
                source_type = 'directory'
        
        # International databases
        for domain in self.university_source_types['international_databases']:
            if domain in url_lower:
                score = max(score, 0.6)
                source_type = 'database'
        
        return score, source_type
    
    def _score_content_indicators(self, title: str, abstract: str) -> Tuple[float, str]:
        """Score content based on university-specific indicators"""
        content = f"{title} {abstract}".lower()
        score = 0.0
        content_type = 'general'
        
        # List indicators
        for pattern in self.university_content_patterns['list_indicators']:
            if re.search(pattern, content):
                score = max(score, 0.8)
                content_type = 'university_list'
        
        # Directory indicators
        for pattern in self.university_content_patterns['directory_indicators']:
            if re.search(pattern, content):
                score = max(score, 0.7)
                content_type = 'directory'
        
        # Official indicators
        for pattern in self.university_content_patterns['official_indicators']:
            if re.search(pattern, content):
                score = max(score, 0.9)
                content_type = 'official'
        
        # Additional keyword scoring
        university_keywords = ['university', 'college', 'institution', 'higher education']
        keyword_count = sum(1 for keyword in university_keywords if keyword in content)
        score += min(keyword_count * 0.1, 0.3)
        
        return score, content_type
    
    def _score_url_patterns(self, url: str) -> float:
        """Score URL based on university-related patterns"""
        score = 0.0
        url_lower = url.lower()
        
        # University-specific paths
        university_paths = [
            'university', 'college', 'institution', 'education',
            'academic', 'higher-ed', 'universities', 'colleges'
        ]
        
        for path in university_paths:
            if path in url_lower:
                score += 0.1
        
        # List/directory paths
        list_paths = ['list', 'directory', 'ranking', 'search', 'database', 'portal']
        for path in list_paths:
            if path in url_lower:
                score += 0.05
        
        return min(score, 0.5)  # Cap at 0.5
    
    def _ensure_source_diversity(self, sources: List[Dict]) -> List[Dict]:
        """Ensure diversity in source types and domains"""
        diverse_sources = []
        domain_counts = {}
        type_counts = {}
        
        for source in sources:
            domain = urlparse(source['url']).netloc
            source_type = source['source_type']
            
            # Limit sources per domain
            max_per_domain = 3
            if domain_counts.get(domain, 0) >= max_per_domain:
                continue
            
            # Ensure type diversity
            max_per_type = 8
            if type_counts.get(source_type, 0) >= max_per_type:
                continue
            
            diverse_sources.append(source)
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
            type_counts[source_type] = type_counts.get(source_type, 0) + 1
        
        return diverse_sources
    
    def _extract_universities_comprehensive(self, soup: BeautifulSoup, source_url: str, 
                                          target_country: Optional[str] = None) -> List[UniversityName]:
        """Extract universities using multiple comprehensive methods"""
        all_universities = []
        
        # Method 1: Use the advanced university name extractor
        extracted_names = self.university_extractor.extract_university_names(soup, source_url)
        all_universities.extend(extracted_names)
        
        # Method 2: Enhanced list extraction
        list_universities = self._extract_from_university_lists(soup, source_url)
        all_universities.extend(list_universities)
        
        # Method 3: Table-based extraction
        table_universities = self._extract_from_tables(soup, source_url)
        all_universities.extend(table_universities)
        
        # Method 4: Link pattern extraction
        link_universities = self._extract_from_link_patterns(soup, source_url)
        all_universities.extend(link_universities)
        
        # Method 5: Heading-based extraction
        heading_universities = self._extract_from_headings(soup, source_url)
        all_universities.extend(heading_universities)
        
        # Filter by target country if specified
        if target_country:
            all_universities = self._filter_by_country(all_universities, target_country)
        
        # Deduplicate within this source
        deduplicated = self._deduplicate_within_source(all_universities)
        
        return deduplicated
    
    def _extract_from_university_lists(self, soup: BeautifulSoup, source_url: str) -> List[UniversityName]:
        """Extract universities from structured lists"""
        universities = []
        
        for selector in self.university_list_selectors:
            try:
                links = soup.select(selector)
                
                for link in links:
                    text = link.get_text(strip=True)
                    href = link.get('href', '')
                    
                    if text and self._looks_like_university_name(text):
                        cleaned_name = self._clean_university_name_strict(text)
                        if cleaned_name:
                            full_url = urljoin(source_url, href) if href else None
                            
                            universities.append(UniversityName(
                                name=cleaned_name,
                                confidence=0.85,
                                source_url=source_url,
                                extraction_method='list_extraction',
                                official_url=full_url,
                                quality_score=self._calculate_list_quality(text, href)
                            ))
            except Exception as e:
                self.logger.debug(f"Error with selector {selector}: {e}")
                continue
        
        return universities
    
    def _extract_from_tables(self, soup: BeautifulSoup, source_url: str) -> List[UniversityName]:
        """Extract universities from table structures"""
        universities = []
        
        # Find tables that might contain university listings
        university_tables = soup.find_all('table')
        
        for table in university_tables:
            rows = table.find_all('tr')
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                
                for cell in cells:
                    # Look for university names in cells
                    text = cell.get_text(strip=True)
                    if text and self._looks_like_university_name(text):
                        cleaned_name = self._clean_university_name_strict(text)
                        if cleaned_name:
                            # Look for associated link
                            link = cell.find('a')
                            official_url = urljoin(source_url, link.get('href', '')) if link else None
                            
                            universities.append(UniversityName(
                                name=cleaned_name,
                                confidence=0.8,
                                source_url=source_url,
                                extraction_method='table_extraction',
                                official_url=official_url,
                                quality_score=self._calculate_table_quality(text, cell)
                            ))
        
        return universities
    
    def _extract_from_link_patterns(self, soup: BeautifulSoup, source_url: str) -> List[UniversityName]:
        """Extract universities using link pattern analysis"""
        universities = []
        
        # Find all links that might point to universities
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # Check if URL or text suggests a university
            if self._is_university_link(href, text):
                # Prefer text if it looks like a university name
                if text and self._looks_like_university_name(text):
                    cleaned_name = self._clean_university_name_strict(text)
                else:
                    # Try to extract name from URL
                    cleaned_name = self._extract_name_from_university_url(href)
                
                if cleaned_name:
                    full_url = urljoin(source_url, href)
                    
                    universities.append(UniversityName(
                        name=cleaned_name,
                        confidence=0.75,
                        source_url=source_url,
                        extraction_method='link_pattern',
                        official_url=full_url,
                        quality_score=self._calculate_link_quality(href, text)
                    ))
        
        return universities
    
    def _extract_from_headings(self, soup: BeautifulSoup, source_url: str) -> List[UniversityName]:
        """Extract universities from heading elements"""
        universities = []
        
        # Check all heading levels
        for level in range(1, 7):
            headings = soup.find_all(f'h{level}')
            
            for heading in headings:
                text = heading.get_text(strip=True)
                
                if text and self._looks_like_university_name(text):
                    cleaned_name = self._clean_university_name_strict(text)
                    if cleaned_name:
                        # Look for associated link in or near the heading
                        link = heading.find('a') or heading.find_next('a')
                        official_url = urljoin(source_url, link.get('href', '')) if link else None
                        
                        universities.append(UniversityName(
                            name=cleaned_name,
                            confidence=0.7,
                            source_url=source_url,
                            extraction_method='heading_extraction',
                            official_url=official_url,
                            quality_score=self._calculate_heading_quality(text, level)
                        ))
        
        return universities
    
    def _looks_like_university_name(self, text: str) -> bool:
        """Enhanced check if text looks like a university name"""
        if not text or len(text.strip()) < 3:
            return False
        
        text_lower = text.lower().strip()
        
        # Must contain university indicators
        university_indicators = [
            'university', 'college', 'institute', 'school',
            'université', 'universidad', 'università', 'universität'
        ]
        
        has_indicator = any(indicator in text_lower for indicator in university_indicators)
        if not has_indicator:
            return False
        
        # Exclude obvious non-university content
        exclusions = [
            r'^(?:best|top|cheapest|most)', r'\?', r'^(?:what|how|why)',
            r'(?:guide|tips|steps)', r'(?:admission|application)',
            r'for international students', r'without ielts'
        ]
        
        for exclusion in exclusions:
            if re.search(exclusion, text_lower):
                return False
        
        # Must have proper capitalization
        words = text.split()
        if len(words) >= 2:
            capitalized = sum(1 for word in words if word and word[0].isupper())
            if capitalized < len(words) * 0.5:
                return False
        
        return True
    
    def _clean_university_name_strict(self, name: str) -> str:
        """Strict cleaning for university names"""
        if not name:
            return ""
        
        # Use the university extractor's cleaning method
        return self.university_extractor._clean_university_name(name)
    
    def _is_university_link(self, href: str, text: str) -> bool:
        """Check if a link appears to point to a university"""
        href_lower = href.lower()
        text_lower = text.lower()
        
        # Educational domains
        edu_domains = ['.edu', '.ac.', 'university.', 'college.']
        if any(domain in href_lower for domain in edu_domains):
            return True
        
        # University keywords in URL
        url_keywords = ['university', 'college', 'institute', 'academic']
        if any(keyword in href_lower for keyword in url_keywords):
            return True
        
        # University keywords in link text
        if any(keyword in text_lower for keyword in ['university', 'college', 'institute']):
            return True
        
        return False
    
    def _extract_name_from_university_url(self, url: str) -> str:
        """Extract university name from URL"""
        if not url:
            return ""
        
        # Use the university extractor's method
        return self.university_extractor._extract_name_from_url(url)
    
    def _calculate_list_quality(self, text: str, href: str) -> float:
        """Calculate quality score for list-extracted universities"""
        quality = 0.6  # Base score
        
        # Length and structure
        if 10 <= len(text) <= 80:
            quality += 0.2
        
        # Link quality
        if href and self._is_university_link(href, text):
            quality += 0.2
        
        return min(quality, 1.0)
    
    def _calculate_table_quality(self, text: str, cell) -> float:
        """Calculate quality score for table-extracted universities"""
        quality = 0.5  # Base score
        
        # Context from table headers
        table = cell.find_parent('table')
        if table:
            headers = table.find_all(['th', 'tr'])
            header_text = ' '.join(h.get_text().lower() for h in headers)
            if any(word in header_text for word in ['university', 'institution', 'college']):
                quality += 0.3
        
        return min(quality, 1.0)
    
    def _calculate_heading_quality(self, text: str, level: int) -> float:
        """Calculate quality score for heading-extracted universities"""
        quality = 0.4  # Base score
        
        # Higher level headings are more reliable
        quality += (6 - level) * 0.1
        
        return min(quality, 1.0)
    
    def _calculate_link_quality(self, href: str, text: str) -> float:
        """Calculate quality score for link-extracted universities"""
        quality = 0.3  # Base score
        
        # Educational domain bonus
        if any(domain in href.lower() for domain in ['.edu', '.ac.']):
            quality += 0.4
        
        # Text quality
        if text and self._looks_like_university_name(text):
            quality += 0.3
        
        return min(quality, 1.0)
    
    def _filter_by_country(self, universities: List[UniversityName], target_country: str) -> List[UniversityName]:
        """Filter universities by target country"""
        # This is a simplified implementation - could be enhanced with country detection
        country_keywords = {
            'norway': ['norway', 'norwegian', 'oslo', 'bergen', 'trondheim'],
            'germany': ['germany', 'german', 'berlin', 'munich', 'hamburg'],
            'usa': ['usa', 'america', 'american', 'california', 'texas', 'new york'],
            'uk': ['uk', 'britain', 'british', 'england', 'scotland', 'london'],
            'canada': ['canada', 'canadian', 'toronto', 'vancouver', 'montreal'],
        }
        
        target_keywords = country_keywords.get(target_country.lower(), [])
        if not target_keywords:
            return universities
        
        filtered = []
        for uni in universities:
            # Check if university name or URL contains country indicators
            combined_text = f"{uni.name} {uni.source_url} {uni.official_url or ''}".lower()
            if any(keyword in combined_text for keyword in target_keywords):
                uni.country = target_country
                filtered.append(uni)
        
        return filtered
    
    def _deduplicate_within_source(self, universities: List[UniversityName]) -> List[UniversityName]:
        """Deduplicate universities within a single source"""
        seen_names = set()
        deduplicated = []
        
        # Sort by confidence first
        universities.sort(key=lambda x: x.confidence, reverse=True)
        
        for uni in universities:
            # Normalize name for comparison
            normalized = re.sub(r'[^\w\s]', '', uni.name.lower())
            normalized = re.sub(r'\s+', ' ', normalized).strip()
            
            if normalized not in seen_names:
                seen_names.add(normalized)
                deduplicated.append(uni)
        
        return deduplicated
    
    def _post_process_discovery_results(self, result: UniversityDiscoveryResult) -> UniversityDiscoveryResult:
        """Post-process discovery results for final cleanup and stats"""
        # Global deduplication across all sources
        result.universities = self._global_deduplicate_universities(result.universities)
        
        # Calculate statistics
        for uni in result.universities:
            if uni.confidence >= 0.8:
                result.high_confidence_count += 1
            if uni.is_verified:
                result.verified_count += 1
        
        # Sort by confidence + quality
        result.universities.sort(key=lambda x: (x.confidence + x.quality_score), reverse=True)
        
        return result
    
    def _global_deduplicate_universities(self, universities: List[UniversityName]) -> List[UniversityName]:
        """Global deduplication across all sources"""
        name_groups = {}
        
        for uni in universities:
            # Create a normalized key
            normalized = re.sub(r'[^\w\s]', '', uni.name.lower())
            normalized = re.sub(r'\b(?:the|university|college|institute)\b', '', normalized)
            normalized = re.sub(r'\s+', ' ', normalized).strip()
            
            if normalized not in name_groups:
                name_groups[normalized] = []
            name_groups[normalized].append(uni)
        
        # Select the best representative from each group
        final_universities = []
        for group in name_groups.values():
            # Sort by confidence + quality + method priority
            method_priority = {
                'structured_data': 1.0, 'ner': 0.9, 'list_extraction': 0.8,
                'table_extraction': 0.7, 'link_pattern': 0.6, 'heading_extraction': 0.5
            }
            
            group.sort(key=lambda x: (
                x.confidence + x.quality_score + method_priority.get(x.extraction_method, 0.0)
            ), reverse=True)
            
            best = group[0]
            
            # Collect variants and additional info from other entries
            variants = []
            for other in group[1:]:
                if other.name != best.name:
                    variants.append(other.name)
                if not best.official_url and other.official_url:
                    best.official_url = other.official_url
            
            best.name_variants = variants
            final_universities.append(best)
        
        return final_universities
    
    def convert_to_organizations(self, universities: List[UniversityName]) -> List[Organization]:
        """Convert UniversityName objects to Organization objects for compatibility"""
        organizations = []
        
        for uni in universities:
            org = Organization(
                name=uni.name,
                url=uni.official_url or uni.source_url,
                org_type='university',
                source_url=uni.source_url,
                confidence_score=uni.confidence,
                extraction_method=uni.extraction_method,
                description=f"University discovered via {uni.extraction_method}"
            )
            organizations.append(org)
        
        return organizations 