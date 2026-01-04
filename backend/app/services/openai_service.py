"""
OpenAI Service
Handles AI question generation using OpenAI API
"""
from openai import OpenAI
import json
from typing import List, Dict, Any
from app.config import settings

# Initialize OpenAI client at module level to avoid initialization issues
_openai_client = None

def get_openai_client():
    """Get or create OpenAI client singleton"""
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai_client


class OpenAIService:
    
    def __init__(self):
        # Use the module-level client
        self.client = get_openai_client()
    
    def generate_quiz_questions(
        self, 
        prompt: str, 
        difficulty_level: str, 
        total_questions: int
    ) -> List[Dict[str, Any]]:
        """
        Generate quiz questions based on prompt and difficulty
        
        Returns:
            List of questions with format:
            [
                {
                    "question_text": "...",
                    "question_type": "RADIO" | "CHECKLIST",
                    "options": [
                        {"option_text": "...", "is_correct": True/False},
                        ...
                    ]
                },
                ...
            ]
        """
        system_prompt = """You are an expert quiz creator. Generate clear, educational quiz questions based on the given topic.

Rules:
1. Create questions that match the specified difficulty level
2. Each question should have 4 options
3. For RADIO type: exactly ONE correct answer
4. For CHECKLIST type: one or MORE correct answers
5. Questions should be unambiguous and educational
6. Return ONLY valid JSON, no additional text

Response format:
{
    "questions": [
        {
            "question_text": "What is...?",
            "question_type": "RADIO",
            "options": [
                {"option_text": "Option A", "is_correct": false},
                {"option_text": "Option B", "is_correct": true},
                {"option_text": "Option C", "is_correct": false},
                {"option_text": "Option D", "is_correct": false}
            ]
        }
    ]
}
"""
        
        user_prompt = f"""Create {total_questions} quiz questions on the following topic:

Topic: {prompt}
Difficulty: {difficulty_level}
Number of questions: {total_questions}

Mix of question types:
- 70% RADIO (single correct answer)
- 30% CHECKLIST (multiple correct answers)

Ensure questions are appropriate for {difficulty_level} difficulty level."""

        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # Validate and return questions
            questions = result.get("questions", [])
            
            # Validation
            for q in questions:
                if "question_text" not in q or "question_type" not in q or "options" not in q:
                    raise ValueError("Invalid question format from OpenAI")
                
                if q["question_type"] not in ["RADIO", "CHECKLIST"]:
                    q["question_type"] = "RADIO"  # Default fallback
                
                # Ensure at least one correct answer
                has_correct = any(opt.get("is_correct", False) for opt in q["options"])
                if not has_correct:
                    q["options"][0]["is_correct"] = True
            
            return questions[:total_questions]  # Ensure we return exact number
            
        except Exception as e:
            print(f"OpenAI API Error: {e}")
            raise Exception(f"Failed to generate questions: {str(e)}")
    
    def generate_quiz_name(self, prompt: str) -> str:
        """Generate a concise quiz name from the prompt"""
        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system", 
                        "content": "Generate a short, descriptive quiz title (max 5 words) from the given prompt. Return only the title, nothing else."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=20
            )
            
            quiz_name = response.choices[0].message.content.strip()
            return quiz_name if quiz_name else "General Quiz"
            
        except Exception as e:
            print(f"Quiz name generation error: {e}")
            # Fallback: use first few words of prompt
            words = prompt.split()[:3]
            return " ".join(words).title() + " Quiz"

