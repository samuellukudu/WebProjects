"""
Configuration management for UniScholar platform.

Handles loading and validation of configuration from files and environment variables.
"""

import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path


@dataclass
class CrawlerConfig:
    """Configuration for web crawlers"""
    max_concurrent: int = 5
    request_delay: float = 1.0
    max_retries: int = 3
    session_timeout: int = 30
    user_agents: List[str] = field(default_factory=lambda: [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0',
    ])
    robots_respect: bool = True
    max_queue_size: int = 10000


@dataclass
class ExtractionConfig:
    """Configuration for data extraction"""
    confidence_threshold: float = 0.5
    max_description_length: int = 2000
    enable_nlp: bool = True
    enable_structured_data: bool = True
    enable_text_extraction: bool = True
    similarity_threshold: float = 0.85
    deduplication_enabled: bool = True


@dataclass
class ValidationConfig:
    """Configuration for data validation"""
    validate_urls: bool = True
    validate_emails: bool = True
    validate_dates: bool = True
    homepage_validation: bool = True
    max_validation_workers: int = 5
    validation_timeout: int = 10


@dataclass
class OutputConfig:
    """Configuration for output formats and destinations"""
    output_directory: str = "output"
    csv_export: bool = True
    json_export: bool = True
    api_export: bool = False
    backup_enabled: bool = True
    compression_enabled: bool = False


@dataclass
class LoggingConfig:
    """Configuration for logging"""
    level: str = "INFO"
    format: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    file_enabled: bool = True
    file_path: str = "logs/unischolar.log"
    console_enabled: bool = True
    max_file_size: int = 10485760  # 10MB
    backup_count: int = 5


@dataclass
class Config:
    """Main configuration class for UniScholar platform"""
    crawler: CrawlerConfig = field(default_factory=CrawlerConfig)
    extraction: ExtractionConfig = field(default_factory=ExtractionConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    # Search configuration
    max_search_results: int = 30
    default_search_workers: int = 5
    
    # Entity-specific configurations
    university_patterns: Dict[str, List[str]] = field(default_factory=lambda: {
        'strong_indicators': [
            r'\b(university|université|universidad|università|universität)\b',
            r'\b(college|collège|colegio|collegio|hochschule)\b',
            r'\b(institute of technology|technical university|polytechnic)\b',
            r'\b(school of medicine|medical school|law school|business school)\b'
        ],
        'domain_patterns': [r'\.edu$', r'\.ac\.', r'\.university$'],
        'context_keywords': [
            'admissions', 'enrollment', 'campus', 'faculty', 'degrees',
            'undergraduate', 'graduate', 'alumni', 'tuition'
        ]
    })
    
    scholarship_patterns: Dict[str, List[str]] = field(default_factory=lambda: {
        'strong_indicators': [
            r'\b(scholarship|scholarships|bourse|beca)\b',
            r'\b(fellowship|fellowships|grant|grants)\b',
            r'\b(financial aid|aide financière|ayuda financiera)\b',
            r'\b(tuition waiver|fee waiver)\b'
        ],
        'amount_patterns': [
            r'\$[\d,]+', r'€[\d,]+', r'£[\d,]+', 
            r'full tuition', r'partial funding'
        ],
        'context_keywords': [
            'eligible', 'apply', 'deadline', 'criteria', 'award',
            'merit-based', 'need-based', 'renewable'
        ]
    })
    
    program_patterns: Dict[str, List[str]] = field(default_factory=lambda: {
        'degree_types': [
            r'\b(bachelor|ba|bs|bsc|license|licenciatura)\b',
            r'\b(master|ma|ms|msc|mba|mfa|mastère)\b',
            r'\b(phd|doctorate|doctoral|ph\.d\.)\b',
            r'\b(certificate|diploma|certification)\b'
        ],
        'field_indicators': [
            r'computer science', r'engineering', r'medicine', r'business',
            r'arts', r'sciences', r'economics', r'psychology', r'law'
        ],
        'context_keywords': [
            'curriculum', 'courses', 'credits', 'requirements', 'prerequisites',
            'specialization', 'concentration', 'track', 'pathway'
        ]
    })

    @classmethod
    def load_from_file(cls, config_path: str) -> 'Config':
        """Load configuration from JSON file"""
        if not os.path.exists(config_path):
            return cls()  # Return default config if file doesn't exist
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            return cls._from_dict(config_data)
        except Exception as e:
            print(f"Warning: Failed to load config from {config_path}: {e}")
            return cls()  # Return default config on error

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> 'Config':
        """Create Config from dictionary"""
        config = cls()
        
        # Update crawler config
        if 'crawler' in data:
            for key, value in data['crawler'].items():
                if hasattr(config.crawler, key):
                    setattr(config.crawler, key, value)
        
        # Update extraction config
        if 'extraction' in data:
            for key, value in data['extraction'].items():
                if hasattr(config.extraction, key):
                    setattr(config.extraction, key, value)
        
        # Update validation config
        if 'validation' in data:
            for key, value in data['validation'].items():
                if hasattr(config.validation, key):
                    setattr(config.validation, key, value)
        
        # Update output config
        if 'output' in data:
            for key, value in data['output'].items():
                if hasattr(config.output, key):
                    setattr(config.output, key, value)
        
        # Update logging config
        if 'logging' in data:
            for key, value in data['logging'].items():
                if hasattr(config.logging, key):
                    setattr(config.logging, key, value)
        
        # Update other fields
        for key in ['max_search_results', 'default_search_workers']:
            if key in data:
                setattr(config, key, data[key])
        
        # Update pattern configurations
        for pattern_type in ['university_patterns', 'scholarship_patterns', 'program_patterns']:
            if pattern_type in data:
                setattr(config, pattern_type, data[pattern_type])
        
        return config

    def save_to_file(self, config_path: str):
        """Save configuration to JSON file"""
        config_dir = os.path.dirname(config_path)
        if config_dir:
            os.makedirs(config_dir, exist_ok=True)
        
        config_data = self._to_dict()
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

    def _to_dict(self) -> Dict[str, Any]:
        """Convert Config to dictionary"""
        return {
            'crawler': {
                'max_concurrent': self.crawler.max_concurrent,
                'request_delay': self.crawler.request_delay,
                'max_retries': self.crawler.max_retries,
                'session_timeout': self.crawler.session_timeout,
                'user_agents': self.crawler.user_agents,
                'robots_respect': self.crawler.robots_respect,
                'max_queue_size': self.crawler.max_queue_size
            },
            'extraction': {
                'confidence_threshold': self.extraction.confidence_threshold,
                'max_description_length': self.extraction.max_description_length,
                'enable_nlp': self.extraction.enable_nlp,
                'enable_structured_data': self.extraction.enable_structured_data,
                'enable_text_extraction': self.extraction.enable_text_extraction,
                'similarity_threshold': self.extraction.similarity_threshold,
                'deduplication_enabled': self.extraction.deduplication_enabled
            },
            'validation': {
                'validate_urls': self.validation.validate_urls,
                'validate_emails': self.validation.validate_emails,
                'validate_dates': self.validation.validate_dates,
                'homepage_validation': self.validation.homepage_validation,
                'max_validation_workers': self.validation.max_validation_workers,
                'validation_timeout': self.validation.validation_timeout
            },
            'output': {
                'output_directory': self.output.output_directory,
                'csv_export': self.output.csv_export,
                'json_export': self.output.json_export,
                'api_export': self.output.api_export,
                'backup_enabled': self.output.backup_enabled,
                'compression_enabled': self.output.compression_enabled
            },
            'logging': {
                'level': self.logging.level,
                'format': self.logging.format,
                'file_enabled': self.logging.file_enabled,
                'file_path': self.logging.file_path,
                'console_enabled': self.logging.console_enabled,
                'max_file_size': self.logging.max_file_size,
                'backup_count': self.logging.backup_count
            },
            'max_search_results': self.max_search_results,
            'default_search_workers': self.default_search_workers,
            'university_patterns': self.university_patterns,
            'scholarship_patterns': self.scholarship_patterns,
            'program_patterns': self.program_patterns
        }

    def merge_from_env(self):
        """Merge configuration from environment variables"""
        # Crawler config from env
        if os.getenv('UNISCHOLAR_MAX_CONCURRENT'):
            self.crawler.max_concurrent = int(os.getenv('UNISCHOLAR_MAX_CONCURRENT'))
        
        if os.getenv('UNISCHOLAR_REQUEST_DELAY'):
            self.crawler.request_delay = float(os.getenv('UNISCHOLAR_REQUEST_DELAY'))
        
        # Extraction config from env
        if os.getenv('UNISCHOLAR_CONFIDENCE_THRESHOLD'):
            self.extraction.confidence_threshold = float(os.getenv('UNISCHOLAR_CONFIDENCE_THRESHOLD'))
        
        # Output config from env
        if os.getenv('UNISCHOLAR_OUTPUT_DIR'):
            self.output.output_directory = os.getenv('UNISCHOLAR_OUTPUT_DIR')
        
        # Logging config from env
        if os.getenv('UNISCHOLAR_LOG_LEVEL'):
            self.logging.level = os.getenv('UNISCHOLAR_LOG_LEVEL')

    def validate(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Validate crawler config
        if self.crawler.max_concurrent <= 0:
            issues.append("crawler.max_concurrent must be positive")
        
        if self.crawler.request_delay < 0:
            issues.append("crawler.request_delay must be non-negative")
        
        # Validate extraction config
        if not 0 <= self.extraction.confidence_threshold <= 1:
            issues.append("extraction.confidence_threshold must be between 0 and 1")
        
        if not 0 <= self.extraction.similarity_threshold <= 1:
            issues.append("extraction.similarity_threshold must be between 0 and 1")
        
        # Validate paths
        try:
            os.makedirs(self.output.output_directory, exist_ok=True)
        except Exception as e:
            issues.append(f"Cannot create output directory: {e}")
        
        return issues


# Global config instance
_config = None

def get_config() -> Config:
    """Get the global configuration instance"""
    global _config
    if _config is None:
        _config = Config()
        
        # Try to load from default locations
        for config_path in ['config.json', 'unischolar_config.json', 'verification_config.json']:
            if os.path.exists(config_path):
                _config = Config.load_from_file(config_path)
                break
        
        # Merge environment variables
        _config.merge_from_env()
    
    return _config

def set_config(config: Config):
    """Set the global configuration instance"""
    global _config
    _config = config 