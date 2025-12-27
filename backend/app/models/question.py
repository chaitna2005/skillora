"""
Question Model
Handles question and question options database operations
"""
from typing import Optional, Dict, Any, List
from psycopg2.extras import RealDictCursor


class QuestionModel:
    
    @staticmethod
    def create_question(cursor: RealDictCursor, question_data: Dict[str, Any]) -> Optional[Dict]:
        """Create a new question"""
        query = """
            INSERT INTO "Question" (quiz_id, question_text, question_type)
            VALUES (%(quiz_id)s, %(question_text)s, %(question_type)s)
            RETURNING question_id, quiz_id, question_text, question_type
        """
        cursor.execute(query, question_data)
        return dict(cursor.fetchone())
    
    @staticmethod
    def create_question_option(cursor: RealDictCursor, option_data: Dict[str, Any]) -> Optional[Dict]:
        """Create a question option"""
        query = """
            INSERT INTO "QuestionOption" (question_id, option_text, is_correct)
            VALUES (%(question_id)s, %(option_text)s, %(is_correct)s)
            RETURNING question_option_id, question_id, option_text, is_correct
        """
        cursor.execute(query, option_data)
        return dict(cursor.fetchone())
    
    @staticmethod
    def get_questions_by_quiz(cursor: RealDictCursor, quiz_id: int) -> List[Dict]:
        """Get all questions for a quiz"""
        query = """
            SELECT question_id, quiz_id, question_text, question_type
            FROM "Question"
            WHERE quiz_id = %s
            ORDER BY question_id
        """
        cursor.execute(query, (quiz_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_question_options(cursor: RealDictCursor, question_id: int) -> List[Dict]:
        """Get all options for a question"""
        query = """
            SELECT question_option_id, question_id, option_text, is_correct
            FROM "QuestionOption"
            WHERE question_id = %s
            ORDER BY question_option_id
        """
        cursor.execute(query, (question_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_quiz_with_questions(cursor: RealDictCursor, quiz_id: int) -> Optional[Dict]:
        """Get quiz with all questions and options"""
        # Get quiz
        quiz_query = """
            SELECT quiz_id, user_id, prompt, total_no_questions, difficulty_level, quiz_name, created_date
            FROM "Quiz"
            WHERE quiz_id = %s
        """
        cursor.execute(quiz_query, (quiz_id,))
        quiz = cursor.fetchone()
        
        if not quiz:
            return None
        
        quiz_dict = dict(quiz)
        
        # Get questions
        questions = QuestionModel.get_questions_by_quiz(cursor, quiz_id)
        
        # Get options for each question
        for question in questions:
            options = QuestionModel.get_question_options(cursor, question['question_id'])
            question['options'] = options
        
        quiz_dict['questions'] = questions
        return quiz_dict

