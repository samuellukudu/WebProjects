#!/usr/bin/env python3
"""
Advanced Recognition Enhancement Test for UniScholar

This script demonstrates how advanced recognition techniques improve
search result alignment with user queries through:
- Multi-dimensional query understanding
- Intelligent result ranking
- Context-aware filtering
- User profile inference
- Geographic and temporal awareness
"""

import logging
import time
from typing import List, Dict
from unischolar.crawlers.academic import AcademicWebCrawler
from unischolar.enhancers.query_understanding import AdvancedQueryAnalyzer, IntelligentResultRanker
from unischolar.core.config import DEFAULT_CONFIG

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('advanced_recognition_test.log')
    ]
)

def test_query_understanding_variations():
    """Test advanced query understanding across different query types"""
    print("🧠 Testing Advanced Query Understanding")
    print("=" * 60)
    
    analyzer = AdvancedQueryAnalyzer()
    
    # Test queries representing different user types and intents
    test_queries = [
        # Basic university search
        "universities in norway",
        
        # Specific academic level + field
        "best engineering masters programs in germany",
        
        # Funding-focused query
        "scholarships for international students in canada phd computer science",
        
        # Admission-focused query
        "how to apply to medical school in uk requirements",
        
        # Comparison query with urgency
        "top business schools usa vs europe deadline 2025",
        
        # Parent perspective query
        "best colleges for my daughter architecture study abroad",
        
        # Researcher query
        "postdoc research positions artificial intelligence universities",
        
        # Multi-language query
        "université en france engineering programs english taught",
        
        # Online study query
        "online master degree computer science accredited universities",
        
        # Specific temporal query
        "spring 2025 admission deadlines psychology programs"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Test {i}: {query} ---")
        context = analyzer.analyze_query(query)
        
        print(f"🔤 Language: {context.language}")
        print(f"📝 Query Type: {context.query_type}")
        print(f"🎯 Specificity: {context.search_specificity:.2f}")
        print(f"👤 User Profile: {context.user_profile}")
        print(f"📊 Experience Level: {context.experience_level}")
        print(f"⏰ Deadline Urgency: {context.deadline_urgency}")
        
        if context.academic_level:
            print(f"🎓 Academic Levels: {', '.join(context.academic_level)}")
        if context.academic_fields:
            print(f"📚 Academic Fields: {', '.join(context.academic_fields)}")
        if context.target_countries:
            print(f"🌍 Target Countries: {', '.join(context.target_countries)}")
        if context.study_mode:
            print(f"💻 Study Mode: {', '.join(context.study_mode)}")
        if context.synonyms:
            print(f"🔄 Synonyms: {', '.join(list(context.synonyms)[:5])}")
        
        print("-" * 50)

def test_result_ranking_enhancement():
    """Test intelligent result ranking with mock search results"""
    print("\n🏆 Testing Intelligent Result Ranking")
    print("=" * 60)
    
    # Create test query context
    analyzer = AdvancedQueryAnalyzer()
    ranker = IntelligentResultRanker()
    
    query = "computer science phd programs in germany"
    context = analyzer.analyze_query(query)
    
    # Mock search results with different characteristics
    mock_results = [
        {
            'url': 'https://www.daad.de/en/study-and-research-in-germany/phd-studies/',
            'title': 'PhD Studies in Germany - DAAD',
            'abstract': 'Official information about PhD programs in Germany for international students. Computer science and engineering doctoral programs.'
        },
        {
            'url': 'https://top10universities.com/best-phd-germany-ever-amazing',
            'title': 'Top 10 Amazing PhD Programs in Germany You Must See!',
            'abstract': 'Blog post listing the most incredible PhD opportunities in Germany with clickbait content.'
        },
        {
            'url': 'https://www.tum.de/en/studies/degree-programs/doctoral-programs/',
            'title': 'Doctoral Programs - Technical University of Munich',
            'abstract': 'TUM offers excellent doctoral programs in computer science, engineering, and natural sciences.'
        },
        {
            'url': 'https://www.mpg.de/phd-programs',
            'title': 'PhD Programs at Max Planck Institutes',
            'abstract': 'Research-intensive PhD opportunities at Max Planck Institutes across Germany in various scientific fields.'
        },
        {
            'url': 'https://www.studyabroad.com/germany-universities-general-info',
            'title': 'Study in Germany - General University Information',
            'abstract': 'General information about studying in Germany, including undergraduate and graduate programs.'
        }
    ]
    
    print(f"📝 Query: {query}")
    print(f"🎯 Context: {context.query_type}, {context.user_profile}")
    
    # Rank results
    ranked_results = ranker.rank_results(mock_results, context)
    
    print(f"\n🏆 Ranking Results:")
    for i, result in enumerate(ranked_results, 1):
        print(f"   {i}. Score: {result.overall_score:.3f} | Confidence: {result.confidence:.2f}")
        print(f"      URL: {result.url}")
        if result.explanation:
            print(f"      Reasons: {', '.join(result.explanation)}")
        
        # Show component scores
        if result.component_scores:
            components = [f"{k}:{v:.2f}" for k, v in result.component_scores.items()]
            print(f"      Components: {', '.join(components)}")
        print()

def test_comprehensive_search_enhancement():
    """Test comprehensive search with all recognition enhancements"""
    print("\n🚀 Testing Comprehensive Search Enhancement")
    print("=" * 60)
    
    # Configure with conservative rate limiting for testing
    config = DEFAULT_CONFIG.copy()
    config['search_rate_limiting'] = {
        'min_search_interval': 5.0,
        'initial_delay': 3.0,
        'max_delay': 60.0,
        'backoff_factor': 2.0,
        'max_retries': 3
    }
    
    crawler = AcademicWebCrawler(config)
    
    # Test queries with different characteristics
    test_queries = [
        "scholarships for engineering students in norway",  # Funding + specific field + location
        "best universities computer science phd germany",   # Comparison + level + field + location
        "medical school admission requirements canada"      # Admission info + field + location
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Comprehensive Test {i}: {query} ---")
        start_time = time.time()
        
        try:
            result = crawler.search_and_crawl(query, max_results=5)
            elapsed = time.time() - start_time
            
            print(f"✅ Enhanced search completed in {elapsed:.1f}s")
            print(f"📊 Found {len(result.organizations)} organizations")
            print(f"📄 Found {len(result.general_content)} content items")
            
            # Show top organizations with their confidence scores
            if result.organizations:
                print(f"\n🏆 Top Organizations:")
                for j, org in enumerate(result.organizations[:5], 1):
                    print(f"   {j}. {org.name} ({org.confidence_score:.2f})")
                    print(f"      URL: {org.url}")
                    print(f"      Method: {org.extraction_method}")
            
        except Exception as e:
            print(f"❌ Enhanced search failed: {e}")
        
        print("-" * 50)
        
        # Wait between tests to respect rate limits
        if i < len(test_queries):
            print("⏳ Waiting 30 seconds between tests...")
            time.sleep(30)

def test_user_profile_adaptation():
    """Test how the system adapts to different user profiles"""
    print("\n👤 Testing User Profile Adaptation")
    print("=" * 60)
    
    analyzer = AdvancedQueryAnalyzer()
    
    # Same topic, different user perspectives
    base_topic = "universities in canada"
    
    profile_queries = [
        ("prospective student", "I want to apply to universities in canada"),
        ("parent", "best universities in canada for my daughter"),
        ("researcher", "research universities in canada for faculty positions"),
        ("current student", "transfer to universities in canada from us"),
        ("beginner", "what are universities in canada like"),
        ("advanced", "specific computer science doctoral programs universities canada")
    ]
    
    for profile_type, query in profile_queries:
        print(f"\n--- {profile_type.title()} Query ---")
        print(f"Query: {query}")
        
        context = analyzer.analyze_query(query)
        
        print(f"🎯 Detected Profile: {context.user_profile}")
        print(f"📊 Experience Level: {context.experience_level}")
        print(f"📝 Query Type: {context.query_type}")
        print(f"📏 Information Depth: {context.information_depth}")
        print(f"🎯 Specificity: {context.search_specificity:.2f}")
        
        if context.synonyms:
            print(f"🔄 Generated Synonyms: {', '.join(list(context.synonyms)[:3])}")
        
        print("-" * 40)

def test_multilingual_recognition():
    """Test multilingual query recognition and handling"""
    print("\n🌍 Testing Multilingual Recognition")
    print("=" * 60)
    
    analyzer = AdvancedQueryAnalyzer()
    
    multilingual_queries = [
        ("English", "universities in germany"),
        ("French", "université en france engineering programs"),
        ("German", "universität deutschland studium computer science"),
        ("Spanish", "universidad en españa medicina"),
        ("Mixed", "université germany english taught programs")
    ]
    
    for lang_label, query in multilingual_queries:
        print(f"\n--- {lang_label} Query ---")
        print(f"Query: {query}")
        
        context = analyzer.analyze_query(query)
        
        print(f"🔤 Detected Language: {context.language}")
        print(f"🌍 Target Countries: {', '.join(context.target_countries) if context.target_countries else 'None'}")
        print(f"🗣️ Language Requirements: {', '.join(context.language_requirements) if context.language_requirements else 'None'}")
        print(f"📚 Academic Fields: {', '.join(context.academic_fields) if context.academic_fields else 'None'}")
        
        print("-" * 40)

def main():
    """Run all advanced recognition tests"""
    print("🧪 UniScholar Advanced Recognition Test Suite")
    print("=" * 70)
    print("Testing multiple recognition techniques for improved search alignment")
    print("=" * 70)
    
    try:
        # Test 1: Query Understanding
        test_query_understanding_variations()
        
        # Test 2: Result Ranking
        test_result_ranking_enhancement()
        
        # Test 3: User Profile Adaptation
        test_user_profile_adaptation()
        
        # Test 4: Multilingual Recognition
        test_multilingual_recognition()
        
        # Test 5: Comprehensive Enhancement (with real searches)
        test_comprehensive_search_enhancement()
        
        print("\n✅ All advanced recognition tests completed!")
        print("📄 Check 'advanced_recognition_test.log' for detailed logs")
        
        print("\n🎯 Key Recognition Improvements Demonstrated:")
        print("   • Multi-dimensional query understanding")
        print("   • Context-aware result ranking")
        print("   • User profile and experience level inference")
        print("   • Geographic and temporal pattern recognition")
        print("   • Academic level and field detection")
        print("   • Query expansion with synonyms and related terms")
        print("   • Multilingual query support")
        print("   • Authority and credibility scoring")
        print("   • Comprehensive relevance calculation")
        
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        logging.exception("Test suite error")

if __name__ == "__main__":
    main() 