"""
Educational Data Extraction Pipeline for UniScholar platform.
Integrates all Phase 1 components for comprehensive educational data extraction.
Implements STUDENT_DATASET_PLAN.md Phase 1 requirements.
"""

import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from .educational_extractor import EducationalExtractor, EducationalExtractionResult
from .dynamic_ner import DynamicNERExtractor
from ..utils.educational_validator import EducationalValidator
from ..core.models import QueryIntent, University, Scholarship, AcademicProgram, StudentEvent, Funding
from ..core.config import get_config
from ..core.exceptions import ExtractionError


@dataclass
class EducationalPipelineResult:
    """Complete result of educational pipeline processing"""
    # Extracted entities
    universities: List[University]
    scholarships: List[Scholarship]
    programs: List[AcademicProgram]
    events: List[StudentEvent]
    funding: List[Funding]
    
    # Pipeline metrics
    total_entities_extracted: int
    total_entities_validated: int
    extraction_time: float
    validation_time: float
    query_intent: Optional[QueryIntent]
    
    # Quality metrics
    quality_score: float
    confidence_distribution: Dict[str, float]


class EducationalPipeline:
    """
    Comprehensive educational data extraction pipeline
    Integrates Phase 1 components for student-focused data collection
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = get_config()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize Phase 1 components
        self.ner_extractor = DynamicNERExtractor(config)
        self.educational_extractor = EducationalExtractor(config)
        self.validator = EducationalValidator()
        
        # Student intent analysis patterns from STUDENT_DATASET_PLAN.md
        self.student_intent_mappings = {
            'university_search': {
                'keywords': ['university', 'college', 'school', 'admission'],
                'focus': 'institutional_information',
                'boost_factors': {'ranking': 0.3, 'location': 0.2, 'programs': 0.2}
            },
            'scholarship_search': {
                'keywords': ['scholarship', 'funding', 'financial aid', 'grant'],
                'focus': 'financial_opportunities',
                'boost_factors': {'amount': 0.4, 'eligibility': 0.3, 'deadline': 0.2}
            },
            'program_search': {
                'keywords': ['major', 'program', 'degree', 'study', 'course'],
                'focus': 'academic_programs',
                'boost_factors': {'field': 0.3, 'level': 0.2, 'duration': 0.1}
            }
        }

    def process_educational_content(self, html_content: str, source_url: str, 
                                  user_query: Optional[str] = None) -> EducationalPipelineResult:
        """
        Complete educational content processing pipeline
        
        Args:
            html_content: HTML content to process
            source_url: Source URL of the content
            user_query: Optional user query for intent analysis
            
        Returns:
            EducationalPipelineResult with extracted and validated entities
        """
        start_time = time.time()
        
        try:
            # Step 1: Analyze query intent (if provided)
            query_intent = None
            if user_query:
                query_intent = self._analyze_student_intent(user_query)
                self.logger.info(f"Detected student intent: {query_intent.search_intent}")
            
            # Step 2: Extract educational entities
            extraction_start = time.time()
            extraction_result = self.educational_extractor.extract_educational_entities(
                html_content, source_url, query_intent
            )
            extraction_time = time.time() - extraction_start
            
            # Step 3: Validate extracted entities
            validation_start = time.time()
            validated_entities = self._validate_educational_entities(extraction_result)
            validation_time = time.time() - validation_start
            
            # Step 4: Calculate quality metrics
            quality_metrics = self._calculate_quality_metrics(validated_entities)
            
            # Step 5: Generate final result
            total_time = time.time() - start_time
            
            result = EducationalPipelineResult(
                universities=validated_entities['universities'],
                scholarships=validated_entities['scholarships'],
                programs=validated_entities['programs'],
                events=validated_entities['events'],
                funding=validated_entities['funding'],
                total_entities_extracted=extraction_result.total_entities,
                total_entities_validated=sum(len(entities) for entities in validated_entities.values()),
                extraction_time=extraction_time,
                validation_time=validation_time,
                query_intent=query_intent,
                quality_score=quality_metrics['overall_quality'],
                confidence_distribution=quality_metrics['confidence_distribution']
            )
            
            self.logger.info(
                f"Educational pipeline completed for {source_url}: "
                f"{result.total_entities_validated} validated entities "
                f"(quality: {result.quality_score:.2%}) in {total_time:.2f}s"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Educational pipeline failed for {source_url}: {e}")
            raise ExtractionError(f"Educational pipeline failed: {e}")

    def _analyze_student_intent(self, user_query: str) -> QueryIntent:
        """Analyze user query with student-focused intent detection"""
        # Use existing NER analyzer but enhance with student context
        query_intent = self.ner_extractor.analyze_query(user_query)
        
        # Enhance with student-specific intent analysis
        for intent_type, intent_config in self.student_intent_mappings.items():
            if any(keyword in user_query.lower() for keyword in intent_config['keywords']):
                query_intent.search_intent = intent_type
                query_intent.confidence_factors.update(intent_config['boost_factors'])
                break
        
        return query_intent

    def _validate_educational_entities(self, extraction_result: EducationalExtractionResult) -> Dict[str, List]:
        """Validate all extracted educational entities"""
        validated_entities = {
            'universities': [],
            'scholarships': [],
            'programs': [],
            'events': [],
            'funding': []
        }
        
        # Validate universities
        for university in extraction_result.universities:
            validation_result = self.validator.validate_university(university)
            if validation_result.is_valid or validation_result.confidence_score >= 0.7:
                validated_entities['universities'].append(university)
            else:
                self.logger.debug(f"Rejected university: {university.name} - {validation_result.issues}")
        
        # Validate scholarships
        for scholarship in extraction_result.scholarships:
            validation_result = self.validator.validate_scholarship(scholarship)
            if validation_result.is_valid or validation_result.confidence_score >= 0.7:
                validated_entities['scholarships'].append(scholarship)
            else:
                self.logger.debug(f"Rejected scholarship: {scholarship.name} - {validation_result.issues}")
        
        # Add other entity validations as they're implemented
        validated_entities['programs'] = extraction_result.programs
        validated_entities['events'] = extraction_result.events
        validated_entities['funding'] = extraction_result.funding
        
        return validated_entities

    def _calculate_quality_metrics(self, validated_entities: Dict[str, List]) -> Dict[str, Any]:
        """Calculate quality metrics for extracted entities"""
        total_entities = sum(len(entities) for entities in validated_entities.values())
        
        if total_entities == 0:
            return {
                'overall_quality': 0.0,
                'confidence_distribution': {}
            }
        
        # Calculate entity type distribution
        entity_distribution = {
            entity_type: len(entities) / total_entities
            for entity_type, entities in validated_entities.items()
            if entities
        }
        
        # Calculate overall quality score
        # Base quality on entity diversity and completeness
        quality_factors = {
            'diversity': min(1.0, len(entity_distribution) * 0.3),  # Reward diverse entity types
            'volume': min(1.0, total_entities / 10),  # Reward reasonable volume
            'completeness': self._assess_completeness(validated_entities)  # Reward complete data
        }
        
        overall_quality = sum(quality_factors.values()) / len(quality_factors)
        
        return {
            'overall_quality': overall_quality,
            'confidence_distribution': entity_distribution,
            'quality_factors': quality_factors
        }

    def _assess_completeness(self, validated_entities: Dict[str, List]) -> float:
        """Assess data completeness across entities"""
        completeness_scores = []
        
        # Assess university completeness
        for university in validated_entities['universities']:
            required_fields = ['name', 'official_url', 'country', 'city']
            filled_fields = sum(1 for field in required_fields if getattr(university, field, None))
            completeness_scores.append(filled_fields / len(required_fields))
        
        # Assess scholarship completeness
        for scholarship in validated_entities['scholarships']:
            required_fields = ['name', 'provider', 'official_url', 'amount']
            filled_fields = sum(1 for field in required_fields if getattr(scholarship, field, None))
            completeness_scores.append(filled_fields / len(required_fields))
        
        return sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0.0

    def process_multiple_sources(self, sources: List[Dict[str, str]], 
                                user_query: Optional[str] = None) -> List[EducationalPipelineResult]:
        """Process multiple sources in parallel for comprehensive data collection"""
        results = []
        
        for source in sources:
            html_content = source.get('html_content', '')
            source_url = source.get('url', '')
            
            if html_content and source_url:
                try:
                    result = self.process_educational_content(html_content, source_url, user_query)
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Failed to process source {source_url}: {e}")
        
        return results

    def aggregate_results(self, results: List[EducationalPipelineResult]) -> EducationalPipelineResult:
        """Aggregate multiple pipeline results into a single comprehensive result"""
        if not results:
            return EducationalPipelineResult(
                universities=[], scholarships=[], programs=[], events=[], funding=[],
                total_entities_extracted=0, total_entities_validated=0,
                extraction_time=0.0, validation_time=0.0, query_intent=None,
                quality_score=0.0, confidence_distribution={}
            )
        
        # Combine all entities
        all_universities = []
        all_scholarships = []
        all_programs = []
        all_events = []
        all_funding = []
        
        for result in results:
            all_universities.extend(result.universities)
            all_scholarships.extend(result.scholarships)
            all_programs.extend(result.programs)
            all_events.extend(result.events)
            all_funding.extend(result.funding)
        
        # Deduplicate entities
        unique_universities = self._deduplicate_universities(all_universities)
        unique_scholarships = self._deduplicate_scholarships(all_scholarships)
        
        # Calculate aggregate metrics
        total_extracted = sum(r.total_entities_extracted for r in results)
        total_validated = len(unique_universities) + len(unique_scholarships) + len(all_programs) + len(all_events) + len(all_funding)
        avg_quality = sum(r.quality_score for r in results) / len(results)
        
        return EducationalPipelineResult(
            universities=unique_universities,
            scholarships=unique_scholarships,
            programs=all_programs,
            events=all_events,
            funding=all_funding,
            total_entities_extracted=total_extracted,
            total_entities_validated=total_validated,
            extraction_time=sum(r.extraction_time for r in results),
            validation_time=sum(r.validation_time for r in results),
            query_intent=results[0].query_intent if results else None,
            quality_score=avg_quality,
            confidence_distribution={}
        )

    def _deduplicate_universities(self, universities: List[University]) -> List[University]:
        """Remove duplicate universities based on name and URL"""
        seen = set()
        unique = []
        
        for uni in universities:
            key = (uni.name.lower().strip(), uni.official_url.lower().strip())
            if key not in seen:
                seen.add(key)
                unique.append(uni)
        
        return unique

    def _deduplicate_scholarships(self, scholarships: List[Scholarship]) -> List[Scholarship]:
        """Remove duplicate scholarships based on name and provider"""
        seen = set()
        unique = []
        
        for scholarship in scholarships:
            key = (scholarship.name.lower().strip(), scholarship.provider.lower().strip())
            if key not in seen:
                seen.add(key)
                unique.append(scholarship)
        
        return unique 