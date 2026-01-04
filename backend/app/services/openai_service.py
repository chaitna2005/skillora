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
        print(f"[OPENAI_SERVICE] Starting question generation")
        print(f"[OPENAI_SERVICE] Requested questions: {total_questions}")
        print(f"[OPENAI_SERVICE] Topic: {prompt}")
        print(f"[OPENAI_SERVICE] Difficulty: {difficulty_level}")
        
        system_prompt = """You are an expert quiz creator. Generate clear, educational quiz questions based on the given topic.

CRITICAL RULES - READ CAREFULLY:
1. You MUST generate EXACTLY the number of questions specified in the user request - NO MORE, NO LESS
2. Before responding, COUNT the questions in your JSON response to ensure it matches the requested number
3. Each question must have exactly 4 options
4. EVERY question MUST have at least one correct answer marked
5. For RADIO type: EXACTLY ONE correct answer (mark exactly one option as "is_correct": true, all others as false)
6. For CHECKLIST type: ONE OR MORE correct answers (mark at least one option as "is_correct": true)
7. Questions should be unambiguous and educational
8. Return ONLY valid JSON, no additional text or explanations

MANDATORY ANSWER REQUIREMENTS:
- EVERY question MUST have at least one option with "is_correct": true
- For RADIO questions: Count the "is_correct": true flags - there MUST be exactly 1
- For CHECKLIST questions: Count the "is_correct": true flags - there MUST be at least 1
- NEVER leave all options as "is_correct": false
- NEVER mark all options as "is_correct": true for RADIO questions

MATHEMATICS-SPECIFIC RULES (if topic involves math):
- For mathematical problems, you MUST verify that the correct answer is mathematically accurate
- Double-check all calculations before marking answers as correct
- For complex mathematics (calculus, algebra, etc.), ensure the correct answer option is the exact solution
- If a question asks to solve an equation, verify the solution is correct by substitution
- For numerical answers, ensure precision matches the question requirements
- Wrong answer options should be plausible but clearly incorrect (common mistakes are acceptable)
- Show mathematical expressions clearly using standard notation

STEP-BY-STEP PROCESS:
1. Read the requested number of questions (e.g., "5 questions")
2. Generate that EXACT number of questions
3. For EACH question:
   a. Ensure it has exactly 4 options
   b. Mark at least one option as "is_correct": true
   c. For RADIO: ensure exactly ONE "is_correct": true
   d. For CHECKLIST: ensure at least ONE "is_correct": true
4. Count the questions in your "questions" array
5. Verify the count matches the requested number
6. Verify every question has correct answers marked
7. Only then, return the JSON response

STRICT RESPONSE FORMAT (MUST FOLLOW EXACTLY):
{
    "questions": [
        {
            "question_text": "What is 2 + 2?",
            "question_type": "RADIO",
            "options": [
                {"option_text": "3", "is_correct": false},
                {"option_text": "4", "is_correct": true},
                {"option_text": "5", "is_correct": false},
                {"option_text": "6", "is_correct": false}
            ]
        },
        {
            "question_text": "Which numbers are even?",
            "question_type": "CHECKLIST",
            "options": [
                {"option_text": "2", "is_correct": true},
                {"option_text": "3", "is_correct": false},
                {"option_text": "4", "is_correct": true},
                {"option_text": "5", "is_correct": false}
            ]
        }
    ]
}

IMPORTANT: Before returning your response, verify:
- Exact question count matches requested number
- Every question has exactly 4 options
- Every RADIO question has exactly 1 "is_correct": true
- Every CHECKLIST question has at least 1 "is_correct": true
- No question has all "is_correct": false
"""
        
        user_prompt = f"""Create EXACTLY {total_questions} quiz questions on the following topic.

TOPIC: {prompt}
DIFFICULTY LEVEL: {difficulty_level}
NUMBER OF QUESTIONS REQUIRED: {total_questions}

CRITICAL REQUIREMENTS:
1. Generate EXACTLY {total_questions} questions - count them before responding
2. Each question MUST have exactly 4 options
3. EVERY question MUST have at least one correct answer marked with "is_correct": true
4. For RADIO questions: mark EXACTLY ONE option as "is_correct": true
5. For CHECKLIST questions: mark AT LEAST ONE option as "is_correct": true
6. NEVER leave all options as "is_correct": false for any question

Question type distribution:
- Approximately 70% should be RADIO type (single correct answer - exactly 1 "is_correct": true)
- Approximately 30% should be CHECKLIST type (multiple correct answers - at least 1 "is_correct": true)

Difficulty level: {difficulty_level}

If this is a mathematics topic, ensure all correct answers are mathematically verified and accurate.

VALIDATION CHECKLIST (verify before responding):
✓ Generated exactly {total_questions} questions
✓ Each question has exactly 4 options
✓ Each RADIO question has exactly 1 "is_correct": true
✓ Each CHECKLIST question has at least 1 "is_correct": true
✓ No question has all options as "is_correct": false

Return ONLY valid JSON following the strict format specified in the system prompt."""

        print(f"[OPENAI_SERVICE] System prompt length: {len(system_prompt)} characters")
        print(f"[OPENAI_SERVICE] User prompt length: {len(user_prompt)} characters")
        print(f"[OPENAI_SERVICE] Model: {settings.OPENAI_MODEL}")
        
        content = None
        try:
            print(f"[OPENAI_SERVICE] Sending request to OpenAI API...")
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent, accurate results
                response_format={"type": "json_object"},
                max_tokens=4000  # Ensure enough tokens for all questions
            )
            
            print(f"[OPENAI_SERVICE] Received response from OpenAI")
            print(f"[OPENAI_SERVICE] Response usage - prompt_tokens: {response.usage.prompt_tokens}, completion_tokens: {response.usage.completion_tokens}, total_tokens: {response.usage.total_tokens}")
            
            content = response.choices[0].message.content
            print(f"[OPENAI_SERVICE] Raw response content length: {len(content)} characters")
            print(f"[OPENAI_SERVICE] Raw response preview (first 500 chars): {content[:500]}")
            
            result = json.loads(content)
            print(f"[OPENAI_SERVICE] Successfully parsed JSON response")
            print(f"[OPENAI_SERVICE] JSON keys: {list(result.keys())}")
            
            # Validate and return questions
            questions = result.get("questions", [])
            print(f"[OPENAI_SERVICE] Questions found in response: {len(questions)}")
            print(f"[OPENAI_SERVICE] Expected questions: {total_questions}")
            
            if len(questions) != total_questions:
                print(f"[OPENAI_SERVICE] ERROR: Question count mismatch!")
                print(f"[OPENAI_SERVICE] Expected: {total_questions}, Got: {len(questions)}")
                print(f"[OPENAI_SERVICE] Difference: {total_questions - len(questions)}")
                # Log each question to see what we got
                for i, q in enumerate(questions):
                    q_text = q.get("question_text", "NO TEXT")[:100]
                    q_type = q.get("question_type", "NO TYPE")
                    q_options = len(q.get("options", []))
                    print(f"[OPENAI_SERVICE] Question {i+1}: type={q_type}, options={q_options}, text_preview='{q_text}'")
            else:
                print(f"[OPENAI_SERVICE] SUCCESS: Question count matches expected number!")
            
            # Validation
            print(f"[OPENAI_SERVICE] Starting validation of questions...")
            validated_count = 0
            for idx, q in enumerate(questions):
                try:
                    if "question_text" not in q or "question_type" not in q or "options" not in q:
                        print(f"[OPENAI_SERVICE] ERROR: Question {idx+1} missing required fields")
                        print(f"[OPENAI_SERVICE] Question {idx+1} keys: {list(q.keys())}")
                        raise ValueError(f"Invalid question format from OpenAI - question {idx+1} missing required fields")
                    
                    if q["question_type"] not in ["RADIO", "CHECKLIST"]:
                        print(f"[OPENAI_SERVICE] WARNING: Question {idx+1} has invalid type '{q['question_type']}', defaulting to RADIO")
                        q["question_type"] = "RADIO"  # Default fallback
                    
                    # Validate options count
                    options_count = len(q.get("options", []))
                    if options_count != 4:
                        print(f"[OPENAI_SERVICE] ERROR: Question {idx+1} has {options_count} options, expected 4")
                        raise ValueError(f"Question {idx+1} must have exactly 4 options, found {options_count}")
                    
                    # Validate correct answers - CRITICAL CHECK
                    correct_count = sum(1 for opt in q["options"] if opt.get("is_correct", False))
                    question_type = q["question_type"]
                    
                    if correct_count == 0:
                        print(f"[OPENAI_SERVICE] ERROR: Question {idx+1} ({question_type}) has NO correct answers marked!")
                        print(f"[OPENAI_SERVICE] Question text: {q.get('question_text', '')[:100]}")
                        print(f"[OPENAI_SERVICE] All options marked as incorrect - this violates the strict format requirement")
                        print(f"[OPENAI_SERVICE] FIXING: Setting first option as correct")
                        q["options"][0]["is_correct"] = True
                        correct_count = 1
                    
                    # For RADIO type, ensure exactly one correct answer
                    if question_type == "RADIO":
                        if correct_count != 1:
                            print(f"[OPENAI_SERVICE] ERROR: Question {idx+1} (RADIO) has {correct_count} correct answers, expected exactly 1")
                            print(f"[OPENAI_SERVICE] Question text: {q.get('question_text', '')[:100]}")
                            print(f"[OPENAI_SERVICE] FIXING: Setting exactly one correct answer (first option)")
                            # Fix: set first option to true, others to false
                            for i, opt in enumerate(q["options"]):
                                opt["is_correct"] = (i == 0)
                            correct_count = 1
                    
                    # For CHECKLIST type, ensure at least one correct answer
                    if question_type == "CHECKLIST":
                        if correct_count == 0:
                            print(f"[OPENAI_SERVICE] ERROR: Question {idx+1} (CHECKLIST) has no correct answers, expected at least 1")
                            print(f"[OPENAI_SERVICE] Question text: {q.get('question_text', '')[:100]}")
                            print(f"[OPENAI_SERVICE] FIXING: Setting first option as correct")
                            q["options"][0]["is_correct"] = True
                            correct_count = 1
                    
                    # Log successful validation
                    if correct_count > 0:
                        print(f"[OPENAI_SERVICE] Question {idx+1} ({question_type}) validated: {correct_count} correct answer(s)")
                    
                    validated_count += 1
                except Exception as e:
                    print(f"[OPENAI_SERVICE] ERROR validating question {idx+1}: {e}")
                    raise
            
            print(f"[OPENAI_SERVICE] Validation complete: {validated_count}/{len(questions)} questions validated")
            
            # Return exactly the requested number
            final_questions = questions[:total_questions]
            print(f"[OPENAI_SERVICE] Returning {len(final_questions)} questions")
            
            if len(final_questions) < total_questions:
                print(f"[OPENAI_SERVICE] WARNING: Returning fewer questions ({len(final_questions)}) than requested ({total_questions})")
            
            return final_questions
                
        except json.JSONDecodeError as e:
            print(f"[OPENAI_SERVICE] ERROR: Failed to parse JSON response")
            print(f"[OPENAI_SERVICE] JSON Error: {e}")
            if content:
                print(f"[OPENAI_SERVICE] Response content that failed to parse (first 1000 chars): {content[:1000]}")
            else:
                print(f"[OPENAI_SERVICE] No content received from OpenAI")
            raise Exception(f"Failed to parse OpenAI response: {str(e)}")
                
        except Exception as e:
            print(f"[OPENAI_SERVICE] ERROR: Exception occurred during question generation")
            print(f"[OPENAI_SERVICE] Exception type: {type(e).__name__}")
            print(f"[OPENAI_SERVICE] Exception message: {str(e)}")
            import traceback
            print(f"[OPENAI_SERVICE] Traceback: {traceback.format_exc()}")
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

