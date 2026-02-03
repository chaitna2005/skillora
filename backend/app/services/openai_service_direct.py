"""
OpenAI Service - Direct HTTP Implementation
Bypasses the OpenAI client library to avoid compatibility issues
"""
import httpx
import json
import re
import math
from typing import List, Dict, Any, Optional
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
    ) -> Dict[str, Any]:
        """Generate quiz questions using direct API calls"""
        
        system_prompt = """You are an expert quiz creator and answer validator. Generate clear, educational, and fully correct quiz questions based on the given topic.

RULES:

1. Create questions that match the specified difficulty level.
2. Each question MUST have exactly 4 options.
3. For RADIO type: EXACTLY ONE correct answer.
4. For CHECKLIST type: ONE OR MORE correct answers.
5. Questions must be clear, medium-length, and unambiguous.
6. Generate a short, relevant quiz title (max 5 words).
7. Return ONLY valid JSON, no explanations or extra text.
8. Do not include comments or formatting outside JSON.
9. ALL questions must be UNIQUE (no duplicates).
10. The correct answer MUST always exist EXACTLY in the options list.
11. NEVER create a question where all options are incorrect.
12. Ensure the correct option(s) are factually, logically, or mathematically accurate.
13. If unsure about correctness, REGENERATE the question instead of guessing.
14. Avoid ambiguous wording or trick questions.
15. Options must be clearly distinct from one another.

FOR MATH OR NUMERIC QUESTIONS:
• Ensure the problem can be clearly calculated.
• Compute the answer carefully before assigning correctness.
• Make sure the computed answer appears exactly in the options.

FOR FILM, HISTORY, SCIENCE, GEOGRAPHY, OR FACTUAL QUESTIONS:
• Verify facts carefully before marking answers correct.
• Do NOT assume correctness.
• Ensure the marked correct answer is accurate in the real world.
• Only mark an option correct if it is accurate in the real world.

You are responsible for correctness. Incorrect questions are not allowed.

Response format:
{
    "title": "Short Quiz Title",
    "questions": [
        {
            "question_text": "Question here?",
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

        
        user_prompt = f"""CRITICAL REQUIREMENT: Generate EXACTLY {total_questions} quiz questions.

Topic: {prompt}
Difficulty: {difficulty_level}
REQUIRED NUMBER OF QUESTIONS: {total_questions}

Mix of question types:
- 70% RADIO (single correct answer)
- 30% CHECKLIST (multiple correct answers)

Ensure questions are appropriate for {difficulty_level} level.

IMPORTANT VALIDATION BEFORE RESPONDING:
✓ Count the questions in your array
✓ Verify the count equals {total_questions}
✓ Ensure no duplicate questions
✓ Ensure each question has exactly 4 unique options
✓ Ensure each question has at least one correct answer

Generate the quiz now."""

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
            
            # Extract title and questions
            title = data.get("title", "").strip()
            questions = data.get("questions", [])
            
            # Fallback: generate title if not provided
            if not title:
                title = self.generate_quiz_name(prompt)
            
            # Validation
            print(f"[OPENAI_DIRECT] Starting validation of {len(questions)} questions")
            print(f"[OPENAI_DIRECT] Requested: {total_questions}, Received: {len(questions)}")
            
            for idx, q in enumerate(questions):
                if "question_text" not in q or "question_type" not in q or "options" not in q:
                    print(f"[OPENAI_DIRECT] ERROR: Question {idx+1} missing required fields")
                    raise ValueError(f"Invalid question format from OpenAI - question {idx+1} missing required fields")
                
                if q["question_type"] not in ["RADIO", "CHECKLIST"]:
                    print(f"[OPENAI_DIRECT] WARNING: Question {idx+1} invalid type '{q['question_type']}', defaulting to RADIO")
                    q["question_type"] = "RADIO"  # Default fallback
                
                # Ensure at least one correct answer
                has_correct = any(opt.get("is_correct", False) for opt in q["options"])
                if not has_correct:
                    print(f"[OPENAI_DIRECT] WARNING: Question {idx+1} has no correct answer, marking first option as correct")
                    q["options"][0]["is_correct"] = True
            
            # CRITICAL: Check if we received enough questions
            if len(questions) < total_questions:
                error_msg = f"OpenAI returned only {len(questions)} questions but {total_questions} were requested. Please try again or reduce the question count."
                print(f"[OPENAI_DIRECT] ERROR: {error_msg}")
                raise ValueError(error_msg)
            
            # Remove duplicates by question text (case-insensitive)
            seen_questions = set()
            unique_questions = []
            for q in questions:
                q_text_normalized = q.get("question_text", "").strip().lower()
                if q_text_normalized and q_text_normalized not in seen_questions:
                    seen_questions.add(q_text_normalized)
                    unique_questions.append(q)
                else:
                    print(f"[OPENAI_DIRECT] Duplicate question removed: '{q.get('question_text', '')[:80]}'")
            
            print(f"[OPENAI_DIRECT] After deduplication: {len(unique_questions)} unique questions")
            
            # CRITICAL: Ensure we have exactly the requested number after deduplication
            if len(unique_questions) < total_questions:
                error_msg = f"After removing duplicates, only {len(unique_questions)} unique questions remain out of {total_questions} requested. Please try again with a different prompt."
                print(f"[OPENAI_DIRECT] ERROR: {error_msg}")
                raise ValueError(error_msg)
            
            # Return title and EXACTLY the requested number of questions
            final_questions = unique_questions[:total_questions]
            print(f"[OPENAI_DIRECT] Returning exactly {len(final_questions)} unique questions")
            
            return {
                "title": title,
                "questions": final_questions
            }
            
        except Exception as e:
            print(f"OpenAI API Error: {e}")
            raise Exception(f"Failed to generate questions: {str(e)}")
    
    def verify_and_correct_question(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """Verify and correct a single question using a second LLM call"""
        
        system_prompt = """You are a STRICT mathematical and logical validator.

MISSION:
Guarantee that every question has a correct answer that EXISTS in the options.

RULES:

1. Recompute math questions independently if numbers are involved.
2. For film, history, science, geography, or other factual knowledge questions — verify facts carefully before marking answers. Do not assume correctness. Ensure the marked correct answer is factually accurate in the real world.
3. If the correct answer is not present in the options:
   → Modify one option to match the correct value.
4. Never allow zero correct answers.
5. RADIO questions → exactly one correct answer.
6. CHECKLIST questions → at least one correct answer.
7. Fix numeric or logical mistakes.
8. Fix mismatched answer flags.
9. Ensure consistency between question and options.
10. If the question is broken beyond repair, rewrite it fully with valid options.

Return corrected_question ALWAYS.

Response format (ALWAYS include corrected_question):
{
    "is_valid": true/false,
    "corrected_question": {
        "question_text": "Question text (corrected if needed)",
        "question_type": "RADIO" or "CHECKLIST",
        "options": [
            {"option_text": "Option A", "is_correct": true/false},
            {"option_text": "Option B", "is_correct": true/false},
            {"option_text": "Option C", "is_correct": true/false},
            {"option_text": "Option D", "is_correct": true/false}
        ]
    },
    "corrections_made": "Description of what was corrected, or 'No corrections needed'"
}"""

        user_prompt = f"""Verify and correct this quiz question:

Question: {question.get('question_text', '')}
Type: {question.get('question_type', 'RADIO')}
Options:
{chr(10).join([f"{i+1}. {opt.get('option_text', '')} - Marked as: {'CORRECT' if opt.get('is_correct', False) else 'INCORRECT'}" for i, opt in enumerate(question.get('options', []))])}

VERIFICATION STEPS:
1. If this is a math question, solve it step-by-step independently
2. Compare your answer with the marked correct answer(s)
3. Verify all options are mathematically/logically valid
4. Check correct answer count matches question type (RADIO=1, CHECKLIST>=1)
5. Return corrected_question with any fixes needed
6. If question is already correct, return it unchanged in corrected_question field

IMPORTANT: Always return the corrected_question field, even if no changes are needed."""

        try:
            result = self._make_request(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Lower temperature for verification
                response_format={"type": "json_object"}
            )
            
            content = result["choices"][0]["message"]["content"]
            verification = json.loads(content)
            
            # Always use corrected_question if provided, regardless of is_valid flag
            if verification.get("corrected_question"):
                corrected = verification["corrected_question"]
                corrections = verification.get("corrections_made", "Unknown")
                print(f"[VERIFICATION] Question verified. Corrections: {corrections}")
                
                # Ensure corrected question has all required fields
                if "question_text" in corrected and "options" in corrected:
                    # Preserve original question_type if not in corrected
                    if "question_type" not in corrected:
                        corrected["question_type"] = question.get("question_type", "RADIO")
                    return corrected
                else:
                    print(f"[WARNING] Corrected question missing required fields, using original")
                    return question
            else:
                # If no corrected_question provided, check if original is valid
                is_valid = verification.get("is_valid", False)
                if is_valid:
                    print(f"[VERIFICATION] Question verified as correct, no corrections needed")
                    return question
                else:
                    print(f"[WARNING] Question verification marked as invalid but no correction provided, using original")
                    return question
                
        except Exception as e:
            print(f"[WARNING] Verification error: {e}, using original question")
            return question
    
    def verify_and_correct_questions(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Verify and correct all questions using second LLM verification"""
        verified_questions = []
        
        for i, question in enumerate(questions):
            try:
                print(f"[VERIFICATION] Verifying question {i+1}/{len(questions)}")
                corrected_question = self.verify_and_correct_question(question)
                
                # Post-verification validation: Ensure structure is correct
                if "question_text" not in corrected_question or "options" not in corrected_question:
                    print(f"[WARNING] Verified question {i+1} missing required fields, using original")
                    corrected_question = question
                
                # Ensure RADIO questions have exactly one correct answer
                question_type = corrected_question.get("question_type", "RADIO")
                options = corrected_question.get("options", [])
                correct_count = sum(1 for opt in options if opt.get("is_correct", False))
                
                if question_type == "RADIO" and correct_count != 1:
                    print(f"[CORRECTION] RADIO question {i+1} has {correct_count} correct answers, fixing to exactly 1")
                    # Reset all to false, then set first one to true
                    for opt in options:
                        opt["is_correct"] = False
                    if options:
                        options[0]["is_correct"] = True
                
                # Ensure CHECKLIST questions have at least one correct answer
                if question_type == "CHECKLIST" and correct_count == 0:
                    print(f"[CORRECTION] CHECKLIST question {i+1} has no correct answers, fixing")
                    if options:
                        options[0]["is_correct"] = True
                
                verified_questions.append(corrected_question)
            except Exception as e:
                print(f"[ERROR] Failed to verify question {i+1}: {e}, using original")
                verified_questions.append(question)  # Fallback to original
        
        return verified_questions
    
    def _is_math_question(self, question_text: str) -> bool:
        """Detect if a question is a math question"""
        math_indicators = [
            r'\d+\s*[+\-*/]\s*\d+',  # Basic operations: 3 + 4
            r'what is\s+\d+',  # "What is 5 + 3"
            r'calculate',  # "Calculate..."
            r'solve',  # "Solve..."
            r'equals?',  # "equals" or "equal"
            r'=\s*\d+',  # "= 5"
            r'\d+\s*\+\s*\d+',  # Addition
            r'\d+\s*-\s*\d+',  # Subtraction
            r'\d+\s*\*\s*\d+',  # Multiplication
            r'\d+\s*/\s*\d+',  # Division
            r'\d+\s*\^\s*\d+',  # Exponentiation
        ]
        question_lower = question_text.lower()
        return any(re.search(pattern, question_lower, re.IGNORECASE) for pattern in math_indicators)
    
    def _extract_math_expression(self, text: str) -> Optional[str]:
        """Extract math expression from option text"""
        # Remove common prefixes like "A.", "1.", "Answer:", etc.
        text = re.sub(r'^[A-Z]\.\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^\d+\.\s*', '', text)
        text = re.sub(r'^answer:\s*', '', text, flags=re.IGNORECASE)
        text = text.strip()
        
        # Handle pure numbers (e.g., "40", "10.5")
        pure_number_match = re.match(r'^(\d+(?:\.\d+)?)$', text)
        if pure_number_match:
            return pure_number_match.group(1)
        
        # Try to extract pure math expression (e.g., "3 + 4", "10", "5 * 2", "(2 + 3) × 4")
        # Include Unicode symbols × ÷ − in pattern
        math_pattern = r'^([\d\s+\-*/()^×÷−.\s]+)$'
        match = re.match(math_pattern, text)
        if match:
            expr = match.group(1).strip()
            # 🔧 Normalize Unicode math symbols (×, ÷, and Unicode minus −)
            expr = expr.replace('×', '*').replace('÷', '/').replace('−', '-')
            return expr
        
        # Try to extract from text like "3 + 4 = 7" or "Answer: 10"
        equals_match = re.search(r'=\s*([\d\s+\-*/()^×÷−.\s]+)', text)
        if equals_match:
            expr = equals_match.group(1).strip()
            # 🔧 Normalize Unicode math symbols (×, ÷, and Unicode minus −)
            expr = expr.replace('×', '*').replace('÷', '/').replace('−', '-')
            return expr
        
        # Try to extract number at the end
        number_match = re.search(r'([\d\s+\-*/()^×÷−.\s]+)$', text)
        if number_match:
            expr = number_match.group(1).strip()
            # Validate it looks like math
            if re.search(r'[\d+\-*/()^×÷−]', expr):
                # 🔧 Normalize Unicode math symbols (×, ÷, and Unicode minus −)
                expr = expr.replace('×', '*').replace('÷', '/').replace('−', '-')
                return expr
        
        return None
    
    def _safe_eval_math(self, expression: str) -> Optional[float]:
        """Safely evaluate a math expression"""
        try:
            # Clean the expression
            expression = expression.strip()
            
            # Normalize Unicode math symbols
            expression = expression.replace('×', '*').replace('÷', '/').replace('−', '-')
            
            # Convert exponent symbol to Python power operator
            expression = expression.replace('^', '**')
            
            # Remove spaces for cleaner evaluation
            expression = expression.replace(' ', '')
            
            # Remove any non-math characters (keep only digits, operators, parentheses, decimal point)
            expression = re.sub(r'[^\d+\-*/.()]', '', expression)
            
            if not expression:
                return None
            
            # Create a safe namespace for eval (only math functions)
            safe_dict = {
                "__builtins__": {},
                "abs": abs,
                "round": round,
                "min": min,
                "max": max,
                "sum": sum,
                "pow": pow,
                "math": math,
            }
            
            # Evaluate the expression
            result = eval(expression, safe_dict)
            
            # Convert to float if it's a number
            if isinstance(result, (int, float)):
                return float(result)
            
            return None
            
        except Exception as e:
            print(f"[MATH_EVAL] Error evaluating '{expression}': {e}")
            return None
    
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
    
    def generate_hint(self, question_text: str, options: List[str]) -> str:
        """Generate a helpful hint for a quiz question without revealing the answer"""
        
        system_prompt = """You are an educational assistant helping students learn. Your role is to provide helpful hints that guide students toward understanding the concept, WITHOUT revealing the correct answer or eliminating options directly.

CRITICAL RULES:
1. DO NOT mention which option is correct
2. DO NOT say "option A is wrong" or "eliminate option B"
3. DO NOT directly state the answer
4. Focus on:
   - Explaining the underlying concept or method
   - Suggesting how to approach the problem
   - Providing context or background knowledge
5. Keep hints SHORT (2-3 lines maximum)
6. Make hints educational and encouraging

Example good hints:
- "Think about the key principles of [topic] and how they apply here."
- "Consider what happens when [relevant condition] occurs."
- "Recall the relationship between [concept A] and [concept B]."

Example BAD hints (DO NOT DO THIS):
- "The answer is option B"
- "Option A and C are incorrect"
- "Choose the option that says [answer]"
"""
        
        options_text = "\n".join([f"- {opt}" for opt in options])
        
        user_prompt = f"""Question: {question_text}

Options:
{options_text}

Provide a helpful hint (2-3 lines) that guides the student toward solving this question without revealing the correct answer. Focus on the concept or method they should consider."""
        
        try:
            result = self._make_request(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=150  # Limit to keep hints short
            )
            
            hint = result["choices"][0]["message"]["content"].strip()
            # Remove any quotes if LLM wrapped the hint
            hint = hint.strip('"').strip("'")
            return hint if hint else self._get_fallback_hint()
            
        except Exception as e:
            print(f"Hint generation error: {e}")
            return self._get_fallback_hint()
    
    def _get_fallback_hint(self) -> str:
        """Return a generic fallback hint if LLM fails"""
        return "Think carefully about the key concepts related to this question. Consider what you know about the topic and how it applies here."
    
    def generate_question_feedback(
        self,
        question_text: str,
        options: List[str],
        user_answer: str,
        correct_answer: str,
        is_correct: bool
    ) -> str:
        """Generate detailed feedback for a question after submission
        
        This provides educational feedback explaining why the answer was correct or incorrect,
        without directly revealing the answer in the first sentence.
        """
        
        system_prompt = """You are a topic expert providing factual explanations. You must explain the specific concept/topic being tested.

STRICT RULES:
1. NEVER start with: "Your answer is", "The selected option", "This demonstrates", "Review"
2. START IMMEDIATELY with topic-specific facts, definitions, or formulas
3. Every sentence must contain SPECIFIC information about the topic
4. Identify what the question tests and explain THAT topic
5. Maximum 3-4 lines

REQUIRED FORMAT:

If WRONG answer:
Line 1: Why selected answer is wrong (with specific facts)
Line 2: Why correct answer is right (with specific facts)
Line 3: Explain the topic/concept

If CORRECT answer:
Line 1: Why this answer is correct (with specific facts)
Line 2: Explain the topic/concept with details

EXAMPLES:

Wrong (Geography): "New York is a major city but not the capital of the USA. Washington D.C. serves as the capital, established in 1790 as a neutral federal district. It was created to avoid giving any state an advantage by hosting the capital."

Correct (Biology): "DNA replication occurs during the S phase of the cell cycle, before mitosis begins. This ensures each daughter cell receives a complete copy of genetic information. The process involves DNA polymerase enzyme unwinding and copying the double helix."

Wrong (Math): "The area formula for a triangle is ½ × base × height, not base × height. For a triangle with base 6 and height 4, the area is ½ × 6 × 4 = 12 square units. The ½ factor accounts for a triangle being half of a rectangle."

NEVER WRITE:
❌ "Your answer is correct/incorrect"
❌ "The selected option correctly/incorrectly..."
❌ "This demonstrates understanding"
❌ "Review the key concepts"
❌ Any sentence without specific topic facts
"""
        
        user_answer_text = user_answer if user_answer else "No answer provided"
        correct_answer_text = correct_answer if correct_answer else "Unknown"
        
        if is_correct:
            user_prompt = f"""Question: {question_text}

Options:
{chr(10).join([f"- {opt}" for opt in options])}

Student selected: "{user_answer_text}"
STATUS: CORRECT

Generate 2-3 lines explanation:
- Line 1: State the SPECIFIC FACT/CONCEPT that makes this correct (no "your answer is...")
- Line 2: Explain the related topic with specific details
- START directly with factual content

Format: "[Fact about why correct]. [Topic explanation]. [Additional detail]."
"""
        else:
            user_prompt = f"""Question: {question_text}

Options:
{chr(10).join([f"- {opt}" for opt in options])}

Student selected: "{user_answer_text}"
Correct answer: "{correct_answer_text}"
STATUS: INCORRECT

Generate 3-4 lines explanation:
- Line 1: Why selected answer is WRONG (specific facts, not "your answer is...")
- Line 2: Why correct answer is RIGHT (specific facts)
- Line 3: Explain the topic/concept
- START directly with factual content

Format: "[Why selected is wrong]. [Why correct is right]. [Topic explanation]."
"""
        
        try:
            result = self._make_request(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=200  # Limit to keep feedback concise
            )
            
            feedback = result["choices"][0]["message"]["content"].strip()
            # Remove any quotes if LLM wrapped the feedback
            feedback = feedback.strip('"').strip("'")
            return feedback if feedback else self._get_fallback_feedback(is_correct)
            
        except Exception as e:
            print(f"Question feedback generation error: {e}")
            return self._get_fallback_feedback(is_correct)
    
    def _get_fallback_feedback(self, is_correct: bool) -> str:
        """Fallback if LLM fails - minimal generic message"""
        return "Unable to generate explanation. Please review the question and related topic concepts."



