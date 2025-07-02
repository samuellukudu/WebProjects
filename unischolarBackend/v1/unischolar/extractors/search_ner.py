"""
Advanced Named Entity Recognition for Search Results and User Queries
Analyzes DuckDuckGo search results and user queries to extract educational entities
and improve content relevance scoring.
"""

import spacy
import re
import json
import logging
from typing import List, Dict, Set, Optional, Tuple, Union
from dataclasses import dataclass, field
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import dateutil.parser as date_parser

# Load spaCy model for NLP processing
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logging.warning("spaCy English model not found. Install with: python -m spacy download en_core_web_sm")
    nlp = None

@dataclass
class ExtractedEntity:
    """Represents an extracted entity with context"""
    text: str
    label: str
    confidence: float
    start_pos: int = 0
    end_pos: int = 0
    context: str = ""
    source: str = ""  # 'query' or 'search_result'
    
@dataclass
class EducationalEntities:
    """Container for all educational entities extracted from text"""
    universities: List[ExtractedEntity] = field(default_factory=list)
    scholarships: List[ExtractedEntity] = field(default_factory=list)
    programs: List[ExtractedEntity] = field(default_factory=list)
    locations: List[ExtractedEntity] = field(default_factory=list)
    subjects: List[ExtractedEntity] = field(default_factory=list)
    degrees: List[ExtractedEntity] = field(default_factory=list)
    deadlines: List[ExtractedEntity] = field(default_factory=list)
    amounts: List[ExtractedEntity] = field(default_factory=list)
    events: List[ExtractedEntity] = field(default_factory=list)
    people: List[ExtractedEntity] = field(default_factory=list)
    organizations: List[ExtractedEntity] = field(default_factory=list)
    
@dataclass
class SearchNERResult:
    """Result of NER analysis on search results and query"""
    query_entities: EducationalEntities
    search_entities: List[Tuple[str, EducationalEntities]]  # (url, entities)
    relevance_scores: Dict[str, float]
    intent_analysis: Dict[str, any]
    entity_matches: Dict[str, List[str]]  # query entity -> matching search entities

class SearchNERProcessor:
    """Advanced NER processor for search results and queries"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.nlp = nlp
        self.config = config or {}
        
        # Educational entity patterns
        self.education_patterns = {
            'university': [
                r'\b(?:university|université|universidad|università|universität)\s+(?:of\s+)?([A-Z][a-zA-Z\s,]+)',
                r'\b([A-Z][a-zA-Z\s]+)\s+(?:university|université|universidad|università|universität)\b',
                r'\b([A-Z][a-zA-Z\s]+)\s+(?:college|institute|school)\b',
                r'\b(?:technical\s+university|polytechnic|institute\s+of\s+technology)\s+(?:of\s+)?([A-Z][a-zA-Z\s]+)',
            ],
            'scholarship': [
                r'\b([A-Z][a-zA-Z\s]+)\s+(?:scholarship|fellowship|grant|award)\b',
                r'\b(?:scholarship|fellowship|grant|award)\s+(?:for\s+)?([A-Z][a-zA-Z\s]+)',
                r'\b([A-Z][a-zA-Z\s]+)\s+(?:scholarship\s+program|fellowship\s+program)\b',
                r'\b(?:merit|need-based|full|partial)\s+scholarship\b',
            ],
            'program': [
                r'\b([A-Z][a-zA-Z\s]+)\s+(?:program|degree|major|course)\b',
                r'\b(?:bachelor|master|phd|doctoral)\s+(?:of\s+|in\s+)?([A-Z][a-zA-Z\s]+)',
                r'\b(?:mba|msc|ma|bs|ba|phd)\s+in\s+([A-Z][a-zA-Z\s]+)',
                r'\b([A-Z][a-zA-Z\s]+)\s+(?:studies|engineering|science|arts)\b',
            ],
            'degree': [
                r'\b(?:bachelor|master|phd|doctoral|doctorate|mba|msc|ma|bs|ba|bsc)\b',
                r'\b(?:undergraduate|graduate|postgraduate)\s+(?:degree|program)\b',
                r'\b(?:certificate|diploma|associate)\s+(?:degree|program)?\b',
            ],
            'subject': [
                r'\b(?:computer\s+science|engineering|medicine|law|business|economics|psychology|biology|chemistry|physics|mathematics|literature|history|philosophy|sociology|anthropology|political\s+science)\b',
                r'\b(?:artificial\s+intelligence|machine\s+learning|data\s+science|cybersecurity|biotechnology|renewable\s+energy)\b',
                r'\b(?:international\s+relations|public\s+policy|environmental\s+science|neuroscience|genetics)\b',
            ],
            'event': [
                r'\b([A-Z][a-zA-Z\s]+)\s+(?:conference|workshop|seminar|symposium|congress)\b',
                r'\b(?:conference|workshop|seminar|symposium)\s+on\s+([A-Z][a-zA-Z\s]+)',
                r'\b([A-Z][a-zA-Z\s]+)\s+(?:competition|contest|hackathon|fair)\b',
                r'\b(?:academic|research|student)\s+(?:conference|workshop|seminar)\b',
            ]
        }
        
        # Academic intent keywords
        self.intent_keywords = {
            'university_search': [
                'best universities', 'top universities', 'university rankings', 
                'universities in', 'study abroad', 'college admissions',
                'university admission', 'how to apply', 'university programs'
            ],
            'scholarship_search': [
                'scholarship opportunities', 'financial aid', 'scholarships for',
                'free scholarships', 'merit scholarships', 'need-based aid',
                'study grants', 'fellowship programs', 'tuition assistance'
            ],
            'program_search': [
                'degree programs', 'academic programs', 'courses offered',
                'majors available', 'graduate programs', 'undergraduate programs',
                'online programs', 'distance learning', 'program requirements'
            ],
            'research_search': [
                'research opportunities', 'research programs', 'phd programs',
                'research funding', 'academic research', 'research grants',
                'research positions', 'postdoc opportunities'
            ],
            'career_search': [
                'career opportunities', 'job prospects', 'employment rates',
                'career services', 'internship programs', 'industry connections',
                'career guidance', 'professional development'
            ]
        }
        
        # Country and region mappings
        self.location_mappings = {
            'usa': ['united states', 'america', 'us', 'usa'],
            'uk': ['united kingdom', 'britain', 'england', 'scotland', 'wales', 'uk'],
            'canada': ['canada', 'canadian'],
            'australia': ['australia', 'australian'],
            'germany': ['germany', 'german', 'deutschland'],
            'france': ['france', 'french'],
            'netherlands': ['netherlands', 'dutch', 'holland'],
            'sweden': ['sweden', 'swedish'],
            'norway': ['norway', 'norwegian'],
            'denmark': ['denmark', 'danish'],
            'switzerland': ['switzerland', 'swiss'],
            'singapore': ['singapore'],
            'japan': ['japan', 'japanese'],
            'south_korea': ['south korea', 'korean', 'korea'],
            'china': ['china', 'chinese'],
            'india': ['india', 'indian']
        }
    
    def process_search_results(self, query: str, search_results: List[Dict]) -> SearchNERResult:
        """Process query and search results to extract educational entities"""
        if not self.nlp:
            return self._fallback_processing(query, search_results)
        
        # Extract entities from query
        query_entities = self.extract_entities_from_text(query, source='query')
        
        # Extract entities from search results
        search_entities = []
        for result in search_results:
            url = result.get('url', '')
            title = result.get('title', '')
            abstract = result.get('abstract', '')
            
            # Combine title and abstract for entity extraction
            combined_text = f"{title}. {abstract}"
            entities = self.extract_entities_from_text(combined_text, source='search_result', url=url)
            search_entities.append((url, entities))
        
        # Calculate relevance scores
        relevance_scores = self._calculate_relevance_scores(query_entities, search_entities)
        
        # Analyze intent
        intent_analysis = self._analyze_search_intent(query, query_entities)
        
        # Find entity matches between query and results
        entity_matches = self._find_entity_matches(query_entities, search_entities)
        
        return SearchNERResult(
            query_entities=query_entities,
            search_entities=search_entities,
            relevance_scores=relevance_scores,
            intent_analysis=intent_analysis,
            entity_matches=entity_matches
        )
    
    def extract_entities_from_text(self, text: str, source: str = '', url: str = '') -> EducationalEntities:
        """Extract educational entities from text using spaCy and custom patterns"""
        entities = EducationalEntities()
        
        if not text or not self.nlp:
            return entities
        
        # Process with spaCy
        doc = self.nlp(text)
        
        # Extract standard entities
        for ent in doc.ents:
            extracted_entity = ExtractedEntity(
                text=ent.text,
                label=ent.label_,
                confidence=0.8,  # spaCy confidence
                start_pos=ent.start_char,
                end_pos=ent.end_char,
                context=text[max(0, ent.start_char-50):ent.end_char+50],
                source=source
            )
            
            # Categorize entities
            if ent.label_ == 'ORG':
                if self._is_university_entity(ent.text):
                    entities.universities.append(extracted_entity)
                else:
                    entities.organizations.append(extracted_entity)
            elif ent.label_ == 'GPE':
                entities.locations.append(extracted_entity)
            elif ent.label_ == 'PERSON':
                entities.people.append(extracted_entity)
            elif ent.label_ == 'MONEY':
                entities.amounts.append(extracted_entity)
            elif ent.label_ == 'DATE':
                entities.deadlines.append(extracted_entity)
        
        # Extract custom educational entities
        entities = self._extract_custom_entities(text, entities, source)
        
        # Extract temporal entities (deadlines)
        entities.deadlines.extend(self._extract_deadlines(text, source))
        
        # Extract financial entities
        entities.amounts.extend(self._extract_financial_entities(text, source))
        
        return entities
    
    def _extract_custom_entities(self, text: str, entities: EducationalEntities, source: str) -> EducationalEntities:
        """Extract custom educational entities using regex patterns"""
        text_lower = text.lower()
        
        for entity_type, patterns in self.education_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    extracted_entity = ExtractedEntity(
                        text=match.group(0),
                        label=entity_type,
                        confidence=0.7,  # Pattern-based confidence
                        start_pos=match.start(),
                        end_pos=match.end(),
                        context=text[max(0, match.start()-50):match.end()+50],
                        source=source
                    )
                    
                    # Add to appropriate category
                    if entity_type == 'university':
                        entities.universities.append(extracted_entity)
                    elif entity_type == 'scholarship':
                        entities.scholarships.append(extracted_entity)
                    elif entity_type == 'program':
                        entities.programs.append(extracted_entity)
                    elif entity_type == 'degree':
                        entities.degrees.append(extracted_entity)
                    elif entity_type == 'subject':
                        entities.subjects.append(extracted_entity)
                    elif entity_type == 'event':
                        entities.events.append(extracted_entity)
        
        return entities
    
    def _extract_deadlines(self, text: str, source: str) -> List[ExtractedEntity]:
        """Extract deadline and date entities"""
        deadlines = []
        
        # Pattern for deadline mentions
        deadline_patterns = [
            r'deadline:?\s*([A-Za-z]+ \d{1,2},? \d{4})',
            r'due by:?\s*([A-Za-z]+ \d{1,2},? \d{4})',
            r'apply by:?\s*([A-Za-z]+ \d{1,2},? \d{4})',
            r'application deadline:?\s*([A-Za-z]+ \d{1,2},? \d{4})',
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{4}-\d{1,2}-\d{1,2})',
            r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}'
        ]
        
        for pattern in deadline_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                deadlines.append(ExtractedEntity(
                    text=match.group(1) if match.groups() else match.group(0),
                    label='deadline',
                    confidence=0.8,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    context=text[max(0, match.start()-50):match.end()+50],
                    source=source
                ))
        
        return deadlines
    
    def _extract_financial_entities(self, text: str, source: str) -> List[ExtractedEntity]:
        """Extract financial amounts and currency entities"""
        amounts = []
        
        # Pattern for financial amounts
        financial_patterns = [
            r'\$[\d,]+(?:\.\d{2})?',
            r'€[\d,]+(?:\.\d{2})?',
            r'£[\d,]+(?:\.\d{2})?',
            r'[\d,]+\s*(?:usd|eur|gbp|dollars?|euros?|pounds?)',
            r'(?:tuition|fee|cost|scholarship|grant|funding):\s*\$?[\d,]+',
            r'up to \$?[\d,]+',
            r'maximum \$?[\d,]+',
            r'worth \$?[\d,]+'
        ]
        
        for pattern in financial_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                amounts.append(ExtractedEntity(
                    text=match.group(0),
                    label='amount',
                    confidence=0.9,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    context=text[max(0, match.start()-50):match.end()+50],
                    source=source
                ))
        
        return amounts
    
    def _is_university_entity(self, text: str) -> bool:
        """Check if an organization entity is likely a university"""
        university_indicators = [
            'university', 'college', 'institute', 'school',
            'université', 'universidad', 'università', 'universität',
            'polytechnic', 'academy', 'conservatory'
        ]
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in university_indicators)
    
    def _calculate_relevance_scores(self, query_entities: EducationalEntities, 
                                  search_entities: List[Tuple[str, EducationalEntities]]) -> Dict[str, float]:
        """Calculate relevance scores for search results based on entity matches"""
        relevance_scores = {}
        
        # Get all query entity texts for comparison
        query_texts = set()
        for entity_list in [query_entities.universities, query_entities.scholarships, 
                           query_entities.programs, query_entities.locations, 
                           query_entities.subjects, query_entities.degrees]:
            query_texts.update(entity.text.lower() for entity in entity_list)
        
        for url, entities in search_entities:
            score = 0.0
            total_entities = 0
            
            # Check matches across all entity types
            for entity_list in [entities.universities, entities.scholarships, 
                               entities.programs, entities.locations, 
                               entities.subjects, entities.degrees]:
                for entity in entity_list:
                    total_entities += 1
                    entity_text = entity.text.lower()
                    
                    # Exact match
                    if entity_text in query_texts:
                        score += 1.0
                    # Partial match
                    elif any(query_text in entity_text or entity_text in query_text 
                            for query_text in query_texts):
                        score += 0.5
            
            # Normalize score
            if total_entities > 0:
                relevance_scores[url] = score / total_entities
            else:
                relevance_scores[url] = 0.0
        
        return relevance_scores
    
    def _analyze_search_intent(self, query: str, entities: EducationalEntities) -> Dict[str, any]:
        """Analyze the search intent based on query and extracted entities"""
        intent_scores = defaultdict(float)
        query_lower = query.lower()
        
        # Score based on keyword presence
        for intent, keywords in self.intent_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    intent_scores[intent] += 1.0
        
        # Score based on entity types
        if entities.universities:
            intent_scores['university_search'] += len(entities.universities) * 0.5
        if entities.scholarships:
            intent_scores['scholarship_search'] += len(entities.scholarships) * 0.8
        if entities.programs or entities.degrees:
            intent_scores['program_search'] += (len(entities.programs) + len(entities.degrees)) * 0.6
        if entities.amounts:
            intent_scores['scholarship_search'] += len(entities.amounts) * 0.3
        if entities.deadlines:
            intent_scores['scholarship_search'] += len(entities.deadlines) * 0.4
        
        # Determine primary intent
        primary_intent = max(intent_scores.keys(), key=intent_scores.get) if intent_scores else 'general'
        
        return {
            'primary_intent': primary_intent,
            'intent_scores': dict(intent_scores),
            'confidence': intent_scores[primary_intent] if intent_scores else 0.0,
            'entity_distribution': {
                'universities': len(entities.universities),
                'scholarships': len(entities.scholarships),
                'programs': len(entities.programs),
                'locations': len(entities.locations),
                'subjects': len(entities.subjects),
                'degrees': len(entities.degrees),
                'deadlines': len(entities.deadlines),
                'amounts': len(entities.amounts)
            }
        }
    
    def _find_entity_matches(self, query_entities: EducationalEntities, 
                           search_entities: List[Tuple[str, EducationalEntities]]) -> Dict[str, List[str]]:
        """Find matches between query entities and search result entities"""
        matches = defaultdict(list)
        
        # Get all query entities with their types
        query_entity_map = {}
        for attr_name in ['universities', 'scholarships', 'programs', 'locations', 'subjects', 'degrees']:
            entity_list = getattr(query_entities, attr_name)
            for entity in entity_list:
                query_entity_map[entity.text.lower()] = attr_name
        
        # Find matches in search results
        for url, entities in search_entities:
            for attr_name in ['universities', 'scholarships', 'programs', 'locations', 'subjects', 'degrees']:
                entity_list = getattr(entities, attr_name)
                for entity in entity_list:
                    entity_text = entity.text.lower()
                    for query_text, query_type in query_entity_map.items():
                        if query_text in entity_text or entity_text in query_text:
                            matches[f"{query_type}:{query_text}"].append(f"{url}:{entity_text}")
        
        return dict(matches)
    
    def _fallback_processing(self, query: str, search_results: List[Dict]) -> SearchNERResult:
        """Fallback processing when spaCy is not available"""
        logging.warning("Using fallback NER processing - install spaCy for better results")
        
        # Simple keyword-based entity extraction
        query_entities = EducationalEntities()
        search_entities = []
        
        # Basic university detection
        university_keywords = ['university', 'college', 'institute']
        for keyword in university_keywords:
            if keyword in query.lower():
                query_entities.universities.append(ExtractedEntity(
                    text=keyword,
                    label='university',
                    confidence=0.5,
                    source='query'
                ))
        
        # Process search results similarly
        for result in search_results:
            url = result.get('url', '')
            text = f"{result.get('title', '')} {result.get('abstract', '')}"
            entities = EducationalEntities()
            
            for keyword in university_keywords:
                if keyword in text.lower():
                    entities.universities.append(ExtractedEntity(
                        text=keyword,
                        label='university',
                        confidence=0.5,
                        source='search_result'
                    ))
            
            search_entities.append((url, entities))
        
        return SearchNERResult(
            query_entities=query_entities,
            search_entities=search_entities,
            relevance_scores={url: 0.5 for url, _ in search_entities},
            intent_analysis={'primary_intent': 'general', 'confidence': 0.5},
            entity_matches={}
        ) 