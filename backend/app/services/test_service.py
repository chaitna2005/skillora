"""
Test Service
Business logic for test taking and evaluation
"""
from typing import Dict, Any, List
from psycopg2.extras import RealDictCursor
from app.models.test import TestModel
from app.models.question import QuestionModel


class TestService:
    
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
            user_option_ids = set(answer["question_option_ids"])
            
            # Get all options for this question
            options = QuestionModel.get_question_options(cursor, question_id)
            
            # Get correct option IDs
            correct_option_ids = set(
                opt["question_option_id"] 
                for opt in options 
                if opt["is_correct"]
            )
            
            # Check if answer is correct
            is_correct = user_option_ids == correct_option_ids
            
            if is_correct:
                total_correct += 1
            
            # Save each selected option as an answer
            for option_id in user_option_ids:
                TestModel.save_answer(cursor, {
                    "uqt_id": uqt_id,
                    "question_id": question_id,
                    "question_option_id": option_id,
                    "is_correct": option_id in correct_option_ids
                })
            
            evaluation_details.append({
                "question_id": question_id,
                "is_correct": is_correct,
                "user_option_ids": list(user_option_ids),
                "correct_option_ids": list(correct_option_ids)
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

