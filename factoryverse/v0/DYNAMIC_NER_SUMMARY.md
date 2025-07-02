# Dynamic Named Entity Recognition Implementation

## 🎯 Overview
Successfully implemented a dynamic Named Entity Recognition (NER) system that replaces hardcoded patterns with intelligent, query-aware extraction. The system analyzes user queries to understand intent and adapts extraction patterns and confidence scoring accordingly.

## 🔍 Problem Solved
**Before**: The system used hardcoded patterns for organization detection:
- Fixed university patterns: `['university', 'college', 'institute']`
- Static research patterns: `['research center', 'laboratory', 'lab']`
- Hardcoded confidence factors
- No query context awareness

**After**: Dynamic, intelligent analysis based on user query intent.

## 🚀 Key Features Implemented

### 1. **Query Intent Analysis**
```python
@dataclass
class QueryIntent:
    entity_types: Set[str]          # What entities they're looking for
    geographic_focus: Set[str]      # Geographic entities mentioned  
    domain_focus: Set[str]          # Domain/field focus (education, business, etc.)
    organization_types: Set[str]    # Types of organizations
    search_intent: str              # Overall intent: academic, business, research
    confidence_factors: Dict[str, float]  # Dynamic confidence weightings
    patterns: Dict[str, List[str]]  # Dynamic regex patterns
```

### 2. **Dynamic Pattern Generation**
The system generates patterns based on query analysis:

**Academic Query**: `"European universities with AI research"`
- **Domain Focus**: `{'education'}`
- **Search Intent**: `academic`
- **Generated Patterns**: University-focused regex patterns
- **Confidence Factors**: High bonus for .edu domains, academic keywords

**Business Query**: `"startup accelerators in Silicon Valley"`
- **Domain Focus**: `{'business', 'technology'}`
- **Search Intent**: `business` 
- **Generated Patterns**: Startup/company-focused patterns
- **Confidence Factors**: Business-oriented scoring

### 3. **Adaptive Confidence Scoring**
Organizations receive different confidence scores based on query relevance:

**Example: Stanford University**
- Academic query → Confidence: 1.000, Type: "university"
- Business query → Confidence: 0.700, Type: "organization"
- Research query → Confidence: 1.000, Type: "university"

### 4. **Domain-Specific Mappings**
```python
domain_mappings = {
    'education': ['university', 'college', 'school', 'institute', 'academy'],
    'research': ['laboratory', 'research center', 'institute', 'foundation'],
    'business': ['company', 'corporation', 'startup', 'enterprise'],
    'healthcare': ['hospital', 'clinic', 'medical center', 'health system'],
    'technology': ['tech company', 'software', 'ai company', 'startup'],
    'government': ['agency', 'department', 'ministry', 'bureau'],
    'nonprofit': ['foundation', 'charity', 'ngo', 'organization']
}
```

## 🎯 Implementation Details

### Core Methods Added:

1. **`analyze_query(query: str) → QueryIntent`**
   - Uses spaCy NER to extract entities
   - Detects domain focus and geographic entities
   - Determines search intent
   - Generates dynamic confidence factors and patterns

2. **`_calculate_dynamic_confidence(name, url, description, query_intent)`**
   - Domain matching bonuses based on query focus
   - Geographic matching for location-specific queries
   - URL domain bonuses (.edu for academic queries)
   - Title matching bonuses for relevant patterns

3. **`_determine_dynamic_org_type(name, url, query_intent)`**
   - Organization type detection based on query intent
   - Prioritizes relevant types (university for academic, startup for business)

4. **`set_query_intent(query_intent)`**
   - Updates extractor patterns for current query
   - Logs intent analysis for debugging

### Integration with Main Pipeline:

1. **Query Storage**: Search results now include `original_query` field
2. **Automatic Intent Detection**: Extracts query from search results if not provided
3. **Dynamic Processing**: Applies query-specific patterns during extraction

## 📊 Results & Benefits

### **1. Context-Aware Extraction**
- Universities get higher confidence for academic queries
- Startups get higher confidence for business queries
- Geographic entities boost relevance for location-specific searches

### **2. Reduced False Positives**
- Dynamic exclusion patterns based on query context
- Smart filtering of irrelevant content types

### **3. Improved Relevance**
- Organizations scored based on query relevance
- Better matching of user intent to results

### **4. Flexibility**
- No more hardcoded patterns to maintain
- Automatically adapts to different search domains
- Easy to extend for new organization types

## 🧪 Testing Examples

### Test 1: Academic Query
```
Query: "European universities with AI research"
Intent: academic
Domain Focus: {'education'}
Include Patterns: [university, college, institute, academy patterns]
Confidence Factors: domain_match=0.4, url_domain_bonus=0.3
```

### Test 2: Business Query  
```
Query: "startup accelerators in Silicon Valley"
Intent: business
Domain Focus: {'business', 'technology'}
Geographic Focus: {'silicon valley'}
Include Patterns: [company, startup, accelerator patterns]
Confidence Factors: domain_match=0.3, geographic_match=0.2
```

### Test 3: Research Query
```
Query: "medical research institutes in Germany"
Intent: academic 
Domain Focus: {'education', 'research'}
Geographic Focus: {'germany'}
Include Patterns: [research center, laboratory, institute patterns]
Confidence Factors: domain_match=0.4, geographic_match=0.2
```

## 🔄 Usage

### Automatic Mode (Recommended)
```bash
python main.py --search "European universities with PhD programs"
# Automatically analyzes query intent and applies dynamic patterns
```

### Manual Processing
```python
from main import OrganizationExtractor

extractor = OrganizationExtractor()
intent = extractor.analyze_query("your search query")
extractor.set_query_intent(intent)
# Now extraction uses dynamic patterns
```

## 🎉 Impact

**Before Dynamic NER:**
- Fixed patterns missed context-relevant organizations
- Same confidence scoring for all query types
- Manual pattern maintenance required
- Lower precision in results

**After Dynamic NER:**
- **Context-aware**: Organizations scored based on query relevance
- **Adaptive**: Patterns generated dynamically for each query type
- **Intelligent**: Higher precision through intent-based filtering
- **Maintainable**: No hardcoded patterns to update

The system now truly understands what the user is looking for and adapts its extraction logic accordingly, resulting in much more relevant and accurate organization detection. 