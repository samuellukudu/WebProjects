# UniScholar - Modular Educational Dataset Platform

A robust, scalable, and modular platform for extracting, processing, and managing comprehensive educational data including universities, scholarships, academic programs, student events, and funding opportunities.

## 📁 Project Structure

```
unischolar/                         # Main package directory
├── __init__.py                     # Package initialization and exports
├── main.py                         # Main CLI entry point
├── core/                           # Core components
│   ├── __init__.py
│   ├── models.py                   # Data models (University, Scholarship, etc.)
│   ├── config.py                   # Configuration management
│   └── exceptions.py               # Custom exceptions
├── extractors/                     # Data extraction modules
│   ├── __init__.py
│   ├── base.py                     # Base extractor classes
│   ├── dynamic_ner.py              # Dynamic NER extractor
│   ├── organization.py             # Organization extractor
│   └── intent_analyzer.py          # Query intent analysis
├── crawlers/                       # Web crawling modules
│   ├── __init__.py
│   ├── base.py                     # Base crawler class
│   ├── academic.py                 # Academic-focused crawler
│   └── web_scraper.py              # General web scraper
├── processors/                     # Data processing modules
│   ├── __init__.py
│   ├── base.py                     # Base processor
│   ├── post_processor.py           # Data cleaning and validation
│   ├── validators.py               # Data validators
│   └── enrichers.py                # Data enrichers
├── utils/                          # Utility modules
│   ├── __init__.py
│   ├── web_utils.py                # Web operations utilities
│   ├── text_utils.py               # Text processing utilities
│   └── file_utils.py               # File I/O utilities
└── cli/                            # Command-line interface
    ├── __init__.py
    └── commands.py                 # CLI command handlers
```

## 🚀 Getting Started

### Installation

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install spaCy English Model**
   ```bash
   python -m spacy download en_core_web_sm
   ```

3. **Verify Installation**
   ```bash
   python -m unischolar.main validate-config
   ```

### Running the Platform

The platform can be run using the module syntax:

```bash
python -m unischolar.main [command] [options]
```

## 🎯 Core Features

### 1. **Comprehensive Data Models**

The platform supports extraction of 5 main entity types:

- **Universities** - Academic institutions with rankings, programs, and admissions data
- **Scholarships** - Financial aid opportunities with eligibility and application details  
- **Academic Programs** - Degree programs with curriculum and career information
- **Student Events** - Conferences, competitions, workshops, and networking opportunities
- **Funding** - Research grants and project funding opportunities

### 2. **Dynamic NER Extraction**

Intelligent entity extraction that:
- Analyzes query intent to understand what you're looking for
- Adapts extraction patterns based on domain focus (academic, business, research)
- Provides confidence scoring and relevance ranking
- Supports geographic and field-specific filtering

### 3. **Modular Architecture**

- **Extractors** - Pluggable extraction engines for different content types
- **Crawlers** - Specialized web crawlers for different source types
- **Processors** - Data cleaning, validation, and enrichment pipelines
- **Utils** - Reusable utilities for common operations

## 📋 Available Commands

### Search Command
Extract entities based on a search query:

```bash
# Basic search
python -m unischolar.main search "universities in Germany computer science"

# Advanced search with options
python -m unischolar.main search "AI scholarships" --max-results 50 --output scholarships.csv

# Search for specific entity types
python -m unischolar.main search "PhD programs machine learning" --max-results 100
```

### Process Command
Process existing data files:

```bash
# Process existing results
python -m unischolar.main process --input search_results.csv

# Process with custom output
python -m unischolar.main process --input raw_data.csv --output cleaned_data.csv
```

### Configuration Validation
Validate your configuration:

```bash
python -m unischolar.main validate-config
```

## ⚙️ Configuration

### Configuration File

Create a `config.json` file to customize behavior:

```json
{
  "crawler": {
    "max_concurrent": 5,
    "request_delay": 1.0,
    "max_retries": 3,
    "session_timeout": 30
  },
  "extraction": {
    "confidence_threshold": 0.5,
    "enable_nlp": true,
    "deduplication_enabled": true
  },
  "output": {
    "output_directory": "output",
    "csv_export": true,
    "json_export": true
  },
  "logging": {
    "level": "INFO",
    "file_enabled": true,
    "file_path": "logs/unischolar.log"
  }
}
```

### Environment Variables

Override configuration with environment variables:

```bash
export UNISCHOLAR_MAX_CONCURRENT=10
export UNISCHOLAR_CONFIDENCE_THRESHOLD=0.7
export UNISCHOLAR_OUTPUT_DIR="/path/to/output"
export UNISCHOLAR_LOG_LEVEL=DEBUG
```

## 🎓 Use Cases & Examples

### 1. University Discovery
Find universities with specific programs in target countries:

```bash
python -m unischolar.main search "computer science universities Germany English programs" --max-results 50
```

**Expected Results**: German universities offering CS programs taught in English, with rankings, tuition, and admission requirements.

### 2. Scholarship Research  
Discover funding opportunities for specific demographics:

```bash
python -m unischolar.main search "scholarships international students engineering" --max-results 100
```

**Expected Results**: Engineering scholarships for international students with amounts, eligibility, and deadlines.

### 3. Academic Program Analysis
Compare academic programs with industry connections:

```bash
python -m unischolar.main search "MBA programs internship opportunities" --max-results 75
```

**Expected Results**: MBA programs emphasizing practical experience with corporate partnerships and placement rates.

### 4. Research Opportunities
Find funded research positions:

```bash
python -m unischolar.main search "PhD positions AI funding Europe" --max-results 50
```

**Expected Results**: Funded AI PhD positions in Europe with supervisor info and project details.

### 5. Student Event Discovery
Locate academic conferences and competitions:

```bash
python -m unischolar.main search "data science conferences students 2024" --max-results 30
```

**Expected Results**: Student-focused data science events with dates, locations, and registration information.

## 🔧 Extending the Platform

### Adding New Extractors

1. Create a new extractor in `unischolar/extractors/`:

```python
from .base import EntityExtractor
from ..core.models import YourEntityType

class YourExtractor(EntityExtractor):
    def __init__(self):
        super().__init__("your_entity_type")
    
    def extract(self, html_content: str, source_url: str, **kwargs):
        # Your extraction logic here
        pass
```

2. Update `unischolar/extractors/__init__.py` to export your extractor.

### Adding New Data Models

1. Define your model in `unischolar/core/models.py`:

```python
@dataclass
class YourEntity:
    name: str
    url: str
    # Add your fields here
    extraction_source: str = ""
    last_updated: datetime = field(default_factory=datetime.now)
```

2. Update the `__all__` list in the module.

### Custom Processing

Create custom processors in `unischolar/processors/`:

```python
from .base import BaseProcessor

class YourProcessor(BaseProcessor):
    def process(self, data):
        # Your processing logic
        return processed_data
```

## 📊 Data Quality & Validation

The platform includes comprehensive data quality measures:

### Validation Rules
- **Required Fields**: Ensures essential data is present
- **URL Validation**: Checks domain accessibility and SSL certificates  
- **Name Validation**: Filters spam and validates proper formatting
- **Geographic Validation**: Verifies country codes and city names

### Duplicate Detection
- **Name Similarity**: Fuzzy matching with 85% threshold
- **URL Canonicalization**: Handles redirects and domain variations
- **Content Fingerprinting**: Compares key field combinations

### Quality Scoring
- **Completeness**: Percentage of filled required fields
- **Accuracy**: Validation success rate for data points
- **Freshness**: Age of data (target: <30 days for time-sensitive info)
- **Source Reliability**: Historical accuracy and update frequency

## 🚧 Development Status

This is the modular refactor of the original UniScholar codebase. Current status:

### ✅ Completed
- [x] Modular package structure
- [x] Core data models for all entity types
- [x] Configuration management system
- [x] Dynamic NER extractor framework
- [x] Basic CLI interface
- [x] Post-processing pipeline structure

### 🚧 In Progress  
- [ ] Complete extractor implementations
- [ ] Web crawler integration
- [ ] Real search API integration (DuckDuckGo, etc.)
- [ ] Academic-specific extractors
- [ ] Validation and enrichment modules

### 📋 Planned
- [ ] API server for programmatic access
- [ ] Web dashboard for data exploration
- [ ] Advanced analytics and insights
- [ ] Multi-language support
- [ ] Integration with external databases

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** your changes: `git commit -m 'Add amazing feature'`
4. **Push** to the branch: `git push origin feature/amazing-feature`
5. **Open** a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built upon the comprehensive student dataset plan outlined in `STUDENT_DATASET_PLAN.md`
- Inspired by the need for accessible educational opportunity discovery
- Designed for scalability and maintainability from the ground up

---

**Note**: This is a modular refactor designed to be scalable and maintainable. The legacy scripts are still available in the root directory for reference, but the new modular structure in the `unischolar/` package is the recommended approach going forward. 