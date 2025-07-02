"""
Post-processing module for cleaning and validating organization data.
Implements feature 10 from plan.md: Data Enrichment and Post-Processing
"""

import pandas as pd
import re
import logging
import json
import requests
import time
from typing import List, Dict, Tuple, Set
from urllib.parse import urlparse, urljoin
import spacy
from dataclasses import dataclass
from collections import Counter
from bs4 import BeautifulSoup

# Load spaCy model for NLP processing
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logging.warning("spaCy English model not found. Install with: python -m spacy download en_core_web_sm")
    nlp = None

@dataclass
class ProcessingRule:
    name: str
    pattern: str
    action: str  # 'exclude', 'reclassify', 'normalize'
    category: str = 'generic'

@dataclass
class HomepageValidation:
    url: str
    is_organization: bool
    confidence_score: float
    organization_type: str
    reason: str
    homepage_title: str = ""
    description: str = ""

class HomepageValidator:
    """Validates homepages to determine if they represent real organizations."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Organization indicators in homepage content
        self.organization_indicators = {
            'university': ['university', 'college', 'institute', 'school', 'academic', 'education', 'phd', 'research'],
            'company': ['company', 'corporation', 'inc', 'ltd', 'llc', 'business', 'enterprise', 'solutions'],
            'research_center': ['research', 'laboratory', 'institute', 'center', 'centre', 'foundation', 'think tank'],
            'government': ['government', 'ministry', 'department', 'agency', 'bureau', 'administration'],
            'nonprofit': ['nonprofit', 'foundation', 'charity', 'organization', 'association', 'society']
        }
        
        # Non-organization indicators
        self.non_organization_indicators = [
            'blog', 'news', 'article', 'post', 'forum', 'discussion', 'social media',
            'marketplace', 'shopping', 'e-commerce', 'personal website', 'portfolio',
            'tutorial', 'guide', 'how-to', 'tips', 'advice', 'review'
        ]
    
    def extract_homepage_url(self, url: str) -> str:
        """Extract the homepage URL from any URL."""
        try:
            parsed = urlparse(url)
            if parsed.scheme and parsed.netloc:
                return f"{parsed.scheme}://{parsed.netloc}/"
            return url
        except Exception as e:
            logging.warning(f"Failed to parse URL {url}: {e}")
            return url
    
    def validate_homepage(self, homepage_url: str) -> HomepageValidation:
        """Validate if a homepage represents a real organization."""
        try:
            # Make request with timeout and retries
            for attempt in range(3):
                try:
                    response = self.session.get(homepage_url, timeout=10, allow_redirects=True)
                    if response.status_code == 200:
                        break
                    time.sleep(1)
                except requests.RequestException as e:
                    if attempt == 2:  # Last attempt
                        return HomepageValidation(
                            url=homepage_url,
                            is_organization=False,
                            confidence_score=0.0,
                            organization_type='unknown',
                            reason=f"Failed to access homepage: {str(e)}"
                        )
                    time.sleep(2)
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title and description
            title = soup.find('title')
            title_text = title.get_text().strip() if title else ""
            
            description = soup.find('meta', attrs={'name': 'description'})
            desc_text = description.get('content', '') if description else ""
            
            # Get main content text
            content_text = self._extract_main_content(soup)
            
            # Analyze content for organization indicators
            analysis = self._analyze_content(title_text, desc_text, content_text, homepage_url)
            
            return HomepageValidation(
                url=homepage_url,
                is_organization=analysis['is_organization'],
                confidence_score=analysis['confidence_score'],
                organization_type=analysis['organization_type'],
                reason=analysis['reason'],
                homepage_title=title_text,
                description=desc_text
            )
            
        except Exception as e:
            logging.error(f"Error validating homepage {homepage_url}: {e}")
            return HomepageValidation(
                url=homepage_url,
                is_organization=False,
                confidence_score=0.0,
                organization_type='unknown',
                reason=f"Validation error: {str(e)}"
            )
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content text from HTML."""
        # Remove script, style, and other non-content elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            element.decompose()
        
        # Get main content areas
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile('content|main'))
        if main_content:
            text = main_content.get_text()
        else:
            text = soup.get_text()
        
        # Clean and limit text
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:2000]  # Limit to first 2000 characters
    
    def _analyze_content(self, title: str, description: str, content: str, url: str) -> Dict:
        """Analyze content to determine if it represents an organization."""
        combined_text = f"{title} {description} {content}".lower()
        
        # Check for non-organization indicators first
        non_org_score = 0
        for indicator in self.non_organization_indicators:
            if indicator in combined_text:
                non_org_score += 1
        
        if non_org_score >= 2:
            return {
                'is_organization': False,
                'confidence_score': 0.1,
                'organization_type': 'non_organization',
                'reason': f"Contains {non_org_score} non-organization indicators"
            }
        
        # Check for organization indicators
        org_scores = {}
        for org_type, indicators in self.organization_indicators.items():
            score = 0
            for indicator in indicators:
                if indicator in combined_text:
                    score += 1
            org_scores[org_type] = score
        
        # Find best matching organization type
        best_type = max(org_scores, key=org_scores.get)
        best_score = org_scores[best_type]
        
        # Additional scoring factors
        bonus_score = 0
        
        # Domain-based scoring
        domain = urlparse(url).netloc.lower()
        if any(tld in domain for tld in ['.edu', '.ac.', '.uni-', '.university']):
            bonus_score += 2
            if best_type != 'university':
                best_type = 'university'
        
        if any(indicator in domain for indicator in ['research', 'institute', 'lab', 'center']):
            bonus_score += 1
        
        # Title-based scoring
        if any(word in title.lower() for word in ['university', 'institute', 'research', 'center', 'company']):
            bonus_score += 1
        
        # About page detection
        if any(phrase in combined_text for phrase in ['about us', 'our mission', 'our vision', 'founded in']):
            bonus_score += 1
        
        # Contact information detection
        if any(phrase in combined_text for phrase in ['contact us', 'email', 'phone', 'address']):
            bonus_score += 0.5
        
        final_score = best_score + bonus_score
        
        # Determine if it's an organization based on score
        is_organization = final_score >= 2.0
        confidence_score = min(final_score / 5.0, 1.0)  # Normalize to 0-1
        
        return {
            'is_organization': is_organization,
            'confidence_score': confidence_score,
            'organization_type': best_type if is_organization else 'non_organization',
            'reason': f"Score: {final_score:.1f}, indicators for {best_type}: {best_score}, bonus: {bonus_score}"
        }

class DataPostProcessor:
    """Enhanced post-processor with homepage validation."""
    
    def __init__(self):
        self.setup_logging()
        self.homepage_validator = HomepageValidator()
        
        # Define processing rules for content classification
        self.processing_rules = [
            # Blog posts and numbered content
            ProcessingRule("blog_posts", r'\d+\s+(postdoctoral|phd|fellowship|scholarship|position)s?\s+at\s+', 'reclassify', 'blog_posts'),
            ProcessingRule("numbered_content", r'^\d+\s+(best|top|leading)', 'reclassify', 'blog_posts'),
            
            # Social media and sharing
            ProcessingRule("social_media", r'(facebook|twitter|linkedin|instagram|youtube|telegram|whatsapp)', 'reclassify', 'social_media'),
            ProcessingRule("social_sharing", r'click to share|share on|follow us', 'reclassify', 'social_media'),
            
            # Marketing and navigation
            ProcessingRule("marketing", r'(click to|opens in new|applications open|apply today|apply now)', 'reclassify', 'marketing'),
            ProcessingRule("navigation", r'^(home|about|contact|privacy|terms|sitemap|search)$', 'reclassify', 'navigation'),
            
            # Generic codes and abbreviations
            ProcessingRule("generic_codes", r'^(stem|gre|gmat|sat|toefl|ielts|phd|mba|ai|it|hr)$', 'reclassify', 'generic_codes'),
            
            # Low confidence threshold
            ProcessingRule("low_confidence", r'.*', 'check_confidence', 'low_confidence')
        ]
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler('post_processor.log'),
                logging.StreamHandler()
            ]
        )
    
    def process_verified_companies_with_homepage_validation(self, input_file: str = "verified_companies.csv") -> Dict:
        """Enhanced processing with homepage validation."""
        logging.info(f"Processing {input_file} with homepage validation")
        
        try:
            df = pd.read_csv(input_file)
            original_count = len(df)
            logging.info(f"Loaded {original_count} entries")
            
            validated_organizations = []
            reclassified_content = []
            failed_validations = []
            
            for idx, row in df.iterrows():
                logging.info(f"Processing entry {idx + 1}/{original_count}: {row['organization_name'][:50]}...")
                
                # Extract homepage URL
                homepage_url = self.homepage_validator.extract_homepage_url(row['url'])
                
                # Validate homepage
                validation = self.homepage_validator.validate_homepage(homepage_url)
                
                if validation.is_organization and validation.confidence_score >= 0.3:
                    # Update organization data with homepage validation
                    updated_row = row.copy()
                    updated_row['url'] = homepage_url  # Use homepage URL
                    updated_row['confidence_score'] = max(row.get('confidence_score', 0), validation.confidence_score)
                    updated_row['type'] = validation.organization_type
                    if validation.homepage_title:
                        updated_row['organization_name'] = validation.homepage_title
                    if validation.description:
                        updated_row['description'] = validation.description
                    
                    validated_organizations.append(updated_row)
                    logging.info(f"✅ Validated: {updated_row['organization_name'][:50]} (Score: {validation.confidence_score:.2f})")
                    
                else:
                    # Reclassify as general content
                    reclassified_entry = row.copy()
                    reclassified_entry['reason_for_reclassification'] = validation.reason
                    reclassified_entry['rule_triggered'] = 'homepage_validation_failed'
                    reclassified_entry['homepage_url'] = homepage_url
                    reclassified_entry['validation_score'] = validation.confidence_score
                    
                    reclassified_content.append(reclassified_entry)
                    logging.info(f"❌ Reclassified: {row['organization_name'][:50]} - {validation.reason}")
                
                # Add small delay to be respectful to servers
                time.sleep(0.5)
            
            # Create DataFrames
            validated_df = pd.DataFrame(validated_organizations)
            reclassified_df = pd.DataFrame(reclassified_content)
            
            # Remove duplicates from validated organizations
            if not validated_df.empty:
                logging.info(f"Starting deduplication with {len(validated_df)} entries")
                validated_df = self._deduplicate_organizations(validated_df)
                logging.info(f"Removed {len(validated_organizations) - len(validated_df)} duplicates, {len(validated_df)} entries remaining")
            
            # Save results
            if not validated_df.empty:
                validated_df.to_csv('verified_companies_clean.csv', index=False)
                logging.info(f"Saved {len(validated_df)} clean organizations to verified_companies_clean.csv")
            
            if not reclassified_df.empty:
                reclassified_df.to_csv('reclassified_content.csv', index=False)
                logging.info(f"Saved {len(reclassified_df)} reclassified entries to reclassified_content.csv")
                
                # Add reclassified content to search_results.csv
                self._add_to_search_results(reclassified_df)
            
            return {
                'original_count': original_count,
                'valid_organizations': len(validated_df),
                'reclassified_entries': len(reclassified_df),
                'validation_success_rate': (len(validated_df) / original_count) * 100 if original_count > 0 else 0
            }
            
        except Exception as e:
            logging.error(f"Error in processing: {e}")
            raise
    
    def _add_to_search_results(self, reclassified_df: pd.DataFrame):
        """Add reclassified content to search_results.csv for reprocessing."""
        try:
            # Read existing search results
            try:
                search_results_df = pd.read_csv('search_results.csv')
            except FileNotFoundError:
                search_results_df = pd.DataFrame(columns=['title', 'abstract', 'url'])
            
            # Convert reclassified entries to search results format
            new_search_entries = []
            for _, row in reclassified_df.iterrows():
                new_search_entries.append({
                    'title': row['organization_name'],
                    'abstract': f"Reclassified: {row.get('reason_for_reclassification', 'Homepage validation failed')}",
                    'url': row.get('homepage_url', row['url'])
                })
            
            # Combine and deduplicate
            combined_df = pd.concat([search_results_df, pd.DataFrame(new_search_entries)], ignore_index=True)
            combined_df.drop_duplicates(subset=['url'], keep='first', inplace=True)
            
            # Save updated search results
            combined_df.to_csv('search_results.csv', index=False)
            logging.info(f"Added {len(new_search_entries)} reclassified entries to search_results.csv")
            
        except Exception as e:
            logging.error(f"Error adding to search results: {e}")
    
    def _deduplicate_organizations(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate organizations based on URL and name similarity."""
        if df.empty:
            return df
        
        # Sort by confidence score (highest first)
        df = df.sort_values('confidence_score', ascending=False)
        
        # Remove exact URL duplicates
        df = df.drop_duplicates(subset=['url'], keep='first')
        
        # Remove similar organization names
        seen_names = set()
        unique_indices = []
        
        for idx, row in df.iterrows():
            name = row['organization_name'].lower().strip()
            # Simple similarity check - remove if name is very similar to existing
            is_duplicate = False
            for seen_name in seen_names:
                if self._are_names_similar(name, seen_name):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                seen_names.add(name)
                unique_indices.append(idx)
        
        return df.loc[unique_indices]
    
    def _are_names_similar(self, name1: str, name2: str, threshold: float = 0.85) -> bool:
        """Check if two organization names are similar."""
        # Simple Jaccard similarity
        words1 = set(name1.split())
        words2 = set(name2.split())
        
        if not words1 or not words2:
            return False
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        similarity = intersection / union if union > 0 else 0
        return similarity >= threshold
    
    def generate_report(self, results: Dict) -> str:
        """Generate a comprehensive processing report."""
        report = f"""# Homepage Validation Processing Report

## 📊 Summary Statistics

- **Original entries**: {results['original_count']}
- **Valid organizations**: {results['valid_organizations']}
- **Reclassified entries**: {results['reclassified_entries']}
- **Validation success rate**: {results['validation_success_rate']:.1f}%

## 🏛️ Organization Quality Improvement

### Homepage Validation Process:
1. **URL Normalization**: Extracted homepage URLs from deep links
2. **Content Analysis**: Analyzed homepage content for organization indicators
3. **Confidence Scoring**: Applied multi-factor confidence scoring
4. **Domain Intelligence**: Used domain patterns (.edu, .ac., etc.) for validation

### Quality Indicators:
- Organizations now have validated homepage URLs
- Content-based confidence scoring
- Proper organization type classification
- Removal of non-organization content

## 📁 Output Files

- `verified_companies_clean.csv`: {results['valid_organizations']} validated organizations
- `reclassified_content.csv`: {results['reclassified_entries']} reclassified entries
- `search_results.csv`: Updated with reclassified content for reprocessing

## 🎯 Next Steps

1. Review validated organizations in `verified_companies_clean.csv`
2. Process reclassified content in `search_results.csv` if needed
3. Consider running additional validation rounds for edge cases

---
Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return report

# Backward compatibility function
def process_verified_companies_legacy(input_file: str = "verified_companies.csv") -> Dict:
    """Legacy processing function without homepage validation."""
    processor = DataPostProcessor()
    return processor.process_verified_companies_legacy(input_file)

if __name__ == "__main__":
    processor = DataPostProcessor()
    results = processor.process_verified_companies_with_homepage_validation()
    
    # Generate and save report
    report = processor.generate_report(results)
    with open('homepage_validation_report.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n🎉 HOMEPAGE VALIDATION COMPLETED!")
    print(f"📊 Results: {results['valid_organizations']} organizations, {results['reclassified_entries']} reclassified")
    print(f"📈 Success rate: {results['validation_success_rate']:.1f}%") 