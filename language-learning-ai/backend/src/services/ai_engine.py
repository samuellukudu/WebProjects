import os
from typing import Dict, Any
from openai import OpenAI
import json
from datetime import datetime

# Initialize OpenAI client
client = OpenAI(
    base_url='http://localhost:11434/v1',
    api_key='ollama',
)

class AIService:
    @staticmethod
    def generate_assessment(language: str, level: str) -> Dict[str, Any]:
        try:
            prompt = f"""Generate a language assessment for {language} at {level} level.
            Include 5 questions with the following structure:
            - 3 multiple choice questions
            - 2 open-ended questions
            
            The response MUST be a valid JSON object with this EXACT structure:
            {{
                "title": "Assessment title",
                "questions": [
                    {{
                        "id": 1,
                        "text": "question text",
                        "type": "multiple_choice",
                        "options": ["option1", "option2", "option3", "option4"],
                        "correct_answer": "correct option"
                    }},
                    {{
                        "id": 2,
                        "text": "open question text",
                        "type": "open_ended"
                    }}
                ]
            }}
            
            Only return the JSON, no additional text or explanations.
            """

            response = client.chat.completions.create(
                model="qwen2.5:0.5b",
                messages=[
                    {"role": "system", "content": "You are a language assessment expert. Only respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ]
            )

            content = response.choices[0].message.content.strip()
            
            # Try to find JSON content between curly braces
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = content[start_idx:end_idx]
                return json.loads(json_str)
            else:
                return {
                    "title": f"{language.capitalize()} {level.capitalize()} Assessment",
                    "questions": [
                        {
                            "id": 1,
                            "text": "Default question due to formatting error",
                            "type": "multiple_choice",
                            "options": ["Option A", "Option B", "Option C", "Option D"],
                            "correct_answer": "Option A"
                        }
                    ]
                }

        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {e}")
            print(f"Raw response: {content}")
            raise Exception("Failed to generate valid assessment format")
        except Exception as e:
            print(f"Error generating assessment: {e}")
            raise Exception(f"Failed to generate assessment: {str(e)}")

    @staticmethod
    def evaluate_response(question: str, user_response: str, language: str) -> Dict[str, Any]:
        try:
            prompt = f"""Evaluate this language response:
            Question: {question}
            User's response: {user_response}
            Language: {language}

            Provide feedback in JSON format:
            {{
                "score": <float between 0 and 1>,
                "feedback": "detailed feedback",
                "correct": <boolean>,
                "suggestions": ["improvement suggestion 1", "improvement suggestion 2"]
            }}
            """

            response = client.chat.completions.create(
                model="qwen2.5:0.5b",
                messages=[
                    {"role": "system", "content": "You are a language assessment expert. Only respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ]
            )

            content = response.choices[0].message.content.strip()
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                return json.loads(content[start_idx:end_idx])
            else:
                return {
                    "score": 0.5,
                    "feedback": "Unable to generate proper feedback",
                    "correct": False,
                    "suggestions": ["Please try again"]
                }

        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {e}")
            print(f"Raw response: {content}")
            return {
                "score": 0,
                "feedback": "Error processing response",
                "correct": False,
                "suggestions": ["System error, please try again"]
            }
        except Exception as e:
            print(f"Error evaluating response: {e}")
            raise Exception(f"Failed to evaluate response: {str(e)}")

    @staticmethod
    def adapt_curriculum(
        current_curriculum: Dict[str, Any],
        progress_data: Dict[str, Any],
        feedback_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Adapt curriculum based on user progress and feedback."""
        try:
            prompt = f"""Analyze learning progress and feedback to adapt curriculum:
            Current Curriculum: {json.dumps(current_curriculum, indent=2)}
            Progress Data: {json.dumps(progress_data, indent=2)}
            Feedback Data: {json.dumps(feedback_data, indent=2)}
            
            Generate adapted curriculum in JSON format:
            {{
                "adjustments": [
                    {{
                        "topic": "topic name",
                        "change_type": "modify|add|remove",
                        "reason": "explanation",
                        "new_content": {{}}
                    }}
                ],
                "difficulty_changes": {{
                    "topic": "new difficulty level",
                    "reason": "explanation"
                }},
                "additional_resources": [
                    {{
                        "type": "resource type",
                        "focus": "target area",
                        "description": "why needed"
                    }}
                ]
            }}
            """

            response = client.chat.completions.create(
                model="qwen2.5:0.5b",
                messages=[
                    {"role": "system", "content": "You are a curriculum adaptation expert."},
                    {"role": "user", "content": prompt}
                ]
            )

            content = response.choices[0].message.content.strip()
            return AIService._extract_json_content(content)
        except Exception as e:
            print(f"Error adapting curriculum: {e}")
            return {"error": "Failed to adapt curriculum"}

    @staticmethod
    def _extract_json_content(content: str) -> Dict[str, Any]:
        """Extract and validate JSON content from AI response."""
        start_idx = content.find('{')
        end_idx = content.rfind('}') + 1
        
        if start_idx != -1 and end_idx != -1:
            try:
                return json.loads(content[start_idx:end_idx])
            except json.JSONDecodeError:
                return {"error": "Invalid JSON format"}
        return {"error": "No JSON content found"}

def analyze_user_input(user_input: str) -> Dict[str, Any]:
    prompt = f"""Analyze this user's language learning preferences and needs:
    User Input: {user_input}
    
    Provide analysis in JSON format:
    {{
        "learning_style": "visual|auditory|reading|kinesthetic",
        "proficiency_level": "beginner|intermediate|advanced",
        "struggles": ["area1", "area2"],
        "interests": ["interest1", "interest2"],
        "recommended_focus": ["focus1", "focus2"]
    }}
    """

    response = client.chat.completions.create(
        model="qwen2.5:0.5b",
        messages=[
            {"role": "system", "content": "You are a language learning expert."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)

def analyze_user_preferences(onboarding_data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        prompt = f"""Based on this user data, provide learning recommendations:
        {json.dumps(onboarding_data, indent=2)}
        
        Return ONLY a valid JSON object with this EXACT structure:
        {{
            "recommended_resources": [
                {{
                    "type": "string",
                    "description": "string",
                    "focus_area": "string"
                }}
            ],
            "learning_path": {{
                "initial_focus": ["string"],
                "progression_plan": ["string"],
                "estimated_timeline": "string"
            }},
            "specialized_content": {{
                "industry_specific": ["string"],
                "skill_specific": ["string"]
            }}
        }}"""

        response = client.chat.completions.create(
            model="qwen2.5:0.5b",
            messages=[
                {"role": "system", "content": "You are a language learning expert. Respond only with valid JSON."},
                {"role": "user", "content": prompt}
            ]
        )

        content = response.choices[0].message.content.strip()
        
        # Extract JSON content
        start_idx = content.find('{')
        end_idx = content.rfind('}') + 1
        
        if start_idx != -1 and end_idx != -1:
            json_str = content[start_idx:end_idx]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"JSON Decode Error: {e}")
                print(f"Attempted to parse: {json_str}")
                return generate_fallback_recommendations(onboarding_data)
        else:
            return generate_fallback_recommendations(onboarding_data)

    except Exception as e:
        print(f"Error in analyze_user_preferences: {e}")
        return generate_fallback_recommendations(onboarding_data)

def generate_fallback_recommendations(onboarding_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate fallback recommendations when AI response fails."""
    language = onboarding_data.get('language', 'unknown')
    level = onboarding_data.get('proficiency_level', 'beginner')
    
    return {
        "recommended_resources": [
            {
                "type": "video",
                "description": f"Basic {language} lessons for {level} level",
                "focus_area": "general comprehension"
            }
        ],
        "learning_path": {
            "initial_focus": ["basic vocabulary", "essential grammar"],
            "progression_plan": ["fundamentals", "practice", "advanced topics"],
            "estimated_timeline": "3 months"
        },
        "specialized_content": {
            "industry_specific": ["general business vocabulary"],
            "skill_specific": ["basic communication skills"]
        }
    }

def generate_learning_path(user_analysis: Dict[str, Any]) -> Dict[str, Any]:
    prompt = f"""Create a personalized learning path based on this analysis:
    {json.dumps(user_analysis, indent=2)}
    
    Generate a curriculum in JSON format:
    {{
        "topics": [
            {{
                "topic": "topic name",
                "resources": [
                    {{
                        "title": "resource title",
                        "type": "video|article|exercise|quiz",
                        "url": "resource url",
                        "description": "resource description"
                    }}
                ],
                "duration": "X weeks"
            }}
        ],
        "estimated_completion_time": "X months",
        "milestones": ["milestone1", "milestone2"]
    }}
    """

    response = client.chat.completions.create(
        model="qwen2.5:0.5b",
        messages=[
            {"role": "system", "content": "You are a curriculum development expert."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)

def create_personalized_curriculum(user_input: str) -> Dict[str, Any]:
    analysis = analyze_user_input(user_input)
    learning_path = generate_learning_path(analysis)
    return {
        "analysis": analysis,
        "curriculum": learning_path
    }