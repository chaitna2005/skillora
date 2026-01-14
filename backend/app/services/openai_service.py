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

CRITICAL RULES - STRICTLY FOLLOW THESE:

1. QUESTION COUNT:
   - You MUST generate EXACTLY the number of questions specified in the user request
   - NO MORE, NO LESS
   - Count the questions in your array before responding

2. QUESTION STRUCTURE (MANDATORY):
   - Each question MUST have exactly 4 options
   - Each option MUST have "option_text" and "is_correct" fields
   - The "is_correct" field MUST be a boolean (true or false, NOT a string)

3. CORRECT ANSWERS (CRITICAL - THIS IS MANDATORY):
   - EVERY question MUST have AT LEAST ONE correct answer marked as "is_correct": true
   - For RADIO type: EXACTLY ONE option must have "is_correct": true, all others must be false
   - For CHECKLIST type: ONE OR MORE options must have "is_correct": true
   - NEVER leave all options as false - this is an INVALID question
   - NEVER leave is_correct undefined or null - it MUST be true or false

4. RESPONSE FORMAT:
   - Return ONLY valid JSON, no additional text
   - Use the exact structure shown below
   - DO NOT add extra fields or change field names

5. MATHEMATICS ACCURACY (if topic involves math):
   - Verify all mathematical answers are correct before marking them
   - Double-check calculations
   - Ensure correct answer options are mathematically accurate

VALIDATION CHECKLIST (Check before responding):
✓ Question count matches requested number?
✓ Every question has exactly 4 options?
✓ Every option has "option_text" and "is_correct" fields?
✓ Every question has AT LEAST ONE option with "is_correct": true?
✓ RADIO questions have EXACTLY ONE correct answer?
✓ CHECKLIST questions have AT LEAST ONE correct answer?
✓ All "is_correct" values are boolean (true/false)?
✓ Response is valid JSON?

MANDATORY JSON FORMAT:
{
    "questions": [
        {
            "question_text": "Your question text here?",
            "question_type": "RADIO",
            "options": [
                {"option_text": "First option", "is_correct": false},
                {"option_text": "Second option (correct)", "is_correct": true},
                {"option_text": "Third option", "is_correct": false},
                {"option_text": "Fourth option", "is_correct": false}
            ]
        }
    ]
}

IMPORTANT: If you generate a question where NO option is marked as correct, the question is INVALID and will be rejected. ALWAYS mark at least one correct answer."""
        
        user_prompt = f"""Generate EXACTLY {total_questions} quiz questions with the following requirements:

TOPIC: {prompt}
DIFFICULTY LEVEL: {difficulty_level}
NUMBER OF QUESTIONS REQUIRED: {total_questions}

MANDATORY REQUIREMENTS:
1. Generate EXACTLY {total_questions} questions (count them!)
2. Each question MUST have exactly 4 options
3. EVERY question MUST have at least one correct answer marked as "is_correct": true
4. NEVER leave all options as false

Question type distribution:
- Approximately 70% RADIO type (exactly ONE correct answer per question)
- Approximately 30% CHECKLIST type (multiple correct answers per question)

Difficulty: {difficulty_level}

CRITICAL REMINDERS:
- Each option must have both "option_text" and "is_correct" fields
- "is_correct" must be boolean true or false (not string, not null)
- At least one option per question MUST be marked as correct
- For mathematics, verify your answers are correct before marking them

Generate {total_questions} valid questions following the exact JSON format from the system prompt."""

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
                    # Check required fields
                    if "question_text" not in q or "question_type" not in q or "options" not in q:
                        print(f"[OPENAI_SERVICE] ERROR: Question {idx+1} missing required fields")
                        print(f"[OPENAI_SERVICE] Question {idx+1} keys: {list(q.keys())}")
                        raise ValueError(f"Invalid question format from OpenAI - question {idx+1} missing required fields")
                    
                    # Validate question type
                    if q["question_type"] not in ["RADIO", "CHECKLIST"]:
                        print(f"[OPENAI_SERVICE] WARNING: Question {idx+1} has invalid type '{q['question_type']}', defaulting to RADIO")
                        q["question_type"] = "RADIO"  # Default fallback
                    
                    # Validate options count
                    options_count = len(q.get("options", []))
                    if options_count != 4:
                        print(f"[OPENAI_SERVICE] ERROR: Question {idx+1} has {options_count} options, expected 4")
                        raise ValueError(f"Question {idx+1} must have exactly 4 options, found {options_count}")
                    
                    # Validate each option has required fields and correct type
                    for opt_idx, opt in enumerate(q["options"]):
                        if "option_text" not in opt:
                            print(f"[OPENAI_SERVICE] ERROR: Question {idx+1}, Option {opt_idx+1} missing 'option_text'")
                            raise ValueError(f"Question {idx+1}, Option {opt_idx+1} missing 'option_text'")
                        
                        if "is_correct" not in opt:
                            print(f"[OPENAI_SERVICE] WARNING: Question {idx+1}, Option {opt_idx+1} missing 'is_correct', defaulting to false")
                            opt["is_correct"] = False
                        
                        # Ensure is_correct is boolean
                        if not isinstance(opt["is_correct"], bool):
                            print(f"[OPENAI_SERVICE] WARNING: Question {idx+1}, Option {opt_idx+1} has non-boolean is_correct value: {opt['is_correct']}")
                            # Convert to boolean
                            opt["is_correct"] = bool(opt["is_correct"])
                    
                    # CRITICAL: Ensure at least one correct answer
                    has_correct = any(opt.get("is_correct", False) for opt in q["options"])
                    if not has_correct:
                        print(f"[OPENAI_SERVICE] CRITICAL WARNING: Question {idx+1} has NO correct answer! AI did not mark any option as correct.")
                        print(f"[OPENAI_SERVICE] Question text: {q.get('question_text', '')[:100]}")
                        print(f"[OPENAI_SERVICE] Fixing by marking first option as correct")
                        q["options"][0]["is_correct"] = True
                    
                    # For RADIO type, ensure exactly one correct answer
                    if q["question_type"] == "RADIO":
                        correct_count = sum(1 for opt in q["options"] if opt.get("is_correct", False))
                        if correct_count != 1:
                            print(f"[OPENAI_SERVICE] WARNING: Question {idx+1} (RADIO) has {correct_count} correct answers, fixing to 1")
                            # Fix: keep first correct, set others to false
                            first_correct_found = False
                            for opt in q["options"]:
                                if opt.get("is_correct", False):
                                    if not first_correct_found:
                                        opt["is_correct"] = True
                                        first_correct_found = True
                                    else:
                                        opt["is_correct"] = False
                    
                    # For CHECKLIST type, ensure at least one correct answer
                    if q["question_type"] == "CHECKLIST":
                        correct_count = sum(1 for opt in q["options"] if opt.get("is_correct", False))
                        if correct_count == 0:
                            print(f"[OPENAI_SERVICE] WARNING: Question {idx+1} (CHECKLIST) has no correct answers, fixing")
                            q["options"][0]["is_correct"] = True
                    
                    validated_count += 1
                except Exception as e:
                    print(f"[OPENAI_SERVICE] ERROR validating question {idx+1}: {e}")
                    raise
            
            print(f"[OPENAI_SERVICE] Validation complete: {validated_count}/{len(questions)} questions validated")
            
            # CRITICAL: Ensure we have exactly the requested number of questions
            print(f"[OPENAI_SERVICE] Checking question count...")
            print(f"[OPENAI_SERVICE] Requested: {total_questions}")
            print(f"[OPENAI_SERVICE] Received from AI: {len(questions)}")
            
            if len(questions) < total_questions:
                error_msg = f"OpenAI returned {len(questions)} questions but {total_questions} were requested. Please try again or reduce the question count."
                print(f"[OPENAI_SERVICE] ERROR: {error_msg}")
                raise ValueError(error_msg)
            
            # Return exactly the requested number (slice in case AI returned more)
            final_questions = questions[:total_questions]
            print(f"[OPENAI_SERVICE] Returning exactly {len(final_questions)} questions")
            
            # Remove duplicates by question text (case-insensitive)
            seen_questions = set()
            unique_questions = []
            for q in final_questions:
                q_text_normalized = q.get("question_text", "").strip().lower()
                if q_text_normalized and q_text_normalized not in seen_questions:
                    seen_questions.add(q_text_normalized)
                    unique_questions.append(q)
                else:
                    print(f"[OPENAI_SERVICE] Duplicate question detected and removed: '{q.get('question_text', '')[:80]}'")
            
            print(f"[OPENAI_SERVICE] After deduplication: {len(unique_questions)} unique questions")
            
            if len(unique_questions) < total_questions:
                error_msg = f"After removing duplicates, only {len(unique_questions)} unique questions remain out of {total_questions} requested. Please try again."
                print(f"[OPENAI_SERVICE] ERROR: {error_msg}")
                raise ValueError(error_msg)
            
            return unique_questions[:total_questions]
                
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

