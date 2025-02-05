from typing import Dict, List, Any

# Mock database structures
mock_assessments = {
    "beginner": {
        "english": [
            {
                "id": 1,
                "title": "Basic English Assessment",
                "questions": [
                    {
                        "id": 1,
                        "text": "What is the plural of 'child'?",
                        "options": ["childs", "children", "childen", "kids"],
                        "correct_answer": "children",
                        "type": "multiple_choice"
                    },
                    {
                        "id": 2,
                        "text": "Write a simple sentence using 'yesterday'",
                        "type": "open_ended"
                    }
                ],
                "level": "beginner",
                "language": "english"
            }
        ],
        "spanish": [
            {
                "id": 2,
                "title": "Evaluación Básica de Español",
                "questions": [
                    {
                        "id": 1,
                        "text": "¿Cómo se dice 'hello' en español?",
                        "options": ["hola", "adiós", "gracias", "por favor"],
                        "correct_answer": "hola",
                        "type": "multiple_choice"
                    }
                ],
                "level": "beginner",
                "language": "spanish"
            }
        ]
    },
    "intermediate": {
        "english": [],
        "spanish": []
    },
    "advanced": {
        "english": [],
        "spanish": []
    }
}

# Add this new mock data structure
mock_curriculum = {
    "english": {
        "beginner": [
            {
                "topic": "Basic Grammar",
                "resources": [
                    {
                        "title": "Present Simple",
                        "type": "video",
                        "url": "https://example.com/present-simple",
                        "description": "Learn the basics of present simple tense"
                    }
                ],
                "duration": "1 week"
            }
        ]
    }
}

# Language levels and their requirements
language_levels = {
    "beginner": {
        "vocabulary_range": "500-1000 words",
        "grammar_topics": ["present simple", "past simple", "basic questions"],
        "required_score": 0.6
    },
    "intermediate": {
        "vocabulary_range": "1500-2500 words",
        "grammar_topics": ["present perfect", "conditionals", "passive voice"],
        "required_score": 0.7
    },
    "advanced": {
        "vocabulary_range": "3000+ words",
        "grammar_topics": ["advanced tenses", "idioms", "academic writing"],
        "required_score": 0.8
    }
}

def get_assessment(language: str, level: str) -> Dict[str, Any]:
    """Retrieve an assessment based on language and level."""
    try:
        assessments = mock_assessments[level][language]
        return assessments[0] if assessments else None
    except KeyError:
        return None

def get_level_requirements(level: str) -> Dict[str, Any]:
    """Get the requirements for a specific language level."""
    return language_levels.get(level, None)

def add_assessment(assessment: Dict[str, Any]) -> Dict[str, Any]:
    """Add a new assessment to the mock database."""
    level = assessment["level"]
    language = assessment["language"]
    if level in mock_assessments and language in mock_assessments[level]:
        mock_assessments[level][language].append(assessment)
        return assessment
    return None

def get_curriculum(language: str, level: str) -> Dict[str, Any]:
    """Retrieve curriculum based on language and level."""
    default_topic = {
        "topic": "Getting Started",
        "resources": [
            {
                "title": "Introduction",
                "type": "video",
                "url": f"https://example.com/{language}/{level}/intro",
                "description": f"Introduction to {language} for {level} level"
            }
        ],
        "duration": "1 week"
    }

    if language not in mock_curriculum:
        return {
            "language": language,
            "level": level,
            "topics": [default_topic]
        }

    if level not in mock_curriculum[language]:
        return {
            "language": language,
            "level": level,
            "topics": [default_topic]
        }

    topics = mock_curriculum[language][level]
    return {
        "language": language,
        "level": level,
        "topics": topics if topics else [default_topic]
    }

def create_curriculum(curriculum_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new curriculum entry."""
    language = curriculum_data["language"]
    level = curriculum_data["level"]
    
    if language not in mock_curriculum:
        mock_curriculum[language] = {}
    if level not in mock_curriculum[language]:
        mock_curriculum[language][level] = []
    
    mock_curriculum[language][level].extend(curriculum_data["topics"])
    return curriculum_data
