# Academic Search Processing Report

## Query Information
- **Query**: universities in canada
- **Max Results**: 30
- **Query Intent**: general

## Results Summary
- **Academic Organizations Found**: 1072
- **General Content Items**: 269
- **Failed URLs**: 0

## Output Files
- **Organizations**: output/search_results.csv
- **General Content**: output/search_results_general_content.csv
- **Failed URLs**: output/search_results_failed_urls.csv

## Content Classification
### Organizations (Academic Institutions)
Academic organizations with confidence scores >= 0.5, excluding blog posts and articles.

### General Content (Filtered Out)
Blog posts, articles, guides, and other non-institutional content like:
- "Best universities" lists
- "Top colleges" articles  
- How-to guides and tutorials
- Navigation pages

## Post-Processing Results
- **Status**: completed
- **Message**: Processed output/search_results.csv (placeholder implementation)

## Processing Details
- **Extraction Method**: Dynamic academic-focused NER with enhanced filtering
- **Confidence Threshold**: 0.5
- **Rate Limiting**: 1.0s between requests
- **Filtering**: Enhanced exclusion patterns for blog posts and articles

Generated on: 2025-07-02 09:23:55
