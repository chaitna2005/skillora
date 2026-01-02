"""
Quiz Model
Handles quiz-related database operations
"""
from typing import Optional, Dict, Any, List
from psycopg2.extras import RealDictCursor


class QuizModel:
    
    @staticmethod
    def create_quiz(cursor: RealDictCursor, quiz_data: Dict[str, Any]) -> Optional[Dict]:
        """Create a new quiz"""
        query = """
            INSERT INTO "Quiz" (user_id, prompt, total_no_questions, difficulty_level, quiz_name, created_date)
            VALUES (%(user_id)s, %(prompt)s, %(total_no_questions)s, %(difficulty_level)s, %(quiz_name)s, NOW())
            RETURNING quiz_id, user_id, prompt, total_no_questions, difficulty_level, quiz_name, created_date
        """
        cursor.execute(query, quiz_data)
        return dict(cursor.fetchone())
    
    @staticmethod
    def get_quiz_by_id(cursor: RealDictCursor, quiz_id: int) -> Optional[Dict]:
        """Get quiz by ID"""
        query = """
            SELECT q.*, u.username as creator_username
            FROM "Quiz" q
            JOIN "User" u ON q.user_id = u.user_id
            WHERE q.quiz_id = %s
        """
        cursor.execute(query, (quiz_id,))
        result = cursor.fetchone()
        return dict(result) if result else None
    
    @staticmethod
    def get_quizzes_by_user(cursor: RealDictCursor, user_id: int) -> List[Dict]:
        """Get all quizzes created by a user"""
        query = """
            SELECT quiz_id, user_id, prompt, total_no_questions, difficulty_level, quiz_name, created_date
            FROM "Quiz"
            WHERE user_id = %s
            ORDER BY created_date DESC
        """
        print(f"[MODEL] get_quizzes_by_user querying with user_id: {user_id}")
        cursor.execute(query, (user_id,))
        results = [dict(row) for row in cursor.fetchall()]
        print(f"[MODEL] get_quizzes_by_user found {len(results)} quizzes")
        if results:
            print(f"[MODEL] Sample quiz: {results[0]}")
        return results
    
    @staticmethod
    def get_assigned_quizzes(cursor: RealDictCursor, user_id: int) -> List[Dict]:
        """Get all quizzes assigned to a user"""
        query = """
            SELECT 
                qa.quiz_assignment_id,
                qa.assign_date,
                qa.due_date,
                q.quiz_id,
                q.quiz_name,
                q.difficulty_level,
                q.total_no_questions,
                q.created_date,
                u.username as assigned_by_username
            FROM "Quiz_Assignment" qa
            JOIN "Quiz" q ON qa.quiz_id = q.quiz_id
            JOIN "User" u ON qa.assigned_by = u.user_id
            WHERE qa.user_id = %s
            ORDER BY qa.assign_date DESC
        """
        print(f"[MODEL] get_assigned_quizzes querying with user_id: {user_id}")
        cursor.execute(query, (user_id,))
        results = [dict(row) for row in cursor.fetchall()]
        print(f"[MODEL] get_assigned_quizzes found {len(results)} assigned quizzes")
        if results:
            print(f"[MODEL] Sample assigned quiz: {results[0]}")
        return results
    
    @staticmethod
    def delete_quiz(cursor: RealDictCursor, quiz_id: int, user_id: int) -> bool:
        """Delete a quiz - only if created by the user"""
        query = """
            DELETE FROM "Quiz"
            WHERE quiz_id = %s AND user_id = %s
        """
        cursor.execute(query, (quiz_id, user_id))
        return cursor.rowcount > 0
    
    @staticmethod
    def create_quiz_assignment(cursor: RealDictCursor, assignment_data: Dict[str, Any]) -> Optional[Dict]:
        """Assign a quiz to a user"""
        query = """
            INSERT INTO "Quiz_Assignment" (user_id, assigned_by, quiz_id, assign_date, due_date)
            VALUES (%(user_id)s, %(assigned_by)s, %(quiz_id)s, NOW(), %(due_date)s)
            RETURNING quiz_assignment_id, user_id, assigned_by, quiz_id, assign_date, due_date
        """
        cursor.execute(query, assignment_data)
        return dict(cursor.fetchone())
    
    @staticmethod
    def delete_all_user_quizzes(cursor: RealDictCursor, user_id: int) -> int:
        """Delete all quizzes created by a user"""
        query = """
            DELETE FROM "Quiz"
            WHERE user_id = %s
        """
        cursor.execute(query, (user_id,))
        return cursor.rowcount
    
    @staticmethod
    def delete_all_assigned_quizzes(cursor: RealDictCursor, user_id: int) -> int:
        """Delete all quiz assignments for a user (unassign all quizzes)"""
        query = """
            DELETE FROM "Quiz_Assignment"
            WHERE user_id = %s
        """
        cursor.execute(query, (user_id,))
        return cursor.rowcount
    
    @staticmethod
    def delete_quizzes_by_ids(cursor: RealDictCursor, quiz_ids: List[int], user_id: int) -> int:
        """Delete specific quizzes by IDs - only if they belong to user"""
        if not quiz_ids:
            return 0
        
        # Use parameterized query with tuple for IN clause
        placeholders = ','.join(['%s'] * len(quiz_ids))
        query = f"""
            DELETE FROM "Quiz"
            WHERE quiz_id IN ({placeholders})
                AND user_id = %s
        """
        cursor.execute(query, tuple(quiz_ids) + (user_id,))
        return cursor.rowcount
    
    @staticmethod
    def delete_assigned_quizzes_by_ids(cursor: RealDictCursor, assignment_ids: List[int], user_id: int) -> int:
        """Delete specific quiz assignments by IDs - only if they belong to user"""
        if not assignment_ids:
            return 0
        
        # Use parameterized query with tuple for IN clause
        placeholders = ','.join(['%s'] * len(assignment_ids))
        query = f"""
            DELETE FROM "Quiz_Assignment"
            WHERE quiz_assignment_id IN ({placeholders})
                AND user_id = %s
        """
        cursor.execute(query, tuple(assignment_ids) + (user_id,))
        return cursor.rowcount

