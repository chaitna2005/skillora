"""
Quiz Service
Business logic for quiz creation and management
"""
import re
import math
from typing import Dict, Any, List, Optional, Set, Tuple
from psycopg2.extras import RealDictCursor
from app.models.quiz import QuizModel
from app.models.question import QuestionModel
from app.models.prompt import ExamplePromptModel
from app.services.openai_service_direct import OpenAIService
from app.services.test_service import TestService


class QuizService:
    
    def __init__(self):
        self.openai_service = OpenAIService()
    
    def create_quiz_with_questions(
        self,
        cursor: RealDictCursor,
        user_id: int,
        prompt: str,
        difficulty_level: str,
        total_no_questions: int
    ) -> Dict[str, Any]:
        """
        Create a complete quiz with AI-generated questions
        
        Steps:
        1. Generate questions and title using OpenAI
        2. Create quiz record with generated title
        3. Save questions and options to database
        """
        
        # Step 1: Generate questions and title using OpenAI
        result = self.openai_service.generate_quiz_questions(
            prompt=prompt,
            difficulty_level=difficulty_level,
            total_questions=total_no_questions
        )
        
        quiz_name = result.get("title", "")
        questions = result.get("questions", [])
        
        # Fallback: generate title if not provided
        if not quiz_name:
            quiz_name = self.openai_service.generate_quiz_name(prompt)
        
        # CRITICAL: Verify we received exactly the requested number of questions
        print(f"[QUIZ_SERVICE] Received {len(questions)} questions from OpenAI service")
        print(f"[QUIZ_SERVICE] Expected {total_no_questions} questions")
        
        if len(questions) < total_no_questions:
            error_msg = f"Expected {total_no_questions} questions but only received {len(questions)}. Please try again."
            print(f"[QUIZ_SERVICE] ERROR: {error_msg}")
            raise ValueError(error_msg)
        
        # Use exactly the requested number (should already be exact from service)
        questions = questions[:total_no_questions]
        print(f"[QUIZ_SERVICE] Using exactly {len(questions)} questions for quiz creation")
        
        # Step 2: Create quiz
        quiz_data = {
            "user_id": user_id,
            "prompt": prompt,
            "total_no_questions": total_no_questions,
            "difficulty_level": difficulty_level,
            "quiz_name": quiz_name
        }
        
        quiz = QuizModel.create_quiz(cursor, quiz_data)
        quiz_id = quiz["quiz_id"]
        
        # Step 2.5: Save prompt to Example_Prompt with 10-prompt limit per user (FIFO)
        # Hook: Save prompt for CREATIVE quizzes (all quizzes are CREATIVE)
        # Conditions: prompt length > 20
        # This must NOT block quiz creation
        try:
            if len(prompt) > 20:
                # Check if this exact prompt already exists for this user
                existing_prompt = ExamplePromptModel.get_user_prompt_by_text(cursor, prompt, user_id)
                
                if existing_prompt:
                    # Duplicate: Update timestamp to move to top
                    ExamplePromptModel.update_prompt_timestamp(cursor, existing_prompt['prompt_id'])
                else:
                    # New prompt: Check if user has 10 or more prompts
                    prompt_count = ExamplePromptModel.get_user_prompt_count(cursor, user_id)
                    if prompt_count >= 10:
                        # Delete oldest prompt (FIFO)
                        ExamplePromptModel.delete_oldest_user_prompt(cursor, user_id)
                    
                    # Create new prompt
                    ExamplePromptModel.create_prompt(cursor, {
                        "prompt_text": prompt,
                        "created_by": user_id
                    })
        except Exception as e:
            # Do not block quiz creation if prompt saving fails
            print(f"[WARNING] Failed to save prompt to Example_Prompt: {e}")
        
        # Step 3: Save questions and options (trust AI-generated content)
        for question_data in questions:
            question_text = question_data.get("question_text", "")
            question_type = question_data.get("question_type", "RADIO")
            options = question_data.get("options", [])
            
            # Create question
            question = QuestionModel.create_question(cursor, {
                "quiz_id": quiz_id,
                "question_text": question_data["question_text"],
                "question_type": question_data["question_type"]
            })
            
            question_id = question["question_id"]
            
            # Create options with validated is_correct flags
            for option_data in options:
                QuestionModel.create_question_option(cursor, {
                    "question_id": question_id,
                    "option_text": option_data["option_text"],
                    "is_correct": option_data["is_correct"]
                })
        
        # Return complete quiz with questions
        return QuestionModel.get_quiz_with_questions(cursor, quiz_id)
    
    def _validate_questions(self, questions: List[Dict[str, Any]], required_count: int) -> List[Dict[str, Any]]:
        """
        Strictly validate questions before saving.
        Rejects invalid questions that cannot have correct answers.
        """
        valid_questions = []
        
        for i, question in enumerate(questions):
            try:
                # Basic structure validation
                if not question.get("question_text") or not question.get("options"):
                    print(f"[VALIDATION] Question {i+1} rejected: Missing question_text or options")
                    continue
                
                question_text = question.get("question_text", "").strip()
                question_type = question.get("question_type", "RADIO")
                options = question.get("options", [])
                
                if not question_text:
                    print(f"[VALIDATION] Question {i+1} rejected: Empty question_text")
                    continue
                
                if len(options) < 2:
                    print(f"[VALIDATION] Question {i+1} rejected: Less than 2 options")
                    continue
                
                # Validate question type
                if question_type not in ["RADIO", "CHECKLIST"]:
                    print(f"[VALIDATION] Question {i+1} rejected: Invalid question_type '{question_type}'")
                    continue
                
                # CRITICAL: For math questions, validate correctness using backend computation
                if TestService._is_math_question(question_text):
                    is_valid, corrected_question = self._validate_math_question(question)
                    if not is_valid:
                        print(f"[VALIDATION] Question {i+1} rejected: Invalid math question - cannot compute correct answer")
                        continue
                    if corrected_question is None:
                        print(f"[VALIDATION] Question {i+1} rejected: Math question validation returned None")
                        continue
                    question = corrected_question  # Use corrected version with backend-computed answers
                
                # CRITICAL: Validate expression syntax for prefix/infix/postfix questions
                if self._is_expression_question(question_text):
                    is_valid_expr, corrected_expr_question = self._validate_expression_question(question)
                    if not is_valid_expr:
                        print(f"[VALIDATION] Question {i+1} rejected: Invalid expression syntax or conversion")
                        continue
                    if corrected_expr_question is not None:
                        question = corrected_expr_question  # Use corrected version
                
                # Ensure at least one correct answer exists (after all corrections)
                correct_count = sum(1 for opt in question.get("options", []) if opt.get("is_correct", False))
                if correct_count == 0:
                    print(f"[VALIDATION] Question {i+1} rejected: No correct answers after validation")
                    continue
                
                # For RADIO, ensure exactly one correct answer
                if question_type == "RADIO" and correct_count != 1:
                    print(f"[VALIDATION] Question {i+1} rejected: RADIO question has {correct_count} correct answers (must be 1)")
                    continue
                
                # All validations passed
                valid_questions.append(question)
                print(f"[VALIDATION] Question {i+1} validated: '{question_text[:50]}...'")
                
            except Exception as e:
                print(f"[VALIDATION] Question {i+1} validation error: {e}")
                continue
        
        return valid_questions
    
    def _validate_math_question(self, question: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Validate math question by recomputing correct answer.
        Returns (is_valid, corrected_question or None)
        """
        question_text = question.get("question_text", "")
        question_type = question.get("question_type", "RADIO")
        options = question.get("options", [])
        
        # Compute correct answer using backend (NOT trusting LLM)
        correct_answer = TestService._compute_correct_answer(question_text, question_type)
        
        if correct_answer is None:
            print(f"[VALIDATION] Cannot compute answer for math question: '{question_text[:50]}...'")
            return False, None
        
        # Evaluate each option and determine correct ones
        correct_option_indices = []
        option_values = []
        
        for i, option in enumerate(options):
            option_text = option.get("option_text", "")
            option_value = TestService._extract_math_value(option_text)
            option_values.append((i, option_value))
            
            if option_value is not None:
                # Compare with tolerance for floating point
                if abs(option_value - correct_answer) < 0.0001:
                    correct_option_indices.append(i)
        
        # Must have at least one option matching computed answer
        if not correct_option_indices:
            print(f"[VALIDATION] No options match computed answer {correct_answer} for question: '{question_text[:50]}...'")
            return False, None
        
        # Create corrected question with proper is_correct flags
        corrected_question = question.copy()
        corrected_options = []
        
        for i, option in enumerate(options):
            corrected_option = option.copy()
            corrected_option["is_correct"] = i in correct_option_indices
            corrected_options.append(corrected_option)
        
        corrected_question["options"] = corrected_options
        
        # For RADIO, ensure exactly one correct answer
        if question_type == "RADIO" and len(correct_option_indices) > 1:
            # Keep only the first matching option as correct
            corrected_question["options"][correct_option_indices[0]]["is_correct"] = True
            for idx in correct_option_indices[1:]:
                corrected_question["options"][idx]["is_correct"] = False
        
        return True, corrected_question
    
    def _is_expression_question(self, question_text: str) -> bool:
        """Check if question is about prefix/infix/postfix expressions"""
        expression_keywords = [
            r'prefix\s+notation',
            r'infix\s+notation',
            r'postfix\s+notation',
            r'polish\s+notation',
            r'reverse\s+polish',
            r'evaluate\s+expression',
            r'expression\s+tree',
        ]
        question_lower = question_text.lower()
        return any(re.search(pattern, question_lower, re.IGNORECASE) for pattern in expression_keywords)
    
    def _validate_expression_question(self, question: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Validate prefix/infix/postfix expression questions.
        Returns (is_valid, corrected_question or None)
        """
        question_text = question.get("question_text", "").lower()
        options = question.get("options", [])
        
        # Check if it's a prefix → infix conversion question
        is_prefix_to_infix = 'prefix' in question_text and 'infix' in question_text and 'convert' in question_text
        
        if is_prefix_to_infix:
            return self._validate_prefix_to_infix_question(question)
        
        # Check if it's an infix → prefix conversion question
        is_infix_to_prefix = 'infix' in question_text and 'prefix' in question_text and 'convert' in question_text
        
        if is_infix_to_prefix:
            return self._validate_infix_to_prefix_question(question)
        
        # Check if it's a postfix → infix conversion question
        is_postfix_to_infix = ('postfix' in question_text or 'reverse polish' in question_text) and 'infix' in question_text
        
        if is_postfix_to_infix:
            return self._validate_postfix_to_infix_question(question)
        
        # For other expression questions, basic validation
        return self._validate_expression_syntax_basic(question_text, options)
    
    def _validate_prefix_to_infix_question(self, question: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Validate Prefix → Infix conversion question"""
        question_text = question.get("question_text", "")
        options = question.get("options", [])
        
        # Extract prefix expression from question text
        # Pattern: "Convert prefix expression + 3 4 to infix" or "What is the infix form of + 3 4?"
        prefix_expr = None
        
        # Try to find prefix expression in question text
        # Pattern 1: "prefix expression X" or "prefix notation X" or "prefix X"
        prefix_match = re.search(r'prefix\s+(?:expression|notation)?\s*([+\-*/]\s+[\d\s+\-*/()a-zA-Z]+)', question_text, re.IGNORECASE)
        if prefix_match:
            candidate = prefix_match.group(1).strip()
            if self._is_valid_prefix_expression(candidate):
                prefix_expr = candidate
        
        # Pattern 2: "Convert X to infix" where X starts with operator
        if not prefix_expr:
            convert_match = re.search(r'convert\s+([+\-*/]\s+[\d\s+\-*/()a-zA-Z]+)\s+to\s+infix', question_text, re.IGNORECASE)
            if convert_match:
                candidate = convert_match.group(1).strip()
                if self._is_valid_prefix_expression(candidate):
                    prefix_expr = candidate
        
        # Pattern 3: "infix form of X" or "infix equivalent of X"
        if not prefix_expr:
            infix_form_match = re.search(r'infix\s+(?:form|equivalent)\s+of\s+([+\-*/]\s+[\d\s+\-*/()a-zA-Z]+)', question_text, re.IGNORECASE)
            if infix_form_match:
                candidate = infix_form_match.group(1).strip()
                if self._is_valid_prefix_expression(candidate):
                    prefix_expr = candidate
        
        # Pattern 4: Expression in quotes or parentheses that starts with operator
        if not prefix_expr:
            quoted_match = re.search(r'["\']([+\-*/]\s+[\d\s+\-*/()a-zA-Z]+)["\']', question_text)
            if quoted_match:
                candidate = quoted_match.group(1).strip()
                if self._is_valid_prefix_expression(candidate):
                    prefix_expr = candidate
        
        # Pattern 5: Direct prefix expression (starts with operator, not infix pattern)
        if not prefix_expr:
            # Find all potential expressions starting with operators
            potential_exprs = re.findall(r'([+\-*/]\s+[\d\s+\-*/()a-zA-Z]+)', question_text)
            for candidate in potential_exprs:
                candidate = candidate.strip()
                if self._is_valid_prefix_expression(candidate) and not self._is_infix_expression(candidate):
                    prefix_expr = candidate
                    break
        
        if not prefix_expr:
            print(f"[VALIDATION] Could not extract prefix expression from: '{question_text}'")
            return False, None
        
        # Validate prefix expression syntax
        if not self._is_valid_prefix_expression(prefix_expr):
            print(f"[VALIDATION] Invalid prefix expression: '{prefix_expr}'")
            return False, None
        
        # Check if prefix expression is actually infix (common error)
        if self._is_infix_expression(prefix_expr):
            print(f"[VALIDATION] Prefix expression is actually infix: '{prefix_expr}'")
            return False, None
        
        # Compute correct infix conversion
        correct_infix = self._prefix_to_infix(prefix_expr)
        if not correct_infix:
            print(f"[VALIDATION] Cannot convert prefix to infix: '{prefix_expr}'")
            return False, None
        
        # Validate that at least one option matches correct infix
        correct_option_found = False
        corrected_options = []
        
        for option in options:
            option_text = option.get("option_text", "").strip()
            corrected_option = option.copy()
            
            # Check if option matches correct infix (accounting for parentheses variations)
            if self._infix_expressions_equivalent(option_text, correct_infix):
                corrected_option["is_correct"] = True
                correct_option_found = True
                print(f"[VALIDATION] Option '{option_text}' matches correct infix '{correct_infix}'")
            else:
                corrected_option["is_correct"] = False
            
            corrected_options.append(corrected_option)
        
        if not correct_option_found:
            print(f"[VALIDATION] No option matches correct infix '{correct_infix}' for prefix '{prefix_expr}'")
            return False, None
        
        # Create corrected question
        corrected_question = question.copy()
        corrected_question["options"] = corrected_options
        
        # Ensure exactly one correct answer for RADIO
        correct_count = sum(1 for opt in corrected_options if opt.get("is_correct", False))
        if question.get("question_type") == "RADIO" and correct_count != 1:
            # Keep first correct, mark others incorrect
            found_first = False
            for opt in corrected_options:
                if opt.get("is_correct", False):
                    if found_first:
                        opt["is_correct"] = False
                    else:
                        found_first = True
        
        return True, corrected_question
    
    def _is_valid_prefix_expression(self, expr: str) -> bool:
        """Check if expression is valid prefix notation"""
        if not expr:
            return False
        
        # Remove extra whitespace
        tokens = expr.split()
        if not tokens:
            return False
        
        # Prefix must start with operator
        if tokens[0] not in ['+', '-', '*', '/', '^']:
            return False
        
        # Count operators and operands
        operator_count = 0
        operand_count = 0
        
        for token in tokens:
            if token in ['+', '-', '*', '/', '^']:
                operator_count += 1
            else:
                # Try to parse as number
                try:
                    float(token)
                    operand_count += 1
                except ValueError:
                    # Might be a variable or invalid
                    operand_count += 1
        
        # Valid prefix: operators + 1 == operands (for binary operators)
        # For n operators, we need n+1 operands
        return operand_count == operator_count + 1
    
    def _is_infix_expression(self, expr: str) -> bool:
        """Check if expression is infix notation (not prefix)"""
        # Infix has pattern: number operator number (with optional spaces)
        infix_pattern = r'\d+\s*[+\-*/]\s*\d+'
        return bool(re.search(infix_pattern, expr))
    
    def _prefix_to_infix(self, prefix_expr: str) -> Optional[str]:
        """Convert prefix expression to infix using stack-based algorithm"""
        try:
            tokens = prefix_expr.split()
            if not tokens:
                return None
            
            stack = []
            
            # Process from RIGHT to LEFT (standard prefix evaluation)
            # This ensures correct operator precedence handling
            for token in reversed(tokens):
                token = token.strip()
                if not token:
                    continue
                    
                if token in ['+', '-', '*', '/', '^']:
                    # Operator: pop two operands
                    if len(stack) < 2:
                        print(f"[VALIDATION] Not enough operands for operator '{token}' in prefix '{prefix_expr}'")
                        return None
                    operand1 = stack.pop()
                    operand2 = stack.pop()
                    # Create infix expression with parentheses for clarity
                    infix = f"({operand1} {token} {operand2})"
                    stack.append(infix)
                else:
                    # Operand: push to stack
                    try:
                        float(token)  # Validate it's a number
                        stack.append(token)
                    except ValueError:
                        # Might be a variable (single letter or word)
                        if re.match(r'^[a-zA-Z][a-zA-Z0-9]*$', token):
                            stack.append(token)
                        else:
                            print(f"[VALIDATION] Invalid operand '{token}' in prefix '{prefix_expr}'")
                            return None
            
            # After processing all tokens, stack should have exactly one element
            if len(stack) != 1:
                print(f"[VALIDATION] Invalid prefix expression '{prefix_expr}': stack has {len(stack)} elements")
                return None
            
            result = stack[0]
            # Keep parentheses for clarity (don't remove outer ones)
            return result
            
        except Exception as e:
            print(f"[VALIDATION] Error converting prefix to infix: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _normalize_infix_expression(self, expr: str) -> str:
        """Normalize infix expression for comparison"""
        # Remove all whitespace
        expr = re.sub(r'\s+', '', expr)
        # Remove outer parentheses if present (but keep inner ones for structure)
        # Only remove if the entire expression is wrapped
        while expr.startswith('(') and expr.endswith(')'):
            # Check if removing outer parentheses would break structure
            inner = expr[1:-1]
            # Count parentheses balance
            if inner.count('(') == inner.count(')'):
                expr = inner
            else:
                break
        return expr.lower()
    
    def _infix_expressions_equivalent(self, expr1: str, expr2: str) -> bool:
        """Check if two infix expressions are equivalent (accounting for parentheses)"""
        # Normalize both
        norm1 = self._normalize_infix_expression(expr1)
        norm2 = self._normalize_infix_expression(expr2)
        
        # Direct match
        if norm1 == norm2:
            return True
        
        # Try removing all parentheses and compare
        no_parens1 = re.sub(r'[()]', '', norm1)
        no_parens2 = re.sub(r'[()]', '', norm2)
        if no_parens1 == no_parens2:
            return True
        
        return False
    
    def _validate_infix_to_prefix_question(self, question: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Validate Infix → Prefix conversion question"""
        # Similar validation logic but for infix → prefix
        # For now, basic validation
        return self._validate_expression_syntax_basic(question.get("question_text", ""), question.get("options", []))
    
    def _validate_postfix_to_infix_question(self, question: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Validate Postfix → Infix conversion question"""
        # Similar validation logic but for postfix → infix
        # For now, basic validation
        return self._validate_expression_syntax_basic(question.get("question_text", ""), question.get("options", []))
    
    def _validate_expression_syntax_basic(self, question_text: str, options: List[Dict[str, Any]]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Basic expression syntax validation.
        Returns (is_valid, None) - no correction needed for basic validation
        """
        valid_operators = ['+', '-', '*', '/', '^', '(', ')']
        
        # Check if options contain valid expressions
        for option in options:
            option_text = option.get("option_text", "")
            # Check for balanced parentheses
            if option_text.count('(') != option_text.count(')'):
                print(f"[VALIDATION] Unbalanced parentheses in option: '{option_text}'")
                return False, None
        
        return True, None

