"""
Educational Data Validation Framework for UniScholar platform.
Implements comprehensive validation rules for educational entities.
Part of Phase 1 requirements from STUDENT_DATASET_PLAN.md
"""

import re
import logging
import requests
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from urllib.parse import urlparse
from dataclasses import dataclass

from ..core.models import University, Scholarship, AcademicProgram, StudentEvent, Funding
from ..core.config import get_config
from ..core.exceptions import ValidationError


@dataclass
class ValidationResult:
    """Result of validation operation"""
    is_valid: bool
    issues: List[str]
    severity: str  # 'error', 'warning', 'info'
    confidence_score: float


@dataclass
class EducationalValidationReport:
    """Comprehensive validation report for educational entities"""
    total_validated: int
    valid_count: int
    invalid_count: int
    validation_results: Dict[str, List[ValidationResult]]
    quality_score: float
    validation_time: float


class EducationalValidator:
    """Validator for educational entities with domain-specific rules"""
    
    def __init__(self):
        self.config = get_config()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Validation rules from STUDENT_DATASET_PLAN.md
        self.validation_rules = {
            'universities': {
                'required_fields': ['name', 'country', 'official_url'],
                'min_name_length': 5,
                'max_name_length': 100
            },
            'scholarships': {
                'required_fields': ['name', 'provider', 'amount', 'application_deadline'],
                'min_name_length': 3,
                'max_name_length': 200
            }
        }
        
        # Spam detection patterns
        self.spam_patterns = [
            r'\b(click here|free money|guaranteed|act now|limited time)\b',
            r'\b(lottery|winner|prize|congratulations)\b'
        ]
        
        # Valid countries for education
        self.valid_countries = {
            'USA', 'United States', 'UK', 'United Kingdom', 'Germany', 'France',
            'Canada', 'Australia', 'China', 'Japan', 'India', 'Brazil', 'Italy',
            'Spain', 'Netherlands', 'Sweden', 'Norway', 'Denmark', 'Finland'
        }
        
        # Valid degree types
        self.valid_degree_types = {
            'bachelor', 'master', 'phd', 'doctorate', 'certificate', 'diploma',
            'associate', 'professional', 'postgraduate'
        }
        
        # Valid event types
        self.valid_event_types = {
            'conference', 'workshop', 'seminar', 'competition', 'fair',
            'webinar', 'networking', 'symposium', 'exhibition'
        }

    def validate_educational_entities(self, entities: Dict[str, List]) -> EducationalValidationReport:
        """Validate all educational entities and return comprehensive report"""
        start_time = datetime.now()
        
        validation_results = {}
        total_validated = 0
        valid_count = 0
        
        # Validate each entity type
        for entity_type, entity_list in entities.items():
            if entity_type == 'universities':
                results = [self.validate_university(uni) for uni in entity_list]
            elif entity_type == 'scholarships':
                results = [self.validate_scholarship(sch) for sch in entity_list]
            elif entity_type == 'programs':
                results = [self.validate_program(prog) for prog in entity_list]
            elif entity_type == 'events':
                results = [self.validate_event(event) for event in entity_list]
            elif entity_type == 'funding':
                results = [self.validate_funding(fund) for fund in entity_list]
            else:
                continue
            
            validation_results[entity_type] = results
            total_validated += len(results)
            valid_count += sum(1 for r in results if r.is_valid)
        
        # Calculate quality metrics
        quality_score = valid_count / total_validated if total_validated > 0 else 0.0
        validation_time = (datetime.now() - start_time).total_seconds()
        
        self.logger.info(
            f"Educational validation completed: {valid_count}/{total_validated} valid "
            f"(quality: {quality_score:.2%}) in {validation_time:.2f}s"
        )
        
        return EducationalValidationReport(
            total_validated=total_validated,
            valid_count=valid_count,
            invalid_count=total_validated - valid_count,
            validation_results=validation_results,
            quality_score=quality_score,
            validation_time=validation_time
        )

    def validate_university(self, university: University) -> ValidationResult:
        """Validate university entity with educational domain rules"""
        issues = []
        confidence_score = 1.0
        
        # Required fields validation
        for field in self.validation_rules['universities']['required_fields']:
            if not getattr(university, field, None):
                issues.append(f"Missing required field: {field}")
                confidence_score -= 0.2
        
        # Name validation
        if university.name:
            if len(university.name) < self.validation_rules['universities']['min_name_length']:
                issues.append("University name too short")
                confidence_score -= 0.1
            
            if len(university.name) > self.validation_rules['universities']['max_name_length']:
                issues.append("University name too long")
                confidence_score -= 0.1
            
            # Check for spam patterns
            for pattern in self.spam_patterns:
                if re.search(pattern, university.name, re.IGNORECASE):
                    issues.append("University name contains spam indicators")
                    confidence_score -= 0.3
                    break
        
        # URL validation
        if university.official_url:
            if not self._is_valid_url(university.official_url):
                issues.append("Invalid URL format")
                confidence_score -= 0.2
        
        # Geographic validation
        if university.country:
            geo_issues = self._validate_geography(university.country, university.city)
            issues.extend(geo_issues)
            confidence_score -= len(geo_issues) * 0.1
        
        # Educational specific validation
        if university.type:
            type_issues = self._validate_university_type(university.type)
            issues.extend(type_issues)
            confidence_score -= len(type_issues) * 0.1
        
        is_valid = len(issues) == 0
        severity = 'error' if not is_valid else 'info'
        
        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            severity=severity,
            confidence_score=max(0.0, confidence_score)
        )

    def validate_scholarship(self, scholarship: Scholarship) -> ValidationResult:
        """Validate scholarship entity"""
        issues = []
        confidence_score = 1.0
        
        # Required fields validation
        for field in self.validation_rules['scholarships']['required_fields']:
            if not getattr(scholarship, field, None):
                issues.append(f"Missing required field: {field}")
                confidence_score -= 0.25
        
        # Name validation
        if scholarship.name:
            if len(scholarship.name) < self.validation_rules['scholarships']['min_name_length']:
                issues.append("Scholarship name too short")
                confidence_score -= 0.1
        
        # Provider validation
        if scholarship.provider:
            if len(scholarship.provider) < 3:
                issues.append("Scholarship provider name too short")
                confidence_score -= 0.1
        
        # Amount validation
        if scholarship.amount:
            amount_issues = self._validate_financial_amount(scholarship.amount)
            issues.extend(amount_issues)
            confidence_score -= len(amount_issues) * 0.15
        
        # Deadline validation
        if scholarship.application_deadline:
            deadline_issues = self._validate_deadline(scholarship.application_deadline)
            issues.extend(deadline_issues)
            confidence_score -= len(deadline_issues) * 0.1
        
        # Academic level validation
        if scholarship.academic_level:
            level_issues = self._validate_academic_levels(scholarship.academic_level)
            issues.extend(level_issues)
            confidence_score -= len(level_issues) * 0.05
        
        is_valid = len(issues) == 0
        severity = 'error' if not is_valid else 'info'
        
        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            severity=severity,
            confidence_score=max(0.0, confidence_score)
        )

    def validate_program(self, program: AcademicProgram) -> ValidationResult:
        """Validate academic program entity"""
        issues = []
        confidence_score = 1.0
        
        # Required fields validation
        for field in self.validation_rules['programs']['required_fields']:
            if not getattr(program, field, None):
                issues.append(f"Missing required field: {field}")
                confidence_score -= 0.25
        
        # Degree type validation
        if program.degree_type:
            degree_issues = self._validate_degree_type(program.degree_type)
            issues.extend(degree_issues)
            confidence_score -= len(degree_issues) * 0.15
        
        # Duration validation
        if program.duration:
            duration_issues = self._validate_program_duration(program.duration, program.degree_type)
            issues.extend(duration_issues)
            confidence_score -= len(duration_issues) * 0.1
        
        is_valid = len(issues) == 0
        severity = 'error' if not is_valid else 'info'
        
        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            severity=severity,
            confidence_score=max(0.0, confidence_score)
        )

    def validate_event(self, event: StudentEvent) -> ValidationResult:
        """Validate student event entity"""
        issues = []
        confidence_score = 1.0
        
        # Required fields validation
        for field in self.validation_rules['events']['required_fields']:
            if not getattr(event, field, None):
                issues.append(f"Missing required field: {field}")
                confidence_score -= 0.25
        
        # Event type validation
        if event.event_type:
            type_issues = self._validate_event_type(event.event_type)
            issues.extend(type_issues)
            confidence_score -= len(type_issues) * 0.15
        
        # Date validation
        if event.date:
            date_issues = self._validate_event_date(event.date)
            issues.extend(date_issues)
            confidence_score -= len(date_issues) * 0.2
        
        is_valid = len(issues) == 0
        severity = 'error' if not is_valid else 'info'
        
        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            severity=severity,
            confidence_score=max(0.0, confidence_score)
        )

    def validate_funding(self, funding: Funding) -> ValidationResult:
        """Validate funding/grant entity"""
        issues = []
        confidence_score = 1.0
        
        # Required fields validation
        for field in self.validation_rules['funding']['required_fields']:
            if not getattr(funding, field, None):
                issues.append(f"Missing required field: {field}")
                confidence_score -= 0.25
        
        # Amount validation
        if funding.amount_range:
            amount_issues = self._validate_financial_amount(funding.amount_range)
            issues.extend(amount_issues)
            confidence_score -= len(amount_issues) * 0.15
        
        # Funding type validation
        if funding.funding_type:
            type_issues = self._validate_funding_type(funding.funding_type)
            issues.extend(type_issues)
            confidence_score -= len(type_issues) * 0.1
        
        is_valid = len(issues) == 0
        severity = 'error' if not is_valid else 'info'
        
        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            severity=severity,
            confidence_score=max(0.0, confidence_score)
        )

    # Helper validation methods
    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format"""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        return url_pattern.match(url) is not None

    def _validate_geography(self, country: str, city: str) -> List[str]:
        """Validate geographic information"""
        issues = []
        
        if country and country not in self.valid_countries:
            # Only check against common countries - could be enhanced with full country list
            pass
        
        return issues

    def _validate_university_type(self, uni_type: str) -> List[str]:
        """Validate university type"""
        valid_types = {'public', 'private', 'technical', 'community', 'university', 'college'}
        
        if uni_type.lower() not in valid_types:
            return [f"Invalid university type: {uni_type}"]
        
        return []

    def _validate_financial_amount(self, amount: Dict[str, str]) -> List[str]:
        """Validate financial amount"""
        issues = []
        
        if not amount:
            return issues
        
        # Validate currency
        valid_currencies = {'$', '€', '£', 'USD', 'EUR', 'GBP'}
        if 'currency' in amount and amount['currency'] not in valid_currencies:
            issues.append(f"Invalid currency: {amount['currency']}")
        
        # Validate amount format
        if 'amount' in amount:
            amount_str = amount['amount'].replace(',', '')
            if not amount_str.isdigit():
                issues.append("Invalid amount format")
            elif int(amount_str) > 1000000:  # Reasonable upper limit
                issues.append("Amount seems unreasonably high")
        
        return issues

    def _validate_deadline(self, deadline: str) -> List[str]:
        """Validate deadline date"""
        issues = []
        
        # Try to parse common date formats
        date_formats = ['%B %d, %Y', '%m/%d/%Y', '%Y-%m-%d', '%d/%m/%Y']
        
        parsed_date = None
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(deadline, fmt)
                break
            except ValueError:
                continue
        
        if not parsed_date:
            issues.append("Invalid deadline date format")
        elif parsed_date < datetime.now():
            issues.append("Deadline is in the past")
        
        return issues

    def _validate_academic_levels(self, levels: List[str]) -> List[str]:
        """Validate academic levels"""
        valid_levels = {'undergraduate', 'graduate', 'phd', 'postdoc', 'certificate', 'all'}
        
        issues = []
        for level in levels:
            if level.lower() not in valid_levels:
                issues.append(f"Invalid academic level: {level}")
        
        return issues

    def _validate_degree_type(self, degree_type: str) -> List[str]:
        """Validate degree type"""
        if degree_type.lower() not in self.valid_degree_types:
            return [f"Invalid degree type: {degree_type}"]
        
        return []

    def _validate_program_duration(self, duration: str, degree_type: str) -> List[str]:
        """Validate program duration based on degree type"""
        issues = []
        
        # Extract number from duration string
        duration_match = re.search(r'(\d+)', duration)
        if not duration_match:
            issues.append("Cannot parse program duration")
            return issues
        
        duration_num = int(duration_match.group(1))
        
        # Reasonable duration ranges by degree type
        duration_ranges = {
            'bachelor': (3, 5),
            'master': (1, 3),
            'phd': (3, 8),
            'certificate': (1, 2)
        }
        
        if degree_type.lower() in duration_ranges:
            min_dur, max_dur = duration_ranges[degree_type.lower()]
            if not (min_dur <= duration_num <= max_dur):
                issues.append(f"Unusual duration for {degree_type}: {duration}")
        
        return issues

    def _validate_event_type(self, event_type: str) -> List[str]:
        """Validate event type"""
        if event_type.lower() not in self.valid_event_types:
            return [f"Invalid event type: {event_type}"]
        
        return []

    def _validate_event_date(self, event_date: str) -> List[str]:
        """Validate event date"""
        # Similar to deadline validation but more permissive for past events
        issues = []
        
        date_formats = ['%B %d, %Y', '%m/%d/%Y', '%Y-%m-%d', '%d/%m/%Y']
        
        parsed_date = None
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(event_date, fmt)
                break
            except ValueError:
                continue
        
        if not parsed_date:
            issues.append("Invalid event date format")
        
        return issues

    def _validate_funding_type(self, funding_type: str) -> List[str]:
        """Validate funding type"""
        valid_types = {'research_grant', 'travel_grant', 'project_funding', 'scholarship', 'fellowship'}
        
        if funding_type.lower() not in valid_types:
            return [f"Invalid funding type: {funding_type}"]
        
        return [] 