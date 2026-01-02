"""
Test Service
Business logic for test taking and evaluation
"""
import re
import math
from typing import Dict, Any, List, Optional, Set
from psycopg2.extras import RealDictCursor
from app.models.test import TestModel
from app.models.question import QuestionModel


class TestService:
    
    @staticmethod
    def _normalize_number(value: Any) -> Optional[float]:
        """Normalize a value to a number for comparison"""
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            # Remove whitespace and try to convert
            value = value.strip()
            try:
                return float(value)
            except ValueError:
                return None
        return None
    
    @staticmethod
    def _normalize_string(value: str) -> str:
        """Normalize string for comparison (trim, lowercase)"""
        if not isinstance(value, str):
            return str(value).strip().lower()
        return value.strip().lower()
    
    @staticmethod
    def _extract_math_value(text: str) -> Optional[float]:
        """Extract numeric value from option text - CRITICAL: Compute math, don't trust LLM"""
        if not text:
            return None
        
        # Remove common prefixes
        text = re.sub(r'^[A-Z]\.\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^\d+\.\s*', '', text)
        text = re.sub(r'^answer:\s*', '', text, flags=re.IGNORECASE)
        text = text.strip()
        
        # Try pure number first
        try:
            return float(text)
        except ValueError:
            pass
        
        # Try to extract number from expression
        number_match = re.search(r'^(\d+(?:\.\d+)?)$', text)
        if number_match:
            try:
                return float(number_match.group(1))
            except ValueError:
                pass
        
        # CRITICAL: Extract and evaluate math expressions
        # Handle various formats: "3 x 3", "3*3", "3 × 3", "3 + 4", "5 - 2", "8 / 2"
        try:
            # Normalize multiplication symbols (x, ×, X) to *
            normalized_text = text.replace('×', '*').replace('x', '*').replace('X', '*')
            # Normalize division symbols (÷) to /
            normalized_text = normalized_text.replace('÷', '/')
            
            # Extract math expression - allow digits, operators, parentheses, decimal points, spaces
            # Pattern: number operator number (with optional spaces)
            math_pattern = r'(\d+(?:\.\d+)?)\s*([+\-*/])\s*(\d+(?:\.\d+)?)'
            match = re.search(math_pattern, normalized_text)
            if match:
                num1 = float(match.group(1))
                operator = match.group(2)
                num2 = float(match.group(3))
                
                # Compute result using Python (NOT trusting LLM)
                if operator == '+':
                    result = num1 + num2
                elif operator == '-':
                    result = num1 - num2
                elif operator == '*':
                    result = num1 * num2
                elif operator == '/':
                    if num2 == 0:
                        return None  # Division by zero
                    result = num1 / num2
                else:
                    return None
                
                return float(result)
            
            # Try to evaluate as a general expression (for more complex cases)
            # Clean the expression - keep only safe math characters
            safe_text = re.sub(r'[^\d+\-*/()^.\s]', '', normalized_text)
            safe_text = safe_text.replace('^', '**')  # Exponentiation
            
            if safe_text and re.search(r'[\d+\-*/()^]', safe_text):
                safe_dict = {
                    "__builtins__": {},
                    "abs": abs,
                    "round": round,
                    "min": min,
                    "max": max,
                    "sum": sum,
                    "pow": pow,
                    "math": math
                }
                result = eval(safe_text, safe_dict)
                if isinstance(result, (int, float)):
                    return float(result)
        except Exception as e:
            print(f"[MATH_EXTRACT] Error extracting math value from '{text}': {e}")
            pass
        
        return None
    
    @staticmethod
    def _is_math_question(question_text: str) -> bool:
        """Check if question is a math question"""
        math_patterns = [
            r'\d+\s*[+\-*/x×]\s*\d+',  # Include x and × for multiplication
            r'\d+\s*x\s*\d+',  # Explicit x multiplication
            r'\d+\s*×\s*\d+',  # Explicit × multiplication
            r'what is\s+\d+',
            r'calculate',
            r'solve',
            r'compute',
            r'equals?',
            r'=\s*\d+',
            r'=\s*\?',  # "= ?" pattern
        ]
        question_lower = question_text.lower()
        return any(re.search(pattern, question_lower, re.IGNORECASE) for pattern in math_patterns)
    
    @staticmethod
    def _compute_correct_answer(question_text: str, question_type: str) -> Optional[float]:
        """Compute correct answer from question text - CRITICAL: Use Python, NOT LLM"""
        # Extract target value for CHECKLIST questions like "which equal 10"
        target_match = re.search(r'equal(?:s| to)?\s+(\d+(?:\.\d+)?)', question_text, re.IGNORECASE)
        if target_match:
            try:
                return float(target_match.group(1))
            except ValueError:
                pass
        
        # Extract math expression from question
        # Patterns: "What is 3 x 3?", "What is 3 * 3?", "Calculate 5 x 4", "3 x 3 = ?"
        
        # Normalize multiplication symbols
        normalized_text = question_text.replace('×', '*').replace('x', '*').replace('X', '*')
        normalized_text = normalized_text.replace('÷', '/')
        
        # Pattern 1: "What is 3 x 3?" or "What is 3 * 3?"
        what_is_match = re.search(r'what is\s+([\d\s+\-*/()^.\s]+)', normalized_text, re.IGNORECASE)
        if what_is_match:
            expr = what_is_match.group(1).strip()
            # Try to extract and compute simple expression
            value = TestService._extract_math_value(expr)
            if value is not None:
                return value
        
        # Pattern 2: "Calculate 5 x 4" or "Solve 3 x 3"
        calc_match = re.search(r'(?:calculate|solve|compute)\s+([\d\s+\-*/()^.\s]+)', normalized_text, re.IGNORECASE)
        if calc_match:
            expr = calc_match.group(1).strip()
            value = TestService._extract_math_value(expr)
            if value is not None:
                return value
        
        # Pattern 3: "3 x 3 = ?" or "5 * 4 = ?"
        equals_q_match = re.search(r'([\d\s+\-*/()^.\s]+)\s*=\s*\?', normalized_text, re.IGNORECASE)
        if equals_q_match:
            expr = equals_q_match.group(1).strip()
            value = TestService._extract_math_value(expr)
            if value is not None:
                return value
        
        # Pattern 4: Direct expression in question (e.g., "3 x 3")
        direct_expr_match = re.search(r'(\d+(?:\.\d+)?)\s*([+\-*/])\s*(\d+(?:\.\d+)?)', normalized_text)
        if direct_expr_match:
            num1 = float(direct_expr_match.group(1))
            operator = direct_expr_match.group(2)
            num2 = float(direct_expr_match.group(3))
            
            # Compute using Python (NOT trusting LLM)
            if operator == '+':
                return float(num1 + num2)
            elif operator == '-':
                return float(num1 - num2)
            elif operator == '*':
                return float(num1 * num2)
            elif operator == '/':
                if num2 != 0:
                    return float(num1 / num2)
        
        # Fallback: Try general expression evaluation
        try:
            safe_expr = re.sub(r'[^\d+\-*/()^.\s]', '', normalized_text)
            safe_expr = safe_expr.replace('^', '**')
            if safe_expr and re.search(r'[\d+\-*/()^]', safe_expr):
                safe_dict = {
                    "__builtins__": {},
                    "abs": abs,
                    "round": round,
                    "min": min,
                    "max": max,
                    "sum": sum,
                    "pow": pow,
                    "math": math
                }
                result = eval(safe_expr, safe_dict)
                if isinstance(result, (int, float)):
                    return float(result)
        except Exception:
            pass
        
        return None
    
    @staticmethod
    def _determine_correct_options(
        question_text: str,
        question_type: str,
        options: List[Dict[str, Any]]
    ) -> Set[int]:
        """
        Deterministically determine which options are correct.
        This re-computes correct answers instead of trusting database flags.
        """
        # Check if math question
        if not TestService._is_math_question(question_text):
            # Non-math question: use database flags
            return set(
                int(opt["question_option_id"])
                for opt in options
                if opt.get("is_correct", False)
            )
        
        # Math question: re-compute correct answer using Python (NEVER trust LLM)
        correct_answer = TestService._compute_correct_answer(question_text, question_type)
        if correct_answer is None:
            # CRITICAL: If we can't compute, try harder - don't trust database flags
            # Try to extract math expression from question text more aggressively
            print(f"[MATH_EVAL] Could not compute answer for '{question_text}', trying alternative extraction")
            # Try to find any math expression in the question
            math_expr_match = re.search(r'(\d+(?:\.\d+)?)\s*([+\-*/x×])\s*(\d+(?:\.\d+)?)', question_text, re.IGNORECASE)
            if math_expr_match:
                try:
                    num1 = float(math_expr_match.group(1))
                    op = math_expr_match.group(2).replace('x', '*').replace('×', '*').replace('X', '*')
                    num2 = float(math_expr_match.group(3))
                    if op == '+':
                        correct_answer = num1 + num2
                    elif op == '-':
                        correct_answer = num1 - num2
                    elif op == '*':
                        correct_answer = num1 * num2
                    elif op == '/':
                        if num2 != 0:
                            correct_answer = num1 / num2
                except Exception as e:
                    print(f"[MATH_EVAL] Alternative extraction failed: {e}")
            
            # If still can't compute, mark all options as potentially correct (better than wrong)
            if correct_answer is None:
                print(f"[MATH_EVAL] WARNING: Cannot compute answer, cannot trust database flags for math question")
                # Return empty set - evaluation will handle this gracefully
                return set()
        
        # Evaluate each option's value - compute using Python, NOT trusting LLM
        correct_option_ids = set()
        for opt in options:
            option_text = opt.get("option_text", "")
            option_value = TestService._extract_math_value(option_text)
            
            if option_value is not None:
                # Compare with tolerance for floating point
                if abs(option_value - correct_answer) < 0.0001:
                    correct_option_ids.add(int(opt["question_option_id"]))
                    print(f"[MATH_EVAL] Option '{option_text}' = {option_value} matches correct answer {correct_answer}")
        
        # CRITICAL: Never fall back to database flags for math questions
        # If no options match computed answer, return empty set (evaluation will mark as incorrect)
        if not correct_option_ids:
            print(f"[MATH_EVAL] WARNING: No options match computed answer {correct_answer} for question '{question_text}'")
            print(f"[MATH_EVAL] Available options: {[opt.get('option_text', '') for opt in options]}")
            # Return empty set - this will mark question as incorrect, which is safer than trusting wrong LLM answer
            return set()
        
        # For RADIO, return ALL options with correct value (not just one)
        # This allows value-based comparison during evaluation
        return correct_option_ids
    
    @staticmethod
    def evaluate_test(
        cursor: RealDictCursor,
        uqt_id: int,
        answers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluate user's test answers
        
        Args:
            cursor: Database cursor
            uqt_id: User Quiz Take ID
            answers: List of {question_id, question_option_ids}
        
        Returns:
            Dictionary with score and evaluation details
        """
        
        total_correct = 0
        total_questions = len(answers)
        evaluation_details = []
        
        for answer in answers:
            question_id = answer["question_id"]
            # Normalize option IDs to integers for consistent comparison
            user_option_ids = set(int(opt_id) for opt_id in answer["question_option_ids"])
            
            # Get question type directly from database
            question_type_query = """
                SELECT question_type FROM "Question" WHERE question_id = %s
            """
            cursor.execute(question_type_query, (question_id,))
            question_type_result = cursor.fetchone()
            if not question_type_result:
                print(f"[WARNING] Question {question_id} not found, marking as incorrect")
                is_correct = False
                evaluation_details.append({
                    "question_id": question_id,
                    "is_correct": False,
                    "user_option_ids": sorted(list(user_option_ids)),
                    "correct_option_ids": []
                })
                continue
            
            question_type = question_type_result["question_type"]
            
            # Get question text for re-evaluation
            question_query = """
                SELECT question_text FROM "Question" WHERE question_id = %s
            """
            cursor.execute(question_query, (question_id,))
            question_result = cursor.fetchone()
            if not question_result:
                print(f"[WARNING] Question {question_id} text not found, marking as incorrect")
                is_correct = False
                evaluation_details.append({
                    "question_id": question_id,
                    "is_correct": False,
                    "user_option_ids": sorted(list(user_option_ids)),
                    "correct_option_ids": []
                })
                continue
            
            question_text = question_result["question_text"]
            
            # Get all options for this question
            options = QuestionModel.get_question_options(cursor, question_id)
            if not options:
                print(f"[WARNING] No options found for question {question_id}, marking as incorrect")
                is_correct = False
                evaluation_details.append({
                    "question_id": question_id,
                    "is_correct": False,
                    "user_option_ids": sorted(list(user_option_ids)),
                    "correct_option_ids": []
                })
                continue
            
            # CRITICAL: Re-compute correct options deterministically (don't trust database flags)
            correct_option_ids = TestService._determine_correct_options(
                question_text,
                question_type,
                options
            )
            
            # Evaluate based on question type using VALUE-based comparison
            if question_type == "RADIO":
                # RADIO: Compare VALUES, not option IDs
                # User must select exactly one option
                if len(user_option_ids) != 1:
                    is_correct = False
                else:
                    # Get the value of user's selected option
                    user_selected_id = next(iter(user_option_ids))
                    user_option = next((opt for opt in options if int(opt["question_option_id"]) == user_selected_id), None)
                    
                    if user_option is None:
                        is_correct = False
                    else:
                        # Always use value-based comparison for consistency
                        # Check if this is a math question
                        is_math = TestService._is_math_question(question_text)
                        
                        if is_math:
                            # Compute correct answer value
                            correct_answer_value = TestService._compute_correct_answer(question_text, question_type)
                            if correct_answer_value is not None:
                                # Extract value from user's selected option
                                user_option_value = TestService._extract_math_value(user_option.get("option_text", ""))
                                if user_option_value is not None:
                                    # Compare values (with tolerance for floating point)
                                    is_correct = abs(user_option_value - correct_answer_value) < 0.0001
                                else:
                                    # Can't extract value, check if option ID is in correct set
                                    # But also check if any option with same text is correct
                                    user_option_text = user_option.get("option_text", "").strip()
                                    is_correct = False
                                    for opt in options:
                                        if opt.get("option_text", "").strip() == user_option_text:
                                            opt_value = TestService._extract_math_value(opt.get("option_text", ""))
                                            if opt_value is not None and abs(opt_value - correct_answer_value) < 0.0001:
                                                is_correct = True
                                                break
                                    if not is_correct:
                                        is_correct = user_selected_id in correct_option_ids
                            else:
                                # Can't compute correct answer, fall back to option ID comparison
                                is_correct = user_selected_id in correct_option_ids
                        else:
                            # Non-math question: compare option text values (normalized)
                            user_option_text = TestService._normalize_string(user_option.get("option_text", ""))
                            # Check if any correct option has the same text
                            is_correct = False
                            for opt in options:
                                if int(opt["question_option_id"]) in correct_option_ids:
                                    correct_option_text = TestService._normalize_string(opt.get("option_text", ""))
                                    if correct_option_text == user_option_text:
                                        is_correct = True
                                        break
                            # Fallback to option ID comparison
                            if not is_correct:
                                is_correct = user_selected_id in correct_option_ids
            else:  # CHECKLIST
                # CHECKLIST: Mark as correct if user selected at least one correct option
                # Partial correctness is allowed - selecting correct options is rewarded
                # Extra incorrect selections do not automatically fail the question
                is_correct = len(user_option_ids & correct_option_ids) > 0
            
            if is_correct:
                total_correct += 1
            
            # Save each selected option as an answer
            # CRITICAL: Delete existing answers for this question first (in case they were saved incrementally)
            # Then save with computed correctness values
            TestModel.delete_answers_for_question(cursor, uqt_id, question_id)
            
            # Save answers with computed correctness
            for option_id in user_option_ids:
                # For RADIO questions, all selected options have the same correctness
                # For CHECKLIST, check if this specific option is correct
                if question_type == "RADIO":
                    option_is_correct = is_correct  # All selected options have same correctness
                else:  # CHECKLIST
                    option_is_correct = int(option_id) in correct_option_ids
                
                TestModel.save_answer(cursor, {
                    "uqt_id": uqt_id,
                    "question_id": question_id,
                    "question_option_id": int(option_id),
                    "is_correct": option_is_correct
                })
            
            evaluation_details.append({
                "question_id": question_id,
                "is_correct": is_correct,
                "user_option_ids": sorted(list(user_option_ids)),
                "correct_option_ids": sorted(list(correct_option_ids))
            })
        
        # Calculate score percentage
        score_percentage = (total_correct / total_questions * 100) if total_questions > 0 else 0
        
        # Determine result category
        if score_percentage >= 80:
            result = "EXCELLENT"
        elif score_percentage >= 60:
            result = "GOOD"
        else:
            result = "NEEDS_IMPROVEMENT"
        
        # Update quiz take with results
        TestModel.complete_quiz_take(cursor, uqt_id, total_correct, result)
        
        return {
            "total_questions": total_questions,
            "total_correct": total_correct,
            "score_percentage": score_percentage,
            "result": result,
            "details": evaluation_details
        }
    
    @staticmethod
    def get_feedback_message(result: str, score_percentage: float) -> str:
        """Generate qualitative feedback based on score"""
        if result == "EXCELLENT":
            return f"Excellent work! You scored {score_percentage:.1f}%. You have a strong understanding of the topic."
        elif result == "GOOD":
            return f"Good job! You scored {score_percentage:.1f}%. Keep practicing to improve further."
        else:
            return f"You scored {score_percentage:.1f}%. Review the material and try again to improve your understanding."

