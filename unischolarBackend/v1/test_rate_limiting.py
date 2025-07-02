#!/usr/bin/env python3
"""
Test script for UniScholar rate limiting functionality.

This script demonstrates how the rate limiting works and allows testing
different configurations to handle DuckDuckGo rate limits.
"""

import time
import logging
from unischolar.crawlers.academic import AcademicWebCrawler
from unischolar.core.config import DEFAULT_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('rate_limiting_test.log')
    ]
)

def test_default_rate_limiting():
    """Test with default rate limiting configuration"""
    print("🧪 Testing with default rate limiting configuration...")
    
    crawler = AcademicWebCrawler()
    
    # Test multiple searches in quick succession
    test_queries = [
        "universities in norway",
        "universities in sweden", 
        "universities in denmark"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Search {i}: {query} ---")
        start_time = time.time()
        
        try:
            result = crawler.search_and_crawl(query, max_results=5)
            elapsed = time.time() - start_time
            
            print(f"✅ Search completed in {elapsed:.1f}s")
            print(f"📊 Found {len(result.organizations)} organizations")
            
        except Exception as e:
            print(f"❌ Search failed: {e}")
        
        print("-" * 50)

def test_conservative_rate_limiting():
    """Test with conservative (slower) rate limiting"""
    print("\n🐌 Testing with conservative rate limiting configuration...")
    
    # Conservative configuration for heavily rate-limited scenarios
    conservative_config = DEFAULT_CONFIG.copy()
    conservative_config['search_rate_limiting'] = {
        'min_search_interval': 10.0,    # Wait 10 seconds between searches
        'initial_delay': 5.0,           # Start with 5-second delays
        'max_delay': 120.0,             # Up to 2-minute delays
        'backoff_factor': 3.0,          # More aggressive backoff
        'max_retries': 7                # More retry attempts
    }
    
    crawler = AcademicWebCrawler(conservative_config)
    
    # Test a single search with conservative settings
    query = "universities in finland"
    print(f"🔍 Testing search: {query}")
    start_time = time.time()
    
    try:
        result = crawler.search_and_crawl(query, max_results=5)
        elapsed = time.time() - start_time
        
        print(f"✅ Conservative search completed in {elapsed:.1f}s")
        print(f"📊 Found {len(result.organizations)} organizations")
        
    except Exception as e:
        print(f"❌ Conservative search failed: {e}")

def test_aggressive_rate_limiting():
    """Test with aggressive (faster) rate limiting"""
    print("\n🚀 Testing with aggressive rate limiting configuration...")
    
    # Aggressive configuration for when rate limits are less strict
    aggressive_config = DEFAULT_CONFIG.copy()
    aggressive_config['search_rate_limiting'] = {
        'min_search_interval': 1.0,     # Minimal delay between searches
        'initial_delay': 1.0,           # Short initial delays
        'max_delay': 30.0,              # Shorter maximum delays
        'backoff_factor': 1.5,          # Gentler backoff
        'max_retries': 3                # Fewer retries
    }
    
    crawler = AcademicWebCrawler(aggressive_config)
    
    # Test rapid searches
    query = "universities in iceland"
    print(f"🔍 Testing aggressive search: {query}")
    start_time = time.time()
    
    try:
        result = crawler.search_and_crawl(query, max_results=5)
        elapsed = time.time() - start_time
        
        print(f"✅ Aggressive search completed in {elapsed:.1f}s")
        print(f"📊 Found {len(result.organizations)} organizations")
        
    except Exception as e:
        print(f"❌ Aggressive search failed: {e}")

def main():
    """Run all rate limiting tests"""
    print("🧪 UniScholar Rate Limiting Test Suite")
    print("=" * 60)
    
    # Test 1: Default configuration
    test_default_rate_limiting()
    
    # Wait between test suites
    print("\n⏳ Waiting 30 seconds between test suites...")
    time.sleep(30)
    
    # Test 2: Conservative configuration
    test_conservative_rate_limiting()
    
    # Wait between test suites
    print("\n⏳ Waiting 30 seconds between test suites...")
    time.sleep(30)
    
    # Test 3: Aggressive configuration
    test_aggressive_rate_limiting()
    
    print("\n✅ Rate limiting tests completed!")
    print("📄 Check 'rate_limiting_test.log' for detailed logs")

if __name__ == "__main__":
    main() 