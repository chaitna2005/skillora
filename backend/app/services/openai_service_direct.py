"""
OpenAI Service - Direct HTTP Implementation
Bypasses the OpenAI client library to avoid compatibility issues
"""
import httpx
import json
from typing import List, Dict, Any
from app.config import settings


class OpenAIService:
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.base_url = "https://api.openai.com/v1"
    
    def _make_request(self, messages: List[Dict], temperature: float = 0.7, 
                     response_format: Dict = None, max_tokens: int = None):
        """Make direct HTTP request to OpenAI API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }
        
        if response_format:
            payload["response_format"] = response_format
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    def generate_quiz_questions(
        self, 
        prompt: str, 
        difficulty_level: str, 
        total_questions: int
    ) -> List[Dict[str, Any]]:
        """Generate quiz questions using direct API calls"""
        
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
            result = self._make_request(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            content = result["choices"][0]["message"]["content"]
            data = json.loads(content)
            
            # Validate and return questions
            questions = data.get("questions", [])
            
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
            result = self._make_request(
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
            
            quiz_name = result["choices"][0]["message"]["content"].strip()
            return quiz_name if quiz_name else "General Quiz"
            
        except Exception as e:
            print(f"Quiz name generation error: {e}")
            # Fallback: use first few words of prompt
            words = prompt.split()[:3]
            return " ".join(words).title() + " Quiz"

