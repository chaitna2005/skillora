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
        
        system_prompt = """You are an expert quiz creator. Generate clear, educational quiz questions based on the given topic.

Rules:
1. Create questions that match the specified difficulty level
2. Each question should have 4 options
3. For RADIO type: exactly ONE correct answer
4. For CHECKLIST type: one or MORE correct answers
5. Questions should be unambiguous and educational
6. Generate a short, relevant quiz title (max 5 words)
7. Return ONLY valid JSON, no additional text

CRITICAL RULES FOR PREFIX/INFIX/POSTFIX EXPRESSIONS:
- For Prefix → Infix conversion questions:
  * Input MUST be a VALID prefix (Polish) notation expression
  * Prefix expressions MUST start with an operator (+, -, *, /)
  * Every operator MUST have exactly two operands
  * Format: operator operand1 operand2 (e.g., "+ 3 4", "* + 2 3 4")
  * NEVER use infix expressions as input (e.g., "3 + 4" is WRONG for prefix input)
  * NEVER use invalid or incomplete prefix expressions
  * The correct answer must be the EXACT infix conversion (e.g., "(3 + 4)" or "3 + 4")
  
- For Infix → Prefix conversion questions:
  * Input MUST be a VALID infix expression
  * Output must be valid prefix notation
  
- For Postfix → Infix conversion questions:
  * Input MUST be a VALID postfix (Reverse Polish) notation expression
  * Postfix expressions MUST end with an operator
  * Format: operand1 operand2 operator (e.g., "3 4 +", "2 3 + 4 *")
  
- Expression validation:
  * Operators: +, -, *, /, ^
  * Operands: numbers or variables
  * Every operator must have exactly 2 operands
  * Expressions must be complete and syntactically valid

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
            
            # Extract title and questions
            title = data.get("title", "").strip()
            questions = data.get("questions", [])
            
            # Fallback: generate title if not provided
            if not title:
                title = self.generate_quiz_name(prompt)
            
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
            
            # Return title and questions
            return {
                "title": title,
                "questions": questions[:total_questions]  # Ensure we return exact number
            }
            
        except Exception as e:
            print(f"OpenAI API Error: {e}")
            raise Exception(f"Failed to generate questions: {str(e)}")
    
    def verify_and_correct_question(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """Verify and correct a single question using a second LLM call"""
        
        system_prompt = """You are a strict quality verifier for quiz questions. Your job is to verify and correct quiz questions, especially math questions.

CRITICAL RULES:
1. For math questions: ALWAYS independently solve the problem step-by-step and verify the correct answer
2. Check if the marked correct answer is ACTUALLY mathematically/logically correct
3. Verify all options are mathematically/logically valid (no impossible values)
4. For RADIO type: Ensure exactly ONE correct answer exists (if multiple marked, fix to one)
5. For CHECKLIST type: Ensure ALL correct answers are marked (none missing)
6. Fix any errors you find - correct wrong answers, fix invalid options, regenerate if needed
7. ALWAYS return corrected_question field, even if no corrections are needed (return original)
8. Return ONLY valid JSON, no additional text

MATH VERIFICATION PROCESS:
- Read the question carefully
- Solve the problem independently
- Compare your answer with the marked correct answer
- If they don't match, correct the is_correct flags
- Verify all other options are valid

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
        
        # Try to extract pure math expression (e.g., "3 + 4", "10", "5 * 2")
        # Match patterns like: number operator number, or just a number
        math_pattern = r'^([\d\s+\-*/()^.\s]+)$'
        match = re.match(math_pattern, text)
        if match:
            return match.group(1).strip()
        
        # Try to extract from text like "3 + 4 = 7" or "Answer: 10"
        equals_match = re.search(r'=\s*([\d\s+\-*/()^.\s]+)', text)
        if equals_match:
            return equals_match.group(1).strip()
        
        # Try to extract number at the end
        number_match = re.search(r'([\d\s+\-*/()^.\s]+)$', text)
        if number_match:
            expr = number_match.group(1).strip()
            # Validate it looks like math
            if re.search(r'[\d+\-*/()^]', expr):
                return expr
        
        return None
    
    def _safe_eval_math(self, expression: str) -> Optional[float]:
        """Safely evaluate a math expression"""
        try:
            # Clean the expression
            expression = expression.strip()
            
            # Replace common math symbols
            expression = expression.replace('×', '*').replace('÷', '/')
            expression = expression.replace('^', '**')
            
            # Remove any non-math characters (keep only digits, operators, parentheses, decimal point)
            expression = re.sub(r'[^\d+\-*/()^.\s]', '', expression)
            expression = expression.strip()
            
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
        
        # Try to find "What is X?" pattern
        what_is_match = re.search(r'what is\s+([\d\s+\-*/()^.\s]+)', question_text, re.IGNORECASE)
        if what_is_match:
            expr = what_is_match.group(1).strip()
            return self._safe_eval_math(expr)
        
        # Try to find "Calculate X" pattern
        calc_match = re.search(r'calculate\s+([\d\s+\-*/()^.\s]+)', question_text, re.IGNORECASE)
        if calc_match:
            expr = calc_match.group(1).strip()
            return self._safe_eval_math(expr)
        
        # Try to find "X = ?" pattern
        equals_q_match = re.search(r'([\d\s+\-*/()^.\s]+)\s*=\s*\?', question_text, re.IGNORECASE)
        if equals_q_match:
            expr = equals_q_match.group(1).strip()
            return self._safe_eval_math(expr)
        
        return None
    
    def _evaluate_math_question(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate math question and override correct answers based on computation"""
        question_text = question.get("question_text", "")
        options = question.get("options", [])
        question_type = question.get("question_type", "RADIO")
        
        # Compute the correct answer from the question
        correct_answer = self._compute_question_answer(question_text)
        
        if correct_answer is None:
            print(f"[MATH_EVAL] Could not compute answer for question, skipping override")
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



