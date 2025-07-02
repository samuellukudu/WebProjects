"""
Main entry point for UniScholar platform.

This module provides the command-line interface and orchestrates the entire
data extraction and processing pipeline.
"""

import argparse
import logging
import sys
import os
from pathlib import Path
from typing import Optional, List

# Add the parent directory to sys.path to enable relative imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from unischolar.core.config import get_config, set_config, Config
from unischolar.core.exceptions import UniScholarException

# Optional imports with comprehensive error handling
try:
    import sys
    import os
    # Import spaCy first to check if it's available
    import spacy
    from unischolar.extractors.dynamic_ner import DynamicNERExtractor
    EXTRACTOR_AVAILABLE = True
except (ImportError, ValueError, OSError) as e:
    print(f"Warning: Advanced NLP features unavailable due to dependency issues.")
    print(f"To enable full functionality, try: pip install numpy<2.0 spacy")
    DynamicNERExtractor = None
    EXTRACTOR_AVAILABLE = False

try:
    from unischolar.processors.post_processor import DataPostProcessor
    PROCESSOR_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Advanced processing features unavailable due to dependency issues.")
    print(f"To enable full functionality, try: pip install numpy<2.0 pandas")
    DataPostProcessor = None
    PROCESSOR_AVAILABLE = False


class UniScholarPipeline:
    """Main pipeline orchestrator for UniScholar platform"""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or get_config()
        self.setup_logging()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, self.config.logging.level.upper()),
            format=self.config.logging.format,
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Add file handler if enabled
        if self.config.logging.file_enabled:
            os.makedirs(os.path.dirname(self.config.logging.file_path), exist_ok=True)
            file_handler = logging.FileHandler(self.config.logging.file_path)
            file_handler.setFormatter(logging.Formatter(self.config.logging.format))
            logging.getLogger().addHandler(file_handler)
    
    def run_search_pipeline(self, query: str, max_results: int = None, 
                          output_file: str = None) -> dict:
        """Run the complete search and extraction pipeline"""
        if max_results is None:
            max_results = self.config.max_search_results
        
        # Set up output directory and file
        output_dir = self.config.output.output_directory
        os.makedirs(output_dir, exist_ok=True)
        
        if output_file is None:
            timestamp = __import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"search_results_{timestamp}.csv"
        
        # Ensure output file is in the configured output directory
        if not os.path.isabs(output_file):
            output_file = os.path.join(output_dir, output_file)
        
        self.logger.info(f"Starting academic search pipeline for: '{query}' (max_results={max_results})")
        self.logger.info(f"💾 Output will be saved to: {output_file}")
        
        # Check if required components are available
        if not EXTRACTOR_AVAILABLE:
            self.logger.warning("Dynamic NER extractor not available - spaCy dependency may be missing")
            return {
                'query': query,
                'max_results': max_results,
                'output_file': output_file,
                'status': 'extractor_unavailable',
                'message': 'spaCy dependency required for full functionality'
            }
        
        try:
            # Import and use the academic crawler
            from unischolar.crawlers.academic import AcademicWebCrawler
            
            # Create crawler with configuration
            crawler = AcademicWebCrawler(self.config.__dict__ if hasattr(self.config, '__dict__') else {})
            
            # Perform search and crawling
            crawl_result = crawler.crawl(query, max_results)
            
            # Save results to CSV with proper separation
            import pandas as pd
            
            # Save organizations (actual academic institutions)
            if crawl_result.organizations:
                org_data = []
                for org in crawl_result.organizations:
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
                org_df = org_df.sort_values('confidence_score', ascending=False)
                
                # Use the specified output file for organizations
                org_df.to_csv(output_file, index=False, encoding='utf-8')
                self.logger.info(f"📊 Saved {len(org_data)} organizations to {output_file}")
            
            # Save general content (blog posts, articles, etc.) to separate file
            if crawl_result.general_content:
                content_data = []
                for content in crawl_result.general_content:
                    content_data.append({
                        'title': content.title,
                        'url': content.url,
                        'content_type': content.content_type,
                        'source_url': content.source_url,
                        'description': content.description
                    })
                
                content_df = pd.DataFrame(content_data)
                
                # Save to separate general content file
                general_content_file = output_file.replace('.csv', '_general_content.csv')
                content_df.to_csv(general_content_file, index=False, encoding='utf-8')
                self.logger.info(f"📝 Saved {len(content_data)} general content items to {general_content_file}")
            
            # Save failed URLs for reference
            if crawl_result.failed_urls:
                failed_data = [{'url': url} for url in crawl_result.failed_urls]
                failed_df = pd.DataFrame(failed_data)
                
                failed_urls_file = output_file.replace('.csv', '_failed_urls.csv')
                failed_df.to_csv(failed_urls_file, index=False, encoding='utf-8')
                self.logger.info(f"❌ Saved {len(crawl_result.failed_urls)} failed URLs to {failed_urls_file}")
            
            # Post-process if processor is available
            if PROCESSOR_AVAILABLE and crawl_result.organizations:
                try:
                    processor = DataPostProcessor()
                    # Pass the output file as input for post-processing
                    results = processor.process_verified_companies_with_homepage_validation(input_file=output_file)
                    
                    # Create a comprehensive report from the results
                    report_content = f"""# Academic Search Processing Report

## Query Information
- **Query**: {query}
- **Max Results**: {max_results}
- **Query Intent**: {crawl_result.query_intent.search_intent if crawl_result.query_intent else 'Unknown'}

## Results Summary
- **Academic Organizations Found**: {len(crawl_result.organizations)}
- **General Content Items**: {len(crawl_result.general_content)}
- **Failed URLs**: {len(crawl_result.failed_urls)}

## Output Files
- **Organizations**: {output_file}
- **General Content**: {output_file.replace('.csv', '_general_content.csv')}
- **Failed URLs**: {output_file.replace('.csv', '_failed_urls.csv')}

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
- **Status**: {results.get('status', 'Unknown')}
- **Message**: {results.get('message', 'No message available')}

## Processing Details
- **Extraction Method**: Dynamic academic-focused NER with enhanced filtering
- **Confidence Threshold**: {self.config.extraction.confidence_threshold}
- **Rate Limiting**: {self.config.crawler.request_delay}s between requests
- **Filtering**: Enhanced exclusion patterns for blog posts and articles

Generated on: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
                    
                    # Save the report
                    report_file = output_file.replace('.csv', '_report.md')
                    with open(report_file, 'w', encoding='utf-8') as f:
                        f.write(report_content)
                    
                    self.logger.info(f"✅ Post-processing completed: {results.get('status', 'Unknown')}")
                    self.logger.info(f"📄 Report saved to {report_file}")
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ Post-processing failed: {e}")
            
            return {
                'query': query,
                'max_results': max_results,
                'output_file': output_file,
                'status': 'completed',
                'organizations_found': len(crawl_result.organizations),
                'general_content_found': len(crawl_result.general_content),
                'failed_urls': len(crawl_result.failed_urls),
                'query_intent': str(crawl_result.query_intent.search_intent) if crawl_result.query_intent else None,
                'output_files': {
                    'organizations': output_file,
                    'general_content': output_file.replace('.csv', '_general_content.csv'),
                    'failed_urls': output_file.replace('.csv', '_failed_urls.csv'),
                    'report': output_file.replace('.csv', '_report.md')
                },
                'extractor_available': EXTRACTOR_AVAILABLE,
                'processor_available': PROCESSOR_AVAILABLE
            }
            
        except ImportError as e:
            self.logger.error(f"Failed to import academic crawler: {e}")
            return {
                'query': query,
                'max_results': max_results,
                'output_file': output_file,
                'status': 'import_error',
                'message': f'Failed to import required modules: {e}'
            }
        except Exception as e:
            self.logger.error(f"Search pipeline failed: {e}")
            return {
                'query': query,
                'max_results': max_results,
                'output_file': output_file,
                'status': 'error',
                'message': f'Pipeline failed: {e}'
            }
    
    def validate_config(self) -> List[str]:
        """Validate current configuration"""
        return self.config.validate()


def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser"""
    parser = argparse.ArgumentParser(
        description="UniScholar - Comprehensive Student Educational Dataset Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search for universities in Germany
  python -m unischolar.main search "universities in Germany computer science"
  
  # Process existing results
  python -m unischolar.main process --input results.csv
  
  # Search with custom settings
  python -m unischolar.main search "AI startups" --max-results 50 --output ai_companies.csv
  
  # Validate configuration
  python -m unischolar.main validate-config
        """
    )
    
    # Global options
    parser.add_argument('--config', type=str, help='Path to configuration file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--quiet', '-q', action='store_true', help='Enable quiet mode')
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search for and extract entities')
    search_parser.add_argument('query', type=str, help='Search query')
    search_parser.add_argument('--max-results', type=int, default=30, 
                              help='Maximum number of search results (default: 30)')
    search_parser.add_argument('--output', '-o', type=str, default='search_results.csv',
                              help='Output file for results (default: search_results.csv)')
    
    # Process command
    process_parser = subparsers.add_parser('process', help='Process existing results')
    process_parser.add_argument('--input', '-i', type=str, required=True,
                               help='Input file to process')
    process_parser.add_argument('--output', '-o', type=str, 
                               help='Output file (default: <input>_processed.csv)')
    
    # Validate config command
    validate_parser = subparsers.add_parser('validate-config', help='Validate configuration')
    
    return parser


def main():
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    try:
        # Load custom config if specified
        if args.config:
            config = Config.load_from_file(args.config)
            set_config(config)
        else:
            config = get_config()
        
        # Adjust logging level based on verbosity
        if args.verbose:
            config.logging.level = "DEBUG"
        elif args.quiet:
            config.logging.level = "WARNING"
        
        # Initialize pipeline
        pipeline = UniScholarPipeline(config)
        
        # Handle commands
        if args.command == 'search':
            result = pipeline.run_search_pipeline(
                query=args.query,
                max_results=args.max_results,
                output_file=args.output
            )
            print(f"\nSearch pipeline result: {result}")
            
        elif args.command == 'process':
            print(f"Processing file: {args.input}")
            print("Processing functionality will be implemented as we build out the modules.")
            
        elif args.command == 'validate-config':
            issues = pipeline.validate_config()
            if issues:
                print("Configuration issues found:")
                for issue in issues:
                    print(f"  - {issue}")
                sys.exit(1)
            else:
                print("Configuration is valid!")
                
        else:
            parser.print_help()
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except UniScholarException as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        if hasattr(args, 'verbose') and args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()