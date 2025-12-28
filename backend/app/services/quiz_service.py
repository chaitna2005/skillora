"""
Quiz Service
Business logic for quiz creation and management
"""
from typing import Dict, Any
from psycopg2.extras import RealDictCursor
from app.models.quiz import QuizModel
from app.models.question import QuestionModel
from app.services.openai_service_direct import OpenAIService


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
        1. Generate quiz name from prompt
        2. Create quiz record
        3. Generate questions using OpenAI
        4. Save questions and options to database
        """
        
        # Step 1: Generate quiz name
        quiz_name = self.openai_service.generate_quiz_name(prompt)
        
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
        
        # Step 3: Generate questions
        questions = self.openai_service.generate_quiz_questions(
            prompt=prompt,
            difficulty_level=difficulty_level,
            total_questions=total_no_questions
        )
        
        # Step 4: Save questions and options
        for question_data in questions:
            # Create question
            question = QuestionModel.create_question(cursor, {
                "quiz_id": quiz_id,
                "question_text": question_data["question_text"],
                "question_type": question_data["question_type"]
            })
            
            question_id = question["question_id"]
            
            # Create options
            for option_data in question_data["options"]:
                QuestionModel.create_question_option(cursor, {
                    "question_id": question_id,
                    "option_text": option_data["option_text"],
                    "is_correct": option_data["is_correct"]
                })
        
        # Return complete quiz with questions
        return QuestionModel.get_quiz_with_questions(cursor, quiz_id)

