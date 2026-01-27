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
        
        system_prompt = """You are an expert quiz creator and STRICT answer validator.

CRITICAL QUALITY RULES (MANDATORY):

1. EVERY question MUST have at least one correct option.
2. The correct answer MUST exist EXACTLY in the options list.
3. NEVER create a question where the answer is missing from options.
4. NEVER leave all options marked as false.
5. For RADIO type → EXACTLY ONE correct answer.
6. For CHECKLIST type → ONE OR MORE correct answers.

MATH QUESTION RULES (VERY IMPORTANT):
7. If the question involves numbers, equations, arithmetic, logic, or calculations:
   - Solve the problem step-by-step internally.
   - Compute the FINAL answer.
   - Ensure that computed answer EXISTS in the options.
   - Mark ONLY the mathematically correct option(s) as true.
8. NEVER guess math answers.
9. NEVER create trick math questions with ambiguous answers.
10. All numeric options must be mathematically valid values.

🔴 ABSOLUTE MATH GENERATION RULES (NON-NEGOTIABLE - STRICTLY ENFORCED):

For ANY math question, you MUST follow these STRICT rules:

✅ POSITIVE NUMBERS ONLY (MANDATORY):
- Use ONLY positive whole numbers from 1 to 100
- EVERY number in the question MUST be positive
- The FINAL ANSWER must also be POSITIVE
- NO negative numbers ANYWHERE (not in question, not in answer)

✅ SINGLE OPERATION ONLY:
- The question must contain EXACTLY ONE arithmetic operation
- Use ONLY one of these operations:
  • Addition: "What is 15 + 7?" → Result: 22 (positive ✓)
  • Subtraction: "What is 20 − 5?" → Result: 15 (positive ✓)
  • Multiplication: "What is 6 × 4?" → Result: 24 (positive ✓)
  • Division: "What is 18 ÷ 3?" → Result: 6 (positive ✓)

✅ VALID QUESTION FORMATS:
- "What is A + B?" (where A, B are positive integers 1-100, result is positive)
- "What is A − B?" (where A > B, both positive integers 1-100, result is POSITIVE)
- "What is A × B?" (where A, B are positive integers 1-100, result is positive)
- "What is A ÷ B?" (where A, B are positive integers 1-100, A divisible by B, result is positive)

🔵 CRITICAL SUBTRACTION RULE:
- For "What is A − B?": A MUST BE GREATER THAN B
- This ensures the result is ALWAYS POSITIVE
- Examples: "What is 20 − 5?" ✓ (result: 15), "What is 5 − 20?" ❌ (result: -15)

✅ ALLOWED EXAMPLES:
- "What is 36 ÷ 6?"  ✓ (result: 6, positive)
- "What is 12 + 8?"  ✓ (result: 20, positive)
- "What is 15 × 3?"  ✓ (result: 45, positive)
- "What is 50 − 12?" ✓ (result: 38, positive)
- "What is 18 − 5?"  ✓ (result: 13, positive)

❌ ABSOLUTELY FORBIDDEN (DO NOT CREATE):
- More than one operator: "36 ÷ 6 + 8" ❌
- Brackets/parentheses: "(5 + 3) × 2" ❌
- Order of operations: "8 + 5 × 2" ❌
- Mixed operators: "10 + 5 − 3" ❌
- Chains of operations: "5 + 3 + 2" ❌
- Negative numbers: "(-2) + 5", "-10", "What is -18 + 7?" ❌
- Subtraction with negative result: "What is 5 − 20?" ❌ (result: -15)
- Negative expressions: "-2 × -7", "(-3) × 4" ❌
- Exponentiation: "5^2", "2^3" ❌
- Decimals: "3.5 + 2.1", "10.5" ❌
- Fractions: "1/2", "3/4" ❌
- Variables: "x + 5", "2y" ❌
- Word problems: "A train travels..." ❌

🔁 VALIDATION BEFORE RETURN (MANDATORY):
11. Before returning the quiz, CHECK EACH MATH QUESTION:
    - Does it have more than one operator? → REGENERATE
    - Does it contain negative numbers? → REGENERATE
    - For subtraction, is A > B? → If not, REGENERATE
    - Is the result positive? → If not, REGENERATE
12. Keep ALL math questions to simple single-step arithmetic with POSITIVE RESULTS ONLY.

SAFETY RULE:
11. If unsure about correctness, REGENERATE the question instead of risking wrong answer.

CONTENT RULES:
12. Questions must be clear and unambiguous.
13. No duplicate questions.
14. Keep questions medium length.
15. Return ONLY valid JSON.

You are responsible for correctness. Wrong answers are unacceptable.

Response format:
{
    "title": "Short Quiz Title",
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
        
        user_prompt = f"""CRITICAL REQUIREMENT: Generate EXACTLY {total_questions} quiz questions. Count them before responding!

Topic: {prompt}
Difficulty: {difficulty_level}
REQUIRED NUMBER OF QUESTIONS: {total_questions} (THIS IS MANDATORY - NOT {total_questions-1}, NOT {total_questions+1}, EXACTLY {total_questions})

🔴 CRITICAL MATH VALIDATION (NON-NEGOTIABLE):
For math questions, use ONLY SINGLE-OPERATION expressions with POSITIVE RESULTS:
- EXACTLY ONE operation per question: A + B, A − B, A × B, or A ÷ B
- ALL numbers MUST be POSITIVE (1-100)
- RESULT must be POSITIVE (no negative answers)
- For subtraction: A MUST BE GREATER THAN B (ensures positive result)
- Format: "What is [number] [operator] [number]?"
- ✅ ALLOWED: "What is 36 ÷ 6?" (=6), "What is 20 − 5?" (=15), "What is 12 + 8?" (=20)
- ❌ FORBIDDEN: "What is 5 − 20?" (=-15), "What is -18 + 7?" (-18 is negative), "36 ÷ 6 + 8" (multiple ops), brackets, negative numbers

Mix of question types:
- 70% RADIO (single correct answer)
- 30% CHECKLIST (multiple correct answers)

Ensure questions are appropriate for {difficulty_level} difficulty level.

IMPORTANT VALIDATION BEFORE RESPONDING:
✓ Count the questions in your array
✓ Verify the count equals {total_questions}
✓ If count is wrong, add or remove questions to match exactly {total_questions}
✓ Ensure no duplicate questions
✓ Ensure each question has exactly 4 unique options

Generate EXACTLY {total_questions} questions now."""

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
            
            # FINAL SAFETY LAYER — MATH OVERRIDE
            print("[FINAL CHECK] Running math answer override...")
            final_questions = self.evaluate_and_override_math_answers(final_questions)
            
            # ABSOLUTE SAFETY CHECK
            for i, q in enumerate(final_questions):
                correct_count = sum(1 for opt in q.get("options", []) if opt.get("is_correct", False))
                if correct_count == 0:
                    print(f"[CRITICAL FIX] Question {i+1} had no correct answer. Forcing first option as correct.")
                    if q.get("options"):
                        q["options"][0]["is_correct"] = True
            
            # 🔍 DEBUG LOGGING - Verify correct flags before saving
            print("\n[DEBUG] Final Questions Before Save:")
            for i, q in enumerate(final_questions):
                print(f"Q{i+1}: {q['question_text']}")
                for opt in q.get("options", []):
                    print(f"   Option: {opt['option_text']} | is_correct={opt['is_correct']}")
            
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

CRITICAL MISSION:
You must guarantee that EVERY question has a correct answer that EXISTS in the options.

RULES:

1. ALWAYS recompute math questions independently.
2. If the correct answer is not present in options:
   → MODIFY one option to match the correct value.
3. NEVER allow zero correct answers.
4. NEVER allow multiple correct answers in RADIO questions.
5. CHECKLIST must have ≥1 correct answers.
6. Fix all numeric mistakes.
7. Fix mismatched answer flags.
8. Remove impossible numeric values.
9. Ensure logical consistency.
10. If question cannot be corrected → rewrite the question completely with valid options.

🔴 MATH QUESTION VALIDATION (MANDATORY - STRICTLY ENFORCED):
11. If the question contains ANY of these forbidden elements, you MUST rewrite it completely:
    ❌ MORE THAN ONE OPERATION: "36 ÷ 6 + 8", "8 + 5 × 2", "10 + 5 − 3"
    ❌ BRACKETS/PARENTHESES: "(5 + 3) × 2", "(10 − 4) ÷ 2"
    ❌ ORDER OF OPERATIONS: "8 + 5 × 2" (requires precedence rules)
    ❌ CHAINED OPERATIONS: "5 + 3 + 2", "10 − 5 − 2"
    ❌ NEGATIVE NUMBERS: (-2), -5, "What is -18 + 7?", negative expressions, "What is -2 × -7?"
    ❌ NEGATIVE RESULTS: "What is 5 − 20?" (result: -15), subtraction where A < B
    ❌ Exponents/Powers: 5^2, 2^3, 10^2
    ❌ Variables/Algebra: x, y, "Solve for x", equations
    ❌ Decimals: 3.5, 2.1, 0.75
    ❌ Fractions: 1/2, 3/4
    ❌ Word problems with hidden math
12. Rewritten math questions MUST use ONLY SINGLE OPERATIONS WITH POSITIVE RESULTS:
    ✅ Format: "What is A + B?" where A, B are positive integers 1-100
    ✅ For subtraction: "What is A − B?" where A > B (ensures positive result)
    ✅ EXACTLY ONE operator: +, −, ×, or ÷
    ✅ ALL numbers must be POSITIVE (1-100)
    ✅ RESULT must be POSITIVE
    ✅ Valid examples: "What is 36 ÷ 6?" (=6), "What is 20 − 5?" (=15), "What is 12 + 8?" (=20)
    ✅ NO brackets, NO multiple operations, NO negative numbers, NO negative results

ABSOLUTE RULE:
Return corrected_question that ALWAYS contains valid correct answer(s).
Returning a question with no correct answer is FORBIDDEN.

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
        
        # FINAL SAFETY LAYER — MATH OVERRIDE AFTER VERIFICATION
        print("[FINAL CHECK] Running math override after verification...")
        verified_questions = self.evaluate_and_override_math_answers(verified_questions)
        
        # ABSOLUTE SAFETY CHECK - Ensure no question has zero correct answers
        for i, q in enumerate(verified_questions):
            correct_count = sum(1 for opt in q.get("options", []) if opt.get("is_correct", False))
            if correct_count == 0:
                print(f"[CRITICAL FIX] Question {i+1} had no correct answer after verification. Forcing first option as correct.")
                if q.get("options"):
                    q["options"][0]["is_correct"] = True
        
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
    
    def _extract_target_value(self, question_text: str) -> Optional[float]:
        """Extract target value from questions like 'which equal 10' or 'select all that equal 5'"""
        # Pattern: "equal 10", "equals 10", "equal to 10", "= 10"
        patterns = [
            r'equal(?:s| to)?\s+(\d+(?:\.\d+)?)',
            r'=\s*(\d+(?:\.\d+)?)',
            r'which.*?(\d+(?:\.\d+)?)',
            r'select.*?(\d+(?:\.\d+)?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, question_text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        
        return None
    
    def _compute_question_answer(self, question_text: str) -> Optional[float]:
        """Compute the correct answer for a math question"""
        # First, check if question asks "which equal X" (for CHECKLIST)
        target_value = self._extract_target_value(question_text)
        if target_value is not None:
            return target_value
        
        # Extract math expression from question
        # Look for patterns like "What is 3 + 4?" or "Calculate 5 * 2"
        
        # Try to find expression in question
        expr = self._extract_math_expression(question_text)
        if expr:
            return self._safe_eval_math(expr)
        
        # Try to find "What is X?" pattern (include Unicode × ÷ − symbols)
        what_is_match = re.search(r'what is\s+([\d\s+\-*/()^×÷−.\s]+)', question_text, re.IGNORECASE)
        if what_is_match:
            expr = what_is_match.group(1).strip()
            return self._safe_eval_math(expr)
        
        # Try to find "Calculate X" pattern (include Unicode × ÷ − symbols)
        calc_match = re.search(r'calculate\s+([\d\s+\-*/()^×÷−.\s]+)', question_text, re.IGNORECASE)
        if calc_match:
            expr = calc_match.group(1).strip()
            return self._safe_eval_math(expr)
        
        # Try to find "X = ?" pattern (include Unicode × ÷ − symbols)
        equals_q_match = re.search(r'([\d\s+\-*/()^×÷−.\s]+)\s*=\s*\?', question_text, re.IGNORECASE)
        if equals_q_match:
            expr = equals_q_match.group(1).strip()
            return self._safe_eval_math(expr)
        
        return None
    
    def _evaluate_math_question(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate math question and override correct answers based on computation"""
        question_text = question.get("question_text", "")
        options = question.get("options", [])
        question_type = question.get("question_type", "RADIO")
        
        # 🔹 STEP 1 — Skip algebra / variable-based questions
        # Only process pure arithmetic questions (no variables like x, y, z)
        # Check for mathematical variables: single letters in equations, "solve for x", "find x", etc.
        algebra_patterns = [
            r'\b[a-z]\s*[=+\-*/()]',  # Single letter followed by math operators: "x =", "x +", "x -", "x(", etc.
            r'[=+\-*/()]\s*\b[a-z]\b',  # Math operators followed by single letter: "= x", "+ y", "- z", "(x", etc.
            r'\d+\s*[a-z]\b',  # Number followed by letter (no space): "3x", "2y", "5z"
            r'solve\s+for\s+[a-z]',  # "solve for x"
            r'find\s+[a-z]',  # "find x"
            r'\b[a-z]\s*[-+]?\s*\d',  # Letter followed by number: "x - 5", "y + 3"
        ]
        if any(re.search(pattern, question_text.lower()) for pattern in algebra_patterns):
            print(f"[MATH_EVAL] Algebra detected in '{question_text[:60]}...' — skipping arithmetic override")
            return question
        
        # 🔹 STEP 2 — Compute the correct answer (arithmetic only)
        correct_answer = self._compute_question_answer(question_text)
        
        if correct_answer is None:
            print(f"[MATH_EVAL] Could not compute arithmetic answer — skipping override")
            return question
        
        print(f"[MATH_EVAL] Computed correct answer: {correct_answer}")
        
        # Evaluate each option and determine which are correct
        option_values = []
        for i, option in enumerate(options):
            option_text = option.get("option_text", "")
            expr = self._extract_math_expression(option_text)
            
            if expr:
                value = self._safe_eval_math(expr)
                option_values.append((i, value, option))
                print(f"[MATH_EVAL] Option {i+1} '{option_text}' -> {value}")
            else:
                # If we can't extract math, keep original is_correct flag
                option_values.append((i, None, option))
                print(f"[MATH_EVAL] Option {i+1} '{option_text}' -> Could not extract math")
        
        # Determine correct options based on computed values
        # For RADIO: exactly one option matching correct_answer
        # For CHECKLIST: all options matching correct_answer
        
        # Reset all is_correct flags
        for _, _, option in option_values:
            option["is_correct"] = False
        
        # Find options that match the correct answer (with tolerance for floating point)
        correct_options = []
        for i, value, option in option_values:
            if value is not None:
                # Use small tolerance for floating point comparison
                if abs(value - correct_answer) < 0.0001:
                    correct_options.append((i, option))
        
        if not correct_options:
            print(f"[MATH_EVAL] WARNING: No options match computed answer {correct_answer}, using first option")
            if options:
                options[0]["is_correct"] = True
        elif question_type == "RADIO":
            # RADIO: exactly one correct answer
            if len(correct_options) == 1:
                correct_options[0][1]["is_correct"] = True
                print(f"[MATH_EVAL] RADIO: Marked option {correct_options[0][0]+1} as correct")
            else:
                # Multiple options match - use first one
                print(f"[MATH_EVAL] RADIO: Multiple options match, using first: {len(correct_options)} options")
                correct_options[0][1]["is_correct"] = True
        elif question_type == "CHECKLIST":
            # CHECKLIST: mark all matching options as correct
            for _, option in correct_options:
                option["is_correct"] = True
            print(f"[MATH_EVAL] CHECKLIST: Marked {len(correct_options)} options as correct")
        
        return question
    
    def evaluate_and_override_math_answers(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Evaluate math questions and override LLM-provided correct answers"""
        corrected_questions = []
        
        for i, question in enumerate(questions):
            question_text = question.get("question_text", "")
            
            # Check if this is a math question
            if self._is_math_question(question_text):
                print(f"[MATH_EVAL] Processing math question {i+1}: {question_text[:50]}...")
                corrected_question = self._evaluate_math_question(question)
                corrected_questions.append(corrected_question)
            else:
                # Not a math question, keep as-is
                corrected_questions.append(question)
        
        return corrected_questions
    
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



