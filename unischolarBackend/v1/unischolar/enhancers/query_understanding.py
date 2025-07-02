"""
Advanced Query Understanding and Recognition System for UniScholar

This module implements sophisticated recognition techniques to improve
search result alignment with user queries through:
- Semantic query analysis
- Multi-language recognition  
- Academic context understanding
- Temporal pattern recognition
- Query expansion and synonyms
- Geographic education system awareness
"""

import re
import logging
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import json

@dataclass
class QueryContext:
    """Comprehensive context analysis of user query"""
    # Core query analysis
    original_query: str
    cleaned_query: str
    language: str
    query_type: str
    
    # Academic context
    academic_level: Set[str] = field(default_factory=set)  # bachelor, master, phd, etc.
    academic_fields: Set[str] = field(default_factory=set)  # engineering, medicine, etc.
    study_mode: Set[str] = field(default_factory=set)  # online, campus, hybrid
    
    # Geographic context
    target_countries: Set[str] = field(default_factory=set)
    target_regions: Set[str] = field(default_factory=set)
    language_requirements: Set[str] = field(default_factory=set)
    
    # Temporal context
    deadline_urgency: str = 'unknown'  # immediate, next_semester, next_year, flexible
    academic_year_context: str = 'unknown'  # fall2024, spring2025, etc.
    
    # Intent specificity
    search_specificity: float = 0.5  # 0.0 = very broad, 1.0 = very specific
    information_depth: str = 'overview'  # overview, detailed, comprehensive
    
    # User profile inference
    user_profile: str = 'unknown'  # prospective_student, current_student, researcher, parent
    experience_level: str = 'unknown'  # beginner, intermediate, advanced
    
    # Expanded terms
    synonyms: Set[str] = field(default_factory=set)
    related_terms: Set[str] = field(default_factory=set)
    domain_specific_terms: Set[str] = field(default_factory=set)

@dataclass
class ResultRelevanceScore:
    """Comprehensive relevance scoring for search results"""
    url: str
    overall_score: float
    component_scores: Dict[str, float] = field(default_factory=dict)
    confidence: float = 0.0
    explanation: List[str] = field(default_factory=list)

class AdvancedQueryAnalyzer:
    """Advanced query analysis using multiple recognition techniques"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self._load_knowledge_bases()
        
    def _load_knowledge_bases(self):
        """Load comprehensive knowledge bases for recognition"""
        
        # Academic level patterns
        self.academic_levels = {
            'undergraduate': ['bachelor', 'undergraduate', 'bachelors', 'bs', 'ba', 'bsc', 'first degree'],
            'graduate': ['master', 'masters', 'graduate', 'ms', 'ma', 'msc', 'postgraduate'],
            'doctoral': ['phd', 'doctorate', 'doctoral', 'dphil', 'doctor of philosophy'],
            'professional': ['mba', 'md', 'jd', 'law school', 'medical school', 'business school'],
            'certificate': ['certificate', 'diploma', 'certification', 'short course'],
            'exchange': ['exchange', 'study abroad', 'semester abroad', 'year abroad']
        }
        
        # Academic fields with synonyms
        self.academic_fields = {
            'engineering': ['engineering', 'technical', 'engineering technology', 'applied sciences'],
            'computer_science': ['computer science', 'cs', 'computing', 'informatics', 'software', 'it'],
            'medicine': ['medicine', 'medical', 'health sciences', 'healthcare', 'nursing', 'pharmacy'],
            'business': ['business', 'management', 'finance', 'economics', 'accounting', 'marketing'],
            'arts': ['arts', 'humanities', 'liberal arts', 'fine arts', 'literature', 'philosophy'],
            'sciences': ['science', 'biology', 'chemistry', 'physics', 'mathematics', 'natural sciences'],
            'social_sciences': ['psychology', 'sociology', 'anthropology', 'political science', 'social work'],
            'education': ['education', 'teaching', 'pedagogy', 'educational sciences', 'teacher training'],
            'law': ['law', 'legal studies', 'jurisprudence', 'legal science'],
            'agriculture': ['agriculture', 'farming', 'agricultural sciences', 'agronomy', 'veterinary']
        }
        
        # Geographic education systems
        self.education_systems = {
            'us': {
                'terms': ['usa', 'united states', 'america', 'american'],
                'levels': ['freshman', 'sophomore', 'junior', 'senior', 'grad school'],
                'degrees': ['associate', 'bachelor', 'master', 'doctorate'],
                'institutions': ['college', 'university', 'community college', 'liberal arts college']
            },
            'uk': {
                'terms': ['uk', 'united kingdom', 'britain', 'british', 'england', 'scotland', 'wales'],
                'levels': ['foundation', 'undergraduate', 'postgraduate', 'research'],
                'degrees': ['certificate', 'diploma', 'bachelor', 'master', 'phd'],
                'institutions': ['university', 'college', 'polytechnic', 'sixth form']
            },
            'europe': {
                'terms': ['europe', 'european', 'eu', 'bologna', 'erasmus'],
                'levels': ['bachelor', 'master', 'doctorate'],
                'degrees': ['licence', 'master', 'doctorat', 'laurea', 'magistrale'],
                'institutions': ['université', 'università', 'universität', 'universidad']
            },
            'canada': {
                'terms': ['canada', 'canadian'],
                'levels': ['undergraduate', 'graduate', 'postgraduate'],
                'degrees': ['certificate', 'diploma', 'bachelor', 'master', 'phd'],
                'institutions': ['university', 'college', 'institute', 'école']
            }
        }
        
        # Temporal patterns
        self.temporal_patterns = {
            'urgent': ['asap', 'urgent', 'immediate', 'deadline soon', 'this month'],
            'current_year': ['2024', '2025', 'this year', 'current'],
            'next_semester': ['next semester', 'upcoming', 'soon', 'next term'],
            'planning_ahead': ['next year', '2026', 'future', 'planning'],
            'academic_seasons': {
                'fall': ['fall', 'autumn', 'september', 'october'],
                'spring': ['spring', 'january', 'february', 'march'],
                'summer': ['summer', 'june', 'july', 'august']
            }
        }
        
        # Query expansion dictionaries
        self.university_synonyms = {
            'university': ['college', 'institute', 'school', 'academy', 'polytechnic'],
            'college': ['university', 'institute', 'school'],
            'school': ['university', 'college', 'institute', 'academy'],
            'program': ['course', 'degree', 'major', 'study', 'field'],
            'scholarship': ['grant', 'funding', 'financial aid', 'bursary', 'fellowship'],
            'admission': ['application', 'entry', 'enrollment', 'acceptance']
        }
        
        # Quality indicators for institutions
        self.quality_indicators = {
            'rankings': ['top', 'best', 'ranked', 'ranking', 'prestigious', 'elite'],
            'accreditation': ['accredited', 'recognized', 'certified', 'approved'],
            'reputation': ['renowned', 'famous', 'well-known', 'respected', 'leading'],
            'research': ['research', 'r1', 'research-intensive', 'doctoral', 'phd-granting']
        }

    def analyze_query(self, query: str) -> QueryContext:
        """Perform comprehensive query analysis"""
        logging.info(f"🔍 Analyzing query: '{query}'")
        
        context = QueryContext(
            original_query=query,
            cleaned_query=self._clean_query(query),
            language=self._detect_language(query),
            query_type=self._classify_query_type(query)
        )
        
        # Academic context analysis
        context.academic_level = self._extract_academic_level(query)
        context.academic_fields = self._extract_academic_fields(query)
        context.study_mode = self._extract_study_mode(query)
        
        # Geographic analysis
        context.target_countries = self._extract_countries(query)
        context.target_regions = self._extract_regions(query)
        context.language_requirements = self._extract_language_requirements(query)
        
        # Temporal analysis
        context.deadline_urgency = self._analyze_deadline_urgency(query)
        context.academic_year_context = self._extract_academic_year(query)
        
        # Intent analysis
        context.search_specificity = self._calculate_specificity(query)
        context.information_depth = self._determine_information_depth(query)
        
        # User profiling
        context.user_profile = self._infer_user_profile(query)
        context.experience_level = self._infer_experience_level(query)
        
        # Query expansion
        context.synonyms = self._generate_synonyms(query)
        context.related_terms = self._generate_related_terms(query)
        context.domain_specific_terms = self._generate_domain_terms(query, context)
        
        self._log_query_analysis(context)
        return context
    
    def _clean_query(self, query: str) -> str:
        """Clean and normalize query text"""
        # Remove extra whitespace, normalize case
        cleaned = re.sub(r'\s+', ' ', query.strip().lower())
        
        # Remove common stop words that don't add meaning
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with'}
        words = cleaned.split()
        cleaned_words = [word for word in words if word not in stop_words or len(words) <= 3]
        
        return ' '.join(cleaned_words)
    
    def _detect_language(self, query: str) -> str:
        """Detect query language for multilingual support"""
        # Simple language detection based on common patterns
        if re.search(r'université|école|études', query.lower()):
            return 'french'
        elif re.search(r'universität|studium|hochschule', query.lower()):
            return 'german'
        elif re.search(r'università|università|corso', query.lower()):
            return 'italian'
        elif re.search(r'universidad|estudios|carrera', query.lower()):
            return 'spanish'
        else:
            return 'english'
    
    def _classify_query_type(self, query: str) -> str:
        """Classify the type of query for better processing"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['scholarship', 'funding', 'grant', 'financial aid']):
            return 'funding_search'
        elif any(word in query_lower for word in ['admission', 'application', 'requirements', 'entry']):
            return 'admission_info'
        elif any(word in query_lower for word in ['ranking', 'best', 'top', 'compare']):
            return 'comparison_search'
        elif any(word in query_lower for word in ['program', 'course', 'major', 'degree']):
            return 'program_search'
        elif any(word in query_lower for word in ['university', 'college', 'school', 'institute']):
            return 'institution_search'
        else:
            return 'general_search'
    
    def _extract_academic_level(self, query: str) -> Set[str]:
        """Extract academic level indicators from query"""
        levels = set()
        query_lower = query.lower()
        
        for level, keywords in self.academic_levels.items():
            if any(keyword in query_lower for keyword in keywords):
                levels.add(level)
        
        return levels
    
    def _extract_academic_fields(self, query: str) -> Set[str]:
        """Extract academic field indicators from query"""
        fields = set()
        query_lower = query.lower()
        
        for field, keywords in self.academic_fields.items():
            if any(keyword in query_lower for keyword in keywords):
                fields.add(field)
        
        return fields
    
    def _extract_study_mode(self, query: str) -> Set[str]:
        """Extract study mode preferences from query"""
        modes = set()
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['online', 'distance', 'remote', 'virtual']):
            modes.add('online')
        if any(word in query_lower for word in ['campus', 'on-campus', 'traditional', 'in-person']):
            modes.add('campus')
        if any(word in query_lower for word in ['hybrid', 'blended', 'mixed']):
            modes.add('hybrid')
        if any(word in query_lower for word in ['part-time', 'evening', 'weekend']):
            modes.add('part_time')
        if any(word in query_lower for word in ['full-time', 'intensive']):
            modes.add('full_time')
        
        return modes
    
    def _extract_countries(self, query: str) -> Set[str]:
        """Extract target country preferences from query"""
        countries = set()
        query_lower = query.lower()
        
        # Common country patterns
        country_patterns = {
            'usa': ['usa', 'united states', 'america', 'american', 'us'],
            'uk': ['uk', 'united kingdom', 'britain', 'british', 'england', 'scotland', 'wales'],
            'canada': ['canada', 'canadian'],
            'australia': ['australia', 'australian', 'aussie'],
            'germany': ['germany', 'german', 'deutschland'],
            'france': ['france', 'french'],
            'italy': ['italy', 'italian'],
            'spain': ['spain', 'spanish'],
            'netherlands': ['netherlands', 'dutch', 'holland'],
            'sweden': ['sweden', 'swedish'],
            'norway': ['norway', 'norwegian'],
            'denmark': ['denmark', 'danish'],
            'finland': ['finland', 'finnish'],
            'japan': ['japan', 'japanese'],
            'south_korea': ['south korea', 'korea', 'korean'],
            'china': ['china', 'chinese'],
            'singapore': ['singapore'],
            'new_zealand': ['new zealand', 'nz']
        }
        
        for country, patterns in country_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                countries.add(country)
        
        return countries
    
    def _extract_regions(self, query: str) -> Set[str]:
        """Extract regional preferences from query"""
        regions = set()
        query_lower = query.lower()
        
        region_patterns = {
            'europe': ['europe', 'european', 'eu'],
            'north_america': ['north america', 'north american'],
            'asia': ['asia', 'asian'],
            'oceania': ['oceania', 'pacific'],
            'scandinavia': ['scandinavia', 'scandinavian', 'nordic'],
            'middle_east': ['middle east', 'gulf'],
            'latin_america': ['latin america', 'south america']
        }
        
        for region, patterns in region_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                regions.add(region)
        
        return regions
    
    def _extract_language_requirements(self, query: str) -> Set[str]:
        """Extract language preferences from query"""
        languages = set()
        query_lower = query.lower()
        
        language_patterns = {
            'english': ['english', 'english-taught', 'in english'],
            'german': ['german', 'deutsch', 'german-taught'],
            'french': ['french', 'français', 'french-taught'],
            'spanish': ['spanish', 'español', 'spanish-taught'],
            'italian': ['italian', 'italiano'],
            'dutch': ['dutch', 'nederlands'],
            'swedish': ['swedish', 'svenska'],
            'norwegian': ['norwegian', 'norsk'],
            'danish': ['danish', 'dansk']
        }
        
        for language, patterns in language_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                languages.add(language)
        
        return languages
    
    def _analyze_deadline_urgency(self, query: str) -> str:
        """Analyze urgency of deadlines mentioned in query"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in self.temporal_patterns['urgent']):
            return 'immediate'
        elif any(word in query_lower for word in self.temporal_patterns['next_semester']):
            return 'next_semester'
        elif any(word in query_lower for word in self.temporal_patterns['planning_ahead']):
            return 'next_year'
        else:
            return 'flexible'
    
    def _extract_academic_year(self, query: str) -> str:
        """Extract academic year context from query"""
        current_year = datetime.now().year
        query_lower = query.lower()
        
        # Look for specific years
        for year in range(current_year, current_year + 3):
            if str(year) in query_lower:
                return f"year_{year}"
        
        # Look for semester patterns
        for season, keywords in self.temporal_patterns['academic_seasons'].items():
            if any(keyword in query_lower for keyword in keywords):
                return f"{season}_{current_year}"
        
        return 'unknown'
    
    def _calculate_specificity(self, query: str) -> float:
        """Calculate how specific the query is"""
        specificity_factors = []
        
        # Length factor (longer queries tend to be more specific)
        words = query.split()
        length_specificity = min(len(words) / 10.0, 1.0)  # Cap at 1.0
        specificity_factors.append(length_specificity)
        
        # Presence of specific terms
        specific_terms = ['program', 'major', 'phd', 'master', 'bachelor', 'scholarship', 'requirements']
        specific_term_count = sum(1 for term in specific_terms if term in query.lower())
        term_specificity = min(specific_term_count / 5.0, 1.0)
        specificity_factors.append(term_specificity)
        
        # Geographic specificity
        has_location = bool(self._extract_countries(query) or self._extract_regions(query))
        geographic_specificity = 0.3 if has_location else 0.0
        specificity_factors.append(geographic_specificity)
        
        return sum(specificity_factors) / len(specificity_factors)
    
    def _determine_information_depth(self, query: str) -> str:
        """Determine what level of information depth user wants"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['detailed', 'comprehensive', 'complete', 'all about']):
            return 'comprehensive'
        elif any(word in query_lower for word in ['requirements', 'how to', 'process', 'steps']):
            return 'detailed'
        elif any(word in query_lower for word in ['list', 'overview', 'general', 'basic']):
            return 'overview'
        else:
            return 'overview'
    
    def _infer_user_profile(self, query: str) -> str:
        """Infer user profile from query patterns"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['my son', 'my daughter', 'my child', 'for my kid']):
            return 'parent'
        elif any(word in query_lower for word in ['transfer', 'changing', 'current student']):
            return 'current_student'
        elif any(word in query_lower for word in ['research', 'faculty', 'professor', 'postdoc']):
            return 'researcher'
        elif any(word in query_lower for word in ['apply', 'applying', 'want to study', 'planning to']):
            return 'prospective_student'
        else:
            return 'unknown'
    
    def _infer_experience_level(self, query: str) -> str:
        """Infer user's experience level with higher education"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['what is', 'how does', 'explain', 'basics']):
            return 'beginner'
        elif any(word in query_lower for word in ['compare', 'difference between', 'vs']):
            return 'intermediate'
        elif any(word in query_lower for word in ['specific', 'particular', 'advanced', 'specialized']):
            return 'advanced'
        else:
            return 'intermediate'
    
    def _generate_synonyms(self, query: str) -> Set[str]:
        """Generate query synonyms for better matching"""
        synonyms = set()
        query_words = query.lower().split()
        
        for word in query_words:
            if word in self.university_synonyms:
                synonyms.update(self.university_synonyms[word])
        
        return synonyms
    
    def _generate_related_terms(self, query: str) -> Set[str]:
        """Generate related terms based on query context"""
        related = set()
        query_lower = query.lower()
        
        # Add related academic terms
        if 'university' in query_lower or 'college' in query_lower:
            related.update(['higher education', 'academic institution', 'campus'])
        
        if 'scholarship' in query_lower:
            related.update(['financial aid', 'tuition assistance', 'grant', 'fellowship'])
        
        if 'program' in query_lower:
            related.update(['curriculum', 'course of study', 'major', 'degree'])
        
        return related
    
    def _generate_domain_terms(self, query: str, context: QueryContext) -> Set[str]:
        """Generate domain-specific terms based on context"""
        domain_terms = set()
        
        # Add field-specific terms
        for field in context.academic_fields:
            if field == 'engineering':
                domain_terms.update(['STEM', 'technical', 'applied sciences'])
            elif field == 'medicine':
                domain_terms.update(['health sciences', 'clinical', 'medical school'])
            elif field == 'business':
                domain_terms.update(['management', 'commerce', 'business school'])
        
        # Add level-specific terms
        for level in context.academic_level:
            if level == 'graduate':
                domain_terms.update(['postgraduate', 'graduate school'])
            elif level == 'doctoral':
                domain_terms.update(['research', 'dissertation', 'thesis'])
        
        return domain_terms
    
    def _log_query_analysis(self, context: QueryContext):
        """Log comprehensive query analysis results"""
        logging.info("🧠 Advanced Query Analysis Results:")
        logging.info(f"   🔤 Language: {context.language}")
        logging.info(f"   📝 Query Type: {context.query_type}")
        logging.info(f"   🎓 Academic Levels: {context.academic_level}")
        logging.info(f"   📚 Academic Fields: {context.academic_fields}")
        logging.info(f"   🌍 Target Countries: {context.target_countries}")
        logging.info(f"   🗣️ Language Requirements: {context.language_requirements}")
        logging.info(f"   ⏰ Deadline Urgency: {context.deadline_urgency}")
        logging.info(f"   🎯 Specificity: {context.search_specificity:.2f}")
        logging.info(f"   👤 User Profile: {context.user_profile}")
        logging.info(f"   📊 Experience Level: {context.experience_level}")
        
        if context.synonyms:
            logging.info(f"   🔄 Synonyms: {list(context.synonyms)[:5]}...")
        if context.related_terms:
            logging.info(f"   🔗 Related Terms: {list(context.related_terms)[:5]}...")


class IntelligentResultRanker:
    """Advanced result ranking using multiple recognition signals"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self._load_ranking_knowledge()
    
    def _load_ranking_knowledge(self):
        """Load knowledge bases for intelligent ranking"""
        
        # Authority indicators for different domains
        self.authority_domains = {
            'edu': 1.0,      # Educational institutions
            'gov': 0.9,      # Government sources
            'org': 0.7,      # Non-profit organizations
            'ac': 1.0,       # Academic domains (international)
            'com': 0.3       # Commercial domains
        }
        
        # URL quality patterns
        self.quality_url_patterns = {
            'official': r'(admissions|apply|programs|academics|study)',
            'university_direct': r'(\.edu|\.ac\.|university|college)',
            'government': r'(\.gov|education\.)',
            'ranking_sites': r'(topuniversities|usnews|qs|times)',
            'scholarship_sites': r'(scholarship|grant|funding)',
            'spam_indicators': r'(top10|best.*ever|amazing|incredible)'
        }
        
        # Content quality indicators
        self.content_quality_signals = {
            'structured_data': 0.3,
            'contact_information': 0.2,
            'official_links': 0.25,
            'comprehensive_info': 0.15,
            'recent_updates': 0.1
        }
    
    def rank_results(self, search_results: List[Dict], query_context: QueryContext, 
                    ner_result: Any = None) -> List[ResultRelevanceScore]:
        """Perform intelligent ranking of search results"""
        
        ranked_results = []
        
        for result in search_results:
            url = result.get('url', '')
            title = result.get('title', '')
            abstract = result.get('abstract', '')
            
            # Calculate comprehensive relevance score
            relevance_score = self._calculate_comprehensive_relevance(
                url, title, abstract, query_context, ner_result
            )
            
            ranked_results.append(relevance_score)
        
        # Sort by overall score
        ranked_results.sort(key=lambda x: x.overall_score, reverse=True)
        
        self._log_ranking_results(ranked_results[:5])  # Log top 5
        
        return ranked_results
    
    def _calculate_comprehensive_relevance(self, url: str, title: str, abstract: str, 
                                         query_context: QueryContext, ner_result: Any) -> ResultRelevanceScore:
        """Calculate comprehensive relevance score using multiple signals"""
        
        component_scores = {}
        explanations = []
        
        # 1. NER-based relevance (if available)
        if ner_result and hasattr(ner_result, 'relevance_scores'):
            ner_score = ner_result.relevance_scores.get(url, 0.0)
            component_scores['ner_relevance'] = ner_score
            if ner_score > 0.5:
                explanations.append(f"High NER relevance ({ner_score:.2f})")
        
        # 2. Query-content semantic alignment
        semantic_score = self._calculate_semantic_alignment(title, abstract, query_context)
        component_scores['semantic_alignment'] = semantic_score
        if semantic_score > 0.6:
            explanations.append(f"Strong semantic match ({semantic_score:.2f})")
        
        # 3. Authority and credibility
        authority_score = self._calculate_authority_score(url, title)
        component_scores['authority'] = authority_score
        if authority_score > 0.7:
            explanations.append(f"High authority source ({authority_score:.2f})")
        
        # 4. Geographic relevance
        geographic_score = self._calculate_geographic_relevance(url, title, abstract, query_context)
        component_scores['geographic_relevance'] = geographic_score
        if geographic_score > 0.5:
            explanations.append(f"Geographic match ({geographic_score:.2f})")
        
        # 5. Academic level appropriateness
        level_score = self._calculate_level_appropriateness(title, abstract, query_context)
        component_scores['level_appropriateness'] = level_score
        if level_score > 0.6:
            explanations.append(f"Appropriate academic level ({level_score:.2f})")
        
        # 6. Temporal relevance
        temporal_score = self._calculate_temporal_relevance(title, abstract, query_context)
        component_scores['temporal_relevance'] = temporal_score
        if temporal_score > 0.5:
            explanations.append(f"Temporally relevant ({temporal_score:.2f})")
        
        # 7. Content comprehensiveness
        comprehensiveness_score = self._calculate_comprehensiveness(title, abstract, query_context)
        component_scores['comprehensiveness'] = comprehensiveness_score
        
        # 8. User profile alignment
        profile_score = self._calculate_profile_alignment(title, abstract, query_context)
        component_scores['profile_alignment'] = profile_score
        
        # Calculate weighted overall score
        weights = {
            'ner_relevance': 0.20,
            'semantic_alignment': 0.25,
            'authority': 0.15,
            'geographic_relevance': 0.10,
            'level_appropriateness': 0.10,
            'temporal_relevance': 0.05,
            'comprehensiveness': 0.10,
            'profile_alignment': 0.05
        }
        
        overall_score = sum(
            component_scores.get(component, 0.0) * weight 
            for component, weight in weights.items()
        )
        
        # Calculate confidence based on number of strong signals
        strong_signals = sum(1 for score in component_scores.values() if score > 0.6)
        confidence = min(strong_signals / len(component_scores), 1.0)
        
        return ResultRelevanceScore(
            url=url,
            overall_score=overall_score,
            component_scores=component_scores,
            confidence=confidence,
            explanation=explanations
        )
    
    def _calculate_semantic_alignment(self, title: str, abstract: str, context: QueryContext) -> float:
        """Calculate semantic alignment between content and query"""
        content = f"{title} {abstract}".lower()
        query_terms = set(context.cleaned_query.split())
        
        # Direct term matches
        direct_matches = sum(1 for term in query_terms if term in content)
        direct_score = direct_matches / len(query_terms) if query_terms else 0
        
        # Synonym matches
        synonym_matches = sum(1 for synonym in context.synonyms if synonym in content)
        synonym_score = (synonym_matches / len(context.synonyms)) * 0.8 if context.synonyms else 0
        
        # Related term matches
        related_matches = sum(1 for term in context.related_terms if term in content)
        related_score = (related_matches / len(context.related_terms)) * 0.6 if context.related_terms else 0
        
        # Academic field alignment
        field_score = 0
        for field in context.academic_fields:
            field_keywords = self._get_field_keywords(field)
            field_matches = sum(1 for keyword in field_keywords if keyword in content)
            field_score += (field_matches / len(field_keywords)) * 0.7
        
        field_score = min(field_score, 1.0)
        
        return (direct_score + synonym_score + related_score + field_score) / 4
    
    def _calculate_authority_score(self, url: str, title: str) -> float:
        """Calculate authority and credibility score"""
        score = 0.0
        
        # Domain authority
        for domain_suffix, domain_score in self.authority_domains.items():
            if f'.{domain_suffix}' in url.lower():
                score += domain_score * 0.4
                break
        
        # URL quality patterns
        for pattern_name, pattern in self.quality_url_patterns.items():
            if re.search(pattern, url.lower()):
                if pattern_name in ['official', 'university_direct']:
                    score += 0.3
                elif pattern_name in ['government', 'ranking_sites']:
                    score += 0.2
                elif pattern_name == 'spam_indicators':
                    score -= 0.2  # Penalty for spam indicators
        
        # Title authority indicators
        authority_words = ['official', 'university', 'college', 'institute', 'government']
        title_authority = sum(1 for word in authority_words if word in title.lower())
        score += min(title_authority * 0.1, 0.3)
        
        return min(max(score, 0.0), 1.0)  # Clamp between 0 and 1
    
    def _calculate_geographic_relevance(self, url: str, title: str, abstract: str, 
                                      context: QueryContext) -> float:
        """Calculate geographic relevance score"""
        if not context.target_countries and not context.target_regions:
            return 0.5  # Neutral score if no geographic preference
        
        content = f"{url} {title} {abstract}".lower()
        score = 0.0
        
        # Country matches
        country_matches = sum(1 for country in context.target_countries 
                            if country.replace('_', ' ') in content)
        if context.target_countries:
            score += (country_matches / len(context.target_countries)) * 0.7
        
        # Region matches  
        region_matches = sum(1 for region in context.target_regions 
                           if region.replace('_', ' ') in content)
        if context.target_regions:
            score += (region_matches / len(context.target_regions)) * 0.5
        
        # Country code in URL (strong signal)
        for country in context.target_countries:
            country_codes = self._get_country_codes(country)
            for code in country_codes:
                if f'.{code}' in url:
                    score += 0.8
                    break
        
        return min(score, 1.0)
    
    def _calculate_level_appropriateness(self, title: str, abstract: str, context: QueryContext) -> float:
        """Calculate academic level appropriateness"""
        if not context.academic_level:
            return 0.5  # Neutral if no level specified
        
        content = f"{title} {abstract}".lower()
        score = 0.0
        
        for level in context.academic_level:
            level_keywords = self._get_level_keywords(level)
            level_matches = sum(1 for keyword in level_keywords if keyword in content)
            score += (level_matches / len(level_keywords)) * (1.0 / len(context.academic_level))
        
        return min(score, 1.0)
    
    def _calculate_temporal_relevance(self, title: str, abstract: str, context: QueryContext) -> float:
        """Calculate temporal relevance based on deadlines and dates"""
        content = f"{title} {abstract}".lower()
        current_year = datetime.now().year
        
        # Look for current/recent years
        year_mentions = re.findall(r'\b(202[0-9])\b', content)
        recent_years = [year for year in year_mentions if int(year) >= current_year - 1]
        
        # Base score for recent content
        if recent_years:
            score = 0.7
        else:
            score = 0.3
        
        # Boost for deadline urgency alignment
        if context.deadline_urgency == 'immediate':
            urgent_keywords = ['apply now', 'deadline', 'closing soon', 'urgent']
            if any(keyword in content for keyword in urgent_keywords):
                score += 0.3
        
        return min(score, 1.0)
    
    def _calculate_comprehensiveness(self, title: str, abstract: str, context: QueryContext) -> float:
        """Calculate content comprehensiveness score"""
        content = f"{title} {abstract}"
        
        # Length indicator
        length_score = min(len(content) / 500, 1.0)  # Normalize to 500 chars
        
        # Information depth alignment
        if context.information_depth == 'comprehensive':
            depth_keywords = ['detailed', 'complete', 'comprehensive', 'guide', 'everything']
            depth_score = sum(1 for keyword in depth_keywords if keyword in content.lower()) * 0.2
        elif context.information_depth == 'detailed':
            depth_keywords = ['requirements', 'process', 'how to', 'steps', 'procedure']
            depth_score = sum(1 for keyword in depth_keywords if keyword in content.lower()) * 0.2
        else:  # overview
            depth_keywords = ['overview', 'introduction', 'basics', 'summary']
            depth_score = sum(1 for keyword in depth_keywords if keyword in content.lower()) * 0.2
        
        return (length_score + min(depth_score, 1.0)) / 2
    
    def _calculate_profile_alignment(self, title: str, abstract: str, context: QueryContext) -> float:
        """Calculate alignment with inferred user profile"""
        content = f"{title} {abstract}".lower()
        
        profile_keywords = {
            'prospective_student': ['admission', 'apply', 'application', 'requirements', 'how to'],
            'current_student': ['transfer', 'change', 'switch', 'current students'],
            'parent': ['parents', 'family', 'guide for parents', 'choosing'],
            'researcher': ['research', 'faculty', 'phd', 'postdoc', 'academic']
        }
        
        if context.user_profile in profile_keywords:
            keywords = profile_keywords[context.user_profile]
            matches = sum(1 for keyword in keywords if keyword in content)
            return min(matches / len(keywords), 1.0)
        
        return 0.5  # Neutral for unknown profiles
    
    def _get_field_keywords(self, field: str) -> List[str]:
        """Get keywords for academic field"""
        field_keywords = {
            'engineering': ['engineering', 'technical', 'technology', 'applied sciences'],
            'computer_science': ['computer', 'computing', 'software', 'programming', 'it'],
            'medicine': ['medical', 'medicine', 'health', 'healthcare', 'clinical'],
            'business': ['business', 'management', 'finance', 'economics', 'mba'],
            'arts': ['arts', 'humanities', 'literature', 'philosophy', 'history'],
            'sciences': ['science', 'biology', 'chemistry', 'physics', 'mathematics']
        }
        return field_keywords.get(field, [])
    
    def _get_level_keywords(self, level: str) -> List[str]:
        """Get keywords for academic level"""
        level_keywords = {
            'undergraduate': ['bachelor', 'undergraduate', 'bachelors', 'first degree'],
            'graduate': ['master', 'graduate', 'masters', 'postgraduate'],
            'doctoral': ['phd', 'doctorate', 'doctoral', 'doctor'],
            'professional': ['professional', 'mba', 'law', 'medical school']
        }
        return level_keywords.get(level, [])
    
    def _get_country_codes(self, country: str) -> List[str]:
        """Get country codes for URL matching"""
        country_codes = {
            'usa': ['us'],
            'uk': ['uk'],
            'canada': ['ca'],
            'australia': ['au'],
            'germany': ['de'],
            'france': ['fr'],
            'italy': ['it'],
            'spain': ['es'],
            'netherlands': ['nl'],
            'sweden': ['se'],
            'norway': ['no'],
            'denmark': ['dk'],
            'finland': ['fi']
        }
        return country_codes.get(country, [])
    
    def _log_ranking_results(self, top_results: List[ResultRelevanceScore]):
        """Log top ranking results"""
        logging.info("🏆 Top Ranked Results:")
        for i, result in enumerate(top_results, 1):
            logging.info(f"   {i}. Score: {result.overall_score:.3f} | {result.url[:50]}...")
            if result.explanation:
                logging.info(f"      Reasons: {', '.join(result.explanation[:2])}") 