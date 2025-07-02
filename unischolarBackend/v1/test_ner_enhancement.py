#!/usr/bin/env python3
"""
Test script for enhanced NER functionality in UniScholar
Demonstrates named entity recognition on DuckDuckGo search results and user queries
"""

import sys
import os
import logging
from datetime import datetime

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from unischolar.crawlers.academic import AcademicWebCrawler
from unischolar.extractors.search_ner import SearchNERProcessor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ner_test.log')
    ]
)

logger = logging.getLogger(__name__)

def test_ner_on_queries():
    """Test NER analysis on various educational queries"""
    print("\n" + "="*80)
    print("🧠 TESTING NER ON EDUCATIONAL QUERIES")
    print("="*80)
    
    # Initialize NER processor
    ner_processor = SearchNERProcessor()
    
    # Test queries with different intents
    test_queries = [
        "best universities in Germany for computer science",
        "scholarships for international students studying engineering",
        "PhD programs in artificial intelligence at Stanford University",
        "University of Cambridge admission requirements for medicine",
        "merit-based scholarships deadline March 2024",
        "technical universities in Netherlands offering robotics programs",
        "research opportunities in machine learning at MIT",
        "study abroad programs in Japan for business students"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Query {i}: '{query}'")
        print("-" * 60)
        
        # Mock search results for testing
        mock_results = [
            {
                'url': f'https://example-uni-{i}.edu/programs',
                'title': f'Top Universities for {query.split()[-1].title()} Programs',
                'abstract': f'Discover the best universities offering {query.split()[-1]} programs with excellent research opportunities, scholarships, and career prospects.'
            },
            {
                'url': f'https://scholarship-portal-{i}.org/opportunities',
                'title': f'Scholarship Opportunities for {query.split()[0].title()} Students',
                'abstract': f'Find {query.split()[0]} scholarships, fellowships, and financial aid for international students. Deadlines, requirements, and application tips.'
            }
        ]
        
        # Process with NER
        try:
            ner_result = ner_processor.process_search_results(query, mock_results)
            
            # Display results
            print(f"🎯 Intent: {ner_result.intent_analysis['primary_intent']} "
                  f"(confidence: {ner_result.intent_analysis['confidence']:.2f})")
            
            print(f"📊 Query Entities:")
            qe = ner_result.query_entities
            if qe.universities:
                print(f"   🏛️ Universities: {[e.text for e in qe.universities]}")
            if qe.scholarships:
                print(f"   💰 Scholarships: {[e.text for e in qe.scholarships]}")
            if qe.programs:
                print(f"   📚 Programs: {[e.text for e in qe.programs]}")
            if qe.locations:
                print(f"   📍 Locations: {[e.text for e in qe.locations]}")
            if qe.subjects:
                print(f"   🔬 Subjects: {[e.text for e in qe.subjects]}")
            if qe.deadlines:
                print(f"   ⏰ Deadlines: {[e.text for e in qe.deadlines]}")
            
            print(f"🔗 Relevance Scores:")
            for url, score in ner_result.relevance_scores.items():
                print(f"   {score:.3f}: {url}")
            
            if ner_result.entity_matches:
                print(f"✅ Entity Matches: {len(ner_result.entity_matches)} found")
            
        except Exception as e:
            print(f"❌ Error processing query: {e}")

def test_full_crawl_with_ner():
    """Test full crawling with NER enhancement"""
    print("\n" + "="*80)
    print("🕷️ TESTING FULL CRAWL WITH NER ENHANCEMENT")
    print("="*80)
    
    # Initialize crawler
    crawler = AcademicWebCrawler()
    
    # Test with a real query
    test_query = "top universities in Germany for engineering"
    print(f"\n🔍 Testing with query: '{test_query}'")
    
    try:
        # Perform search and crawl with NER enhancement
        result = crawler.search_and_crawl(test_query, max_results=5)
        
        print(f"\n📊 Crawl Results:")
        print(f"   🏛️ Organizations found: {len(result.organizations)}")
        print(f"   📄 General content: {len(result.general_content)}")
        print(f"   ❌ Failed URLs: {len(result.failed_urls)}")
        
        # Show top organizations with NER-enhanced confidence
        print(f"\n🏆 Top Organizations (with NER-enhanced scoring):")
        sorted_orgs = sorted(result.organizations, key=lambda x: x.confidence_score, reverse=True)
        
        for i, org in enumerate(sorted_orgs[:10], 1):
            print(f"   {i}. {org.name}")
            print(f"      🔗 URL: {org.url}")
            print(f"      📊 Confidence: {org.confidence_score:.3f}")
            print(f"      🔧 Method: {org.extraction_method}")
            print(f"      📝 Type: {org.org_type}")
            if org.description:
                print(f"      💬 Description: {org.description[:100]}...")
            print()
        
        # Show NER-specific extractions
        ner_extractions = [org for org in result.organizations if org.extraction_method.startswith('ner')]
        if ner_extractions:
            print(f"🧠 NER-Guided Extractions: {len(ner_extractions)}")
            for org in ner_extractions[:5]:
                print(f"   • {org.name} ({org.org_type}) - {org.confidence_score:.3f}")
        
    except Exception as e:
        print(f"❌ Error during crawl: {e}")
        import traceback
        traceback.print_exc()

def test_ner_entity_extraction():
    """Test detailed NER entity extraction on sample texts"""
    print("\n" + "="*80)
    print("🔍 TESTING DETAILED NER ENTITY EXTRACTION")
    print("="*80)
    
    ner_processor = SearchNERProcessor()
    
    # Sample educational texts
    sample_texts = [
        "Stanford University offers excellent PhD programs in Computer Science with full scholarships available. Application deadline is January 15, 2024. Tuition coverage up to $50,000 per year.",
        
        "The Technical University of Munich (TUM) is ranked among the top engineering schools in Europe. They offer Master's programs in Robotics and Machine Learning with research opportunities.",
        
        "Merit-based scholarships worth €15,000 are available for international students at University of Amsterdam. Apply by March 31, 2024 for programs starting in September.",
        
        "MIT hosts the International Conference on Artificial Intelligence every year. Students can present research and network with leading academics in the field."
    ]
    
    for i, text in enumerate(sample_texts, 1):
        print(f"\n📄 Text {i}:")
        print(f"'{text[:100]}...'")
        print("-" * 60)
        
        try:
            entities = ner_processor.extract_entities_from_text(text, source='test')
            
            # Display extracted entities
            entity_types = [
                ('Universities', entities.universities),
                ('Programs', entities.programs),
                ('Scholarships', entities.scholarships),
                ('Locations', entities.locations),
                ('Subjects', entities.subjects),
                ('Degrees', entities.degrees),
                ('Deadlines', entities.deadlines),
                ('Amounts', entities.amounts),
                ('Events', entities.events)
            ]
            
            for entity_name, entity_list in entity_types:
                if entity_list:
                    print(f"   {entity_name}:")
                    for entity in entity_list:
                        print(f"      • {entity.text} (confidence: {entity.confidence:.2f})")
            
        except Exception as e:
            print(f"❌ Error extracting entities: {e}")

def main():
    """Run all NER tests"""
    print("🚀 Starting Enhanced NER Testing for UniScholar")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Test 1: NER on queries
        test_ner_on_queries()
        
        # Test 2: Detailed entity extraction
        test_ner_entity_extraction()
        
        # Test 3: Full crawl with NER (this makes real web requests)
        response = input("\n🌐 Run full crawl test with real web requests? (y/N): ")
        if response.lower() == 'y':
            test_full_crawl_with_ner()
        else:
            print("⏭️ Skipping full crawl test")
        
        print("\n" + "="*80)
        print("✅ All NER tests completed successfully!")
        print("="*80)
        
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"⏰ Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 