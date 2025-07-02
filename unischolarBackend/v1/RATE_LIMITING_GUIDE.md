# UniScholar Rate Limiting Guide

## Overview

UniScholar uses DuckDuckGo search to find academic content. Due to the nature of web search services, rate limiting can occur when making too many requests in a short period. This guide explains how to handle and configure rate limiting in UniScholar.

## Understanding Rate Limiting

### What is Rate Limiting?
Rate limiting is a mechanism used by search services to prevent abuse and ensure fair usage. When you see errors like:
```
Error to search using html backend: https://html.duckduckgo.com/html 202 Ratelimit
```

This means you've exceeded the allowed number of requests per time period.

### Common Scenarios
- Making multiple searches in quick succession
- Running automated searches frequently
- High-volume data extraction tasks

## UniScholar's Rate Limiting Solution

UniScholar implements several mechanisms to handle rate limiting:

### 1. Global Search Rate Limiting
- Enforces minimum time between searches
- Default: 3 seconds between searches
- Prevents rapid-fire search requests

### 2. Exponential Backoff Retry
- Automatically retries failed searches with increasing delays
- Default: 2s, 4s, 8s, 16s, 32s delays
- Maximum 5 retry attempts by default

### 3. Configurable Parameters
All rate limiting parameters can be customized based on your needs.

## Configuration Options

### Default Configuration
```python
{
    'search_rate_limiting': {
        'min_search_interval': 3.0,    # Minimum seconds between searches
        'initial_delay': 2.0,          # Initial delay for retries (seconds)
        'max_delay': 60.0,             # Maximum delay for retries (seconds)
        'backoff_factor': 2.0,         # Exponential backoff multiplier
        'max_retries': 5               # Maximum number of retry attempts
    }
}
```

### Conservative Configuration (for Heavy Rate Limiting)
```python
conservative_config = {
    'search_rate_limiting': {
        'min_search_interval': 10.0,   # Wait 10 seconds between searches
        'initial_delay': 5.0,          # Start with 5-second delays
        'max_delay': 120.0,            # Up to 2-minute delays
        'backoff_factor': 3.0,         # More aggressive backoff
        'max_retries': 7               # More retry attempts
    }
}
```

### Aggressive Configuration (for Light Rate Limiting)
```python
aggressive_config = {
    'search_rate_limiting': {
        'min_search_interval': 1.0,    # Minimal delay between searches
        'initial_delay': 1.0,          # Short initial delays
        'max_delay': 30.0,             # Shorter maximum delays
        'backoff_factor': 1.5,         # Gentler backoff
        'max_retries': 3               # Fewer retries
    }
}
```

## Usage Examples

### Basic Usage with Default Rate Limiting
```python
from unischolar.crawlers.academic import AcademicWebCrawler

# Uses default rate limiting configuration
crawler = AcademicWebCrawler()
result = crawler.search_and_crawl("universities in norway", max_results=30)
```

### Custom Rate Limiting Configuration
```python
from unischolar.crawlers.academic import AcademicWebCrawler

config = {
    'search_rate_limiting': {
        'min_search_interval': 5.0,
        'initial_delay': 3.0,
        'max_delay': 90.0,
        'backoff_factor': 2.5,
        'max_retries': 6
    }
}

crawler = AcademicWebCrawler(config)
result = crawler.search_and_crawl("universities in sweden", max_results=30)
```

### Batch Processing with Rate Limiting
```python
import time
from unischolar.crawlers.academic import AcademicWebCrawler

# Conservative configuration for batch processing
config = {
    'search_rate_limiting': {
        'min_search_interval': 15.0,  # 15 seconds between searches
        'initial_delay': 10.0,        # Start with 10-second delays
        'max_delay': 300.0,           # Up to 5-minute delays
        'backoff_factor': 2.0,
        'max_retries': 10
    }
}

crawler = AcademicWebCrawler(config)

queries = [
    "universities in norway",
    "universities in sweden", 
    "universities in denmark",
    "universities in finland",
    "universities in iceland"
]

for query in queries:
    print(f"Processing: {query}")
    result = crawler.search_and_crawl(query, max_results=20)
    print(f"Found {len(result.organizations)} organizations")
    
    # Additional delay between queries (optional)
    time.sleep(30)
```

## Best Practices

### 1. Start Conservative
When you're experiencing rate limiting, start with conservative settings and gradually make them more aggressive as needed.

### 2. Monitor Logs
UniScholar provides detailed logging about rate limiting:
```
⏳ Global search rate limit: waiting 3.0s
⏳ Rate limit delay: 4.0s (attempt 2/5)
⚠️ Rate limit detected on attempt 3: 202 Ratelimit
```

### 3. Time Your Searches
- Avoid peak hours when possible
- Spread searches across longer time periods
- Use more specific search terms to reduce the need for multiple searches

### 4. Handle Graceful Degradation
UniScholar returns empty results instead of crashing when all retries fail:
```python
result = crawler.search_and_crawl("query", max_results=30)
if not result.organizations:
    print("Search was rate limited or failed - trying alternative approach")
    # Implement fallback logic
```

## Testing Rate Limiting

Use the provided test script to verify your configuration:

```bash
python test_rate_limiting.py
```

This will test different rate limiting configurations and help you find the optimal settings for your use case.

## Troubleshooting

### Still Getting Rate Limited?
1. **Increase delays**: Use larger `min_search_interval` and `initial_delay` values
2. **Reduce frequency**: Wait longer between searches manually
3. **Use different times**: Try searching during off-peak hours
4. **Smaller batches**: Reduce `max_results` parameter

### Rate Limiting Messages
When rate limited, UniScholar provides helpful suggestions:
```
💡 Rate limiting suggestions:
   • Wait 5-10 minutes before trying again
   • Use more specific search terms
   • Try searching for a different topic
   • Consider running searches at different times of day
```

### Log Analysis
Check the logs for patterns:
- High frequency of rate limit errors → increase intervals
- Long delays between retries → reduce backoff factor
- Many failed attempts → increase max_retries

## Advanced Configuration

### Per-Domain Rate Limiting
UniScholar also implements per-domain rate limiting for web scraping:
```python
config = {
    'scraping': {
        'request_delay': 2.0,  # Delay between requests to same domain
        'max_retries': 5       # Retries for failed requests
    }
}
```

### Environment-Based Configuration
Create different configurations for different environments:

```python
import os

if os.getenv('ENVIRONMENT') == 'production':
    # Conservative settings for production
    config = {'search_rate_limiting': {'min_search_interval': 10.0}}
else:
    # More aggressive settings for development
    config = {'search_rate_limiting': {'min_search_interval': 2.0}}
```

## Summary

Rate limiting is a normal part of working with web search services. UniScholar provides robust mechanisms to handle it gracefully:

- **Automatic retries** with exponential backoff
- **Configurable parameters** for different scenarios
- **Graceful degradation** when searches fail
- **Detailed logging** for monitoring and debugging

By following this guide and adjusting the configuration based on your needs, you can effectively handle rate limiting while maximizing the success rate of your searches. 