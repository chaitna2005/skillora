"""
Test Model
Handles user quiz attempts and results
"""
from typing import Optional, Dict, Any, List
from psycopg2.extras import RealDictCursor


class TestModel:
    
    @staticmethod
    def create_quiz_take(cursor: RealDictCursor, take_data: Dict[str, Any]) -> Optional[Dict]:
        """Create a new quiz attempt"""
        query = """
            INSERT INTO "User_Quiz_Take" (user_id, quiz_id, start_time, quiz_assignment_id)
            VALUES (%(user_id)s, %(quiz_id)s, NOW(), %(quiz_assignment_id)s)
            RETURNING uqt_id, user_id, quiz_id, start_time, quiz_assignment_id
        """
        cursor.execute(query, take_data)
        return dict(cursor.fetchone())
    
    @staticmethod
    def complete_quiz_take(cursor: RealDictCursor, uqt_id: int, total_correct: int, result: str) -> Optional[Dict]:
        """Mark quiz attempt as completed"""
        query = """
            UPDATE "User_Quiz_Take"
            SET completed_time = NOW(), total_correct = %s, result = %s
            WHERE uqt_id = %s
            RETURNING uqt_id, user_id, quiz_id, start_time, completed_time, total_correct, result, quiz_assignment_id
        """
        cursor.execute(query, (total_correct, result, uqt_id))
        return dict(cursor.fetchone())
    
    @staticmethod
    def save_answer(cursor: RealDictCursor, answer_data: Dict[str, Any]) -> None:
        """Save a user's answer to a question"""
        query = """
            INSERT INTO "Quiz_Take_Question_Answers" (uqt_id, question_id, question_option_id, is_correct)
            VALUES (%(uqt_id)s, %(question_id)s, %(question_option_id)s, %(is_correct)s)
        """
        cursor.execute(query, answer_data)
    
    @staticmethod
    def get_quiz_take(cursor: RealDictCursor, uqt_id: int) -> Optional[Dict]:
        """Get quiz take details"""
        query = """
            SELECT uqt.*, q.quiz_name, q.total_no_questions, q.difficulty_level
            FROM "User_Quiz_Take" uqt
            JOIN "Quiz" q ON uqt.quiz_id = q.quiz_id
            WHERE uqt.uqt_id = %s
        """
        cursor.execute(query, (uqt_id,))
        result = cursor.fetchone()
        return dict(result) if result else None
    
    @staticmethod
    def get_user_quiz_takes(cursor: RealDictCursor, user_id: int, quiz_id: int) -> List[Dict]:
        """Get all attempts for a specific quiz by a user"""
        query = """
            SELECT uqt_id, user_id, quiz_id, start_time, completed_time, total_correct, result, quiz_assignment_id
            FROM "User_Quiz_Take"
            WHERE user_id = %s AND quiz_id = %s
            ORDER BY start_time DESC
        """
        cursor.execute(query, (user_id, quiz_id))
        return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_all_user_tests(cursor: RealDictCursor, user_id: int) -> List[Dict]:
        """Get all tests taken by a user"""
        query = """
            SELECT 
                uqt.uqt_id,
                uqt.user_id,
                uqt.start_time,
                uqt.completed_time,
                uqt.total_correct,
                uqt.result,
                q.quiz_id,
                q.quiz_name,
                q.total_no_questions,
                q.difficulty_level
            FROM "User_Quiz_Take" uqt
            JOIN "Quiz" q ON uqt.quiz_id = q.quiz_id
            WHERE uqt.user_id = %s
            ORDER BY uqt.start_time DESC
        """
        cursor.execute(query, (user_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_test_answers(cursor: RealDictCursor, uqt_id: int) -> List[Dict]:
        """Get all answers for a test"""
        query = """
            SELECT 
                qa.uqt_id,
                qa.question_id,
                qa.question_option_id,
                qa.is_correct,
                q.question_text,
                q.question_type,
                qo.option_text
            FROM "Quiz_Take_Question_Answers" qa
            JOIN "Question" q ON qa.question_id = q.question_id
            JOIN "QuestionOption" qo ON qa.question_option_id = qo.question_option_id
            WHERE qa.uqt_id = %s
            ORDER BY qa.question_id
        """
        cursor.execute(query, (uqt_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_pending_tests(cursor: RealDictCursor, user_id: int) -> List[Dict]:
        """Get all pending (incomplete) tests for a user"""
        query = """
            SELECT 
                uqt.uqt_id,
                uqt.user_id,
                uqt.start_time,
                q.quiz_id,
                q.quiz_name,
                q.total_no_questions,
                q.difficulty_level
            FROM "User_Quiz_Take" uqt
            JOIN "Quiz" q ON uqt.quiz_id = q.quiz_id
            WHERE uqt.user_id = %s AND uqt.completed_time IS NULL
            ORDER BY uqt.start_time DESC
        """
        cursor.execute(query, (user_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_completed_tests(cursor: RealDictCursor, user_id: int) -> List[Dict]:
        """Get all completed tests for a user"""
        query = """
            SELECT 
                uqt.uqt_id,
                uqt.user_id,
                uqt.start_time,
                uqt.completed_time,
                uqt.total_correct,
                uqt.result,
                q.quiz_id,
                q.quiz_name,
                q.total_no_questions,
                q.difficulty_level
            FROM "User_Quiz_Take" uqt
            JOIN "Quiz" q ON uqt.quiz_id = q.quiz_id
            WHERE uqt.user_id = %s AND uqt.completed_time IS NOT NULL
            ORDER BY uqt.completed_time DESC
        """
        cursor.execute(query, (user_id,))
        return [dict(row) for row in cursor.fetchall()]

