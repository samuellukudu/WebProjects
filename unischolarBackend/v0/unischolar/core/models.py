"""
Data models for UniScholar platform.

Comprehensive data structures for universities, scholarships, academic programs,
student events, funding opportunities, and general content extraction.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Any
from datetime import datetime
from enum import Enum


class OrganizationType(Enum):
    """Types of organizations that can be extracted"""
    UNIVERSITY = "university"
    COMPANY = "company" 
    INSTITUTE = "institute"
    RESEARCH_CENTER = "research_center"
    GOVERNMENT = "government"
    NONPROFIT = "nonprofit"
    UNKNOWN = "unknown"


class AcademicLevel(Enum):
    """Academic levels for programs and scholarships"""
    UNDERGRADUATE = "undergraduate"
    GRADUATE = "graduate"
    PHD = "phd"
    POSTDOC = "postdoc"
    CERTIFICATE = "certificate"
    ALL = "all"


class DegreeType(Enum):
    """Types of academic degrees"""
    BACHELOR = "bachelor"
    MASTER = "master"
    PHD = "phd"
    CERTIFICATE = "certificate"
    DIPLOMA = "diploma"


class FundingType(Enum):
    """Types of funding opportunities"""
    RESEARCH_GRANT = "research_grant"
    TRAVEL_GRANT = "travel_grant"
    PROJECT_FUNDING = "project_funding"
    SCHOLARSHIP = "scholarship"
    FELLOWSHIP = "fellowship"


class EventType(Enum):
    """Types of student events"""
    CONFERENCE = "conference"
    COMPETITION = "competition"
    FAIR = "fair"
    WORKSHOP = "workshop"
    WEBINAR = "webinar"
    NETWORKING = "networking"


@dataclass
class University:
    """University/Academic Institution entity"""
    name: str
    official_url: str
    country: str
    city: str
    type: str  # public, private, technical, community
    world_ranking: Optional[int] = None
    national_ranking: Optional[int] = None
    established_year: Optional[int] = None
    student_population: Optional[int] = None
    international_student_percentage: Optional[float] = None
    tuition_fees: Dict[str, str] = field(default_factory=dict)  # {currency: amount, level: undergrad/grad}
    languages_of_instruction: List[str] = field(default_factory=list)
    admission_requirements: Dict[str, Any] = field(default_factory=dict)
    notable_programs: List[str] = field(default_factory=list)
    research_areas: List[str] = field(default_factory=list)
    campus_facilities: List[str] = field(default_factory=list)
    application_deadlines: Dict[str, str] = field(default_factory=dict)
    contact_info: Dict[str, str] = field(default_factory=dict)
    social_media: Dict[str, str] = field(default_factory=dict)
    accreditations: List[str] = field(default_factory=list)
    description: str = ""
    extraction_source: str = ""
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class Scholarship:
    """Scholarship/Financial Aid entity"""
    name: str
    provider: str  # university, government, foundation, company
    official_url: str
    amount: Dict[str, str] = field(default_factory=dict)  # {currency: amount, type: full/partial}
    eligibility_criteria: Dict[str, Any] = field(default_factory=dict)
    target_countries: List[str] = field(default_factory=list)
    target_regions: List[str] = field(default_factory=list)
    academic_level: List[str] = field(default_factory=list)  # undergraduate, graduate, phd, postdoc
    fields_of_study: List[str] = field(default_factory=list)
    application_deadline: str = ""
    application_process: str = ""
    required_documents: List[str] = field(default_factory=list)
    selection_criteria: List[str] = field(default_factory=list)
    renewable: bool = False
    number_of_awards: Optional[int] = None
    duration: str = ""
    benefits_included: List[str] = field(default_factory=list)  # tuition, living allowance, books, etc.
    restrictions: List[str] = field(default_factory=list)
    contact_info: Dict[str, str] = field(default_factory=dict)
    success_rate: Optional[float] = None
    description: str = ""
    tags: List[str] = field(default_factory=list)  # merit-based, need-based, diversity, etc.
    extraction_source: str = ""
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class AcademicProgram:
    """Academic Program/Major entity"""
    program_name: str
    university: str
    university_url: str
    program_url: str
    degree_type: str  # bachelor, master, phd, certificate
    field_of_study: str
    specializations: List[str] = field(default_factory=list)
    duration: str = ""
    credit_hours: Optional[int] = None
    language_of_instruction: str = ""
    admission_requirements: Dict[str, Any] = field(default_factory=dict)
    curriculum_highlights: List[str] = field(default_factory=list)
    career_prospects: List[str] = field(default_factory=list)
    internship_opportunities: bool = False
    research_opportunities: bool = False
    faculty_ratio: Optional[str] = None
    tuition_cost: Dict[str, str] = field(default_factory=dict)
    application_deadlines: Dict[str, str] = field(default_factory=dict)
    prerequisites: List[str] = field(default_factory=list)
    accreditation: List[str] = field(default_factory=list)
    online_availability: bool = False
    exchange_programs: List[str] = field(default_factory=list)
    industry_partnerships: List[str] = field(default_factory=list)
    graduate_employment_rate: Optional[float] = None
    average_starting_salary: Optional[Dict[str, str]] = None
    description: str = ""
    extraction_source: str = ""
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class StudentEvent:
    """Student Event/Opportunity entity"""
    event_name: str
    event_type: str  # conference, competition, fair, workshop, webinar
    organizer: str
    official_url: str
    date: str = ""
    location: Dict[str, str] = field(default_factory=dict)  # virtual/physical
    target_audience: List[str] = field(default_factory=list)  # undergrad, grad, all students
    fields_of_interest: List[str] = field(default_factory=list)
    registration_deadline: str = ""
    registration_fee: Dict[str, str] = field(default_factory=dict)
    benefits: List[str] = field(default_factory=list)  # networking, certificates, prizes
    speakers: List[str] = field(default_factory=list)
    agenda_highlights: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)
    capacity: Optional[int] = None
    scholarships_available: bool = False
    travel_support: bool = False
    contact_info: Dict[str, str] = field(default_factory=dict)
    social_media: Dict[str, str] = field(default_factory=dict)
    description: str = ""
    tags: List[str] = field(default_factory=list)
    extraction_source: str = ""
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class Funding:
    """Funding/Grant entity"""
    program_name: str
    funding_body: str
    official_url: str
    funding_type: str  # research_grant, travel_grant, project_funding
    amount_range: Dict[str, str] = field(default_factory=dict)
    target_recipients: List[str] = field(default_factory=list)  # students, researchers, institutions
    academic_levels: List[str] = field(default_factory=list)
    research_areas: List[str] = field(default_factory=list)
    geographic_eligibility: List[str] = field(default_factory=list)
    application_deadline: str = ""
    funding_duration: str = ""
    application_process: str = ""
    evaluation_criteria: List[str] = field(default_factory=list)
    success_rate: Optional[float] = None
    past_recipients: List[str] = field(default_factory=list)
    renewable: bool = False
    reporting_requirements: List[str] = field(default_factory=list)
    restrictions: List[str] = field(default_factory=list)
    contact_info: Dict[str, str] = field(default_factory=dict)
    description: str = ""
    tags: List[str] = field(default_factory=list)
    extraction_source: str = ""
    last_updated: datetime = field(default_factory=datetime.now)


# Legacy models for backward compatibility
@dataclass
class Organization:
    """General organization entity (legacy)"""
    name: str
    url: str
    org_type: str  # 'university', 'company', 'institute', 'research_center'
    source_url: str
    confidence_score: float
    extraction_method: str
    country: Optional[str] = None
    description: Optional[str] = None


@dataclass
class GeneralContent:
    """General content entity (legacy)"""
    title: str
    url: str
    content_type: str  # 'blog_post', 'navigation', 'directory', 'news'
    source_url: str
    description: Optional[str] = None


@dataclass
class QueryIntent:
    """Represents analyzed user query intent"""
    entity_types: Set[str]
    geographic_focus: Set[str] 
    domain_focus: Set[str]
    organization_types: Set[str]
    search_intent: str
    confidence_factors: Dict[str, float]
    patterns: Dict[str, List[str]]


# Utility functions for model operations
def to_dict(obj) -> Dict:
    """Convert dataclass to dictionary"""
    if hasattr(obj, '__dataclass_fields__'):
        result = {}
        for field_name, field_def in obj.__dataclass_fields__.items():
            value = getattr(obj, field_name)
            if isinstance(value, datetime):
                result[field_name] = value.isoformat()
            elif hasattr(value, '__dataclass_fields__'):
                result[field_name] = to_dict(value)
            else:
                result[field_name] = value
        return result
    return obj


def from_dict(data: Dict, model_class) -> Any:
    """Create dataclass instance from dictionary"""
    # Handle datetime fields
    if 'last_updated' in data and isinstance(data['last_updated'], str):
        data['last_updated'] = datetime.fromisoformat(data['last_updated'])
    
    return model_class(**data) 