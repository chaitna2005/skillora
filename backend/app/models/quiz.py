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
    def create_shareable_assignment(cursor: RealDictCursor, teacher_id: int, quiz_id: int, share_token: str) -> Optional[Dict]:
        """Create a shareable assignment link (without student user_id)"""
        query = """
            INSERT INTO "Quiz_Assignment" (user_id, assigned_by, quiz_id, assign_date)
            VALUES (%(assigned_by)s, %(assigned_by)s, %(quiz_id)s, NOW())
            RETURNING quiz_assignment_id, user_id, assigned_by, quiz_id, assign_date, due_date
        """
        cursor.execute(query, {
            "assigned_by": teacher_id,
            "quiz_id": quiz_id
        })
        result = dict(cursor.fetchone())
        result["share_token"] = share_token
        return result
    
    @staticmethod
    def get_assignment_by_token(cursor: RealDictCursor, share_token: str) -> Optional[Dict]:
        """Get assignment by share token - decode token to get assignment_id"""
        import base64
        import json
        try:
            decoded = base64.urlsafe_b64decode(share_token + '==')
            token_data = json.loads(decoded)
            assignment_id = token_data.get("assignment_id")
            if not assignment_id:
                return None
            
            query = """
                SELECT qa.*, q.quiz_name, q.total_no_questions, q.difficulty_level
                FROM "Quiz_Assignment" qa
                JOIN "Quiz" q ON qa.quiz_id = q.quiz_id
                WHERE qa.quiz_assignment_id = %s AND qa.user_id = qa.assigned_by
            """
            cursor.execute(query, (assignment_id,))
            result = cursor.fetchone()
            return dict(result) if result else None
        except Exception:
            return None
    
    @staticmethod
    def claim_assignment(cursor: RealDictCursor, share_token: str, user_id: int) -> Optional[Dict]:
        """Claim an assignment by creating a new student assignment record (supports multiple students)"""
        import base64
        import json
        try:
            decoded = base64.urlsafe_b64decode(share_token + '==')
            token_data = json.loads(decoded)
            assignment_id = token_data.get("assignment_id")
            if not assignment_id:
                return None
            
            # Get the original assignment (teacher's template)
            get_query = """
                SELECT quiz_id, assigned_by, assign_date, due_date
                FROM "Quiz_Assignment"
                WHERE quiz_assignment_id = %s
            """
            cursor.execute(get_query, (assignment_id,))
            original = cursor.fetchone()
            if not original:
                return None
            
            # Check if student already claimed this assignment (prevent duplicates)
            check_query = """
                SELECT quiz_assignment_id, user_id, assigned_by, quiz_id, assign_date, due_date
                FROM "Quiz_Assignment"
                WHERE quiz_id = %s AND user_id = %s AND assigned_by = %s
            """
            cursor.execute(check_query, (original["quiz_id"], user_id, original["assigned_by"]))
            existing = cursor.fetchone()
            if existing:
                # Already claimed, return existing record
                return dict(existing)
            
            # Create new assignment record for this student
            insert_query = """
                INSERT INTO "Quiz_Assignment" (user_id, assigned_by, quiz_id, assign_date, due_date)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING quiz_assignment_id, user_id, assigned_by, quiz_id, assign_date, due_date
            """
            cursor.execute(insert_query, (
                user_id,
                original["assigned_by"],
                original["quiz_id"],
                original["assign_date"],
                original["due_date"]
            ))
            result = cursor.fetchone()
            return dict(result) if result else None
        except Exception as e:
            print(f"[ERROR] claim_assignment failed: {e}")
            return None
    
    @staticmethod
    def get_assignment_results_for_teacher(cursor: RealDictCursor, teacher_id: int) -> List[Dict]:
        """Get all assignment results for quizzes assigned by teacher"""
        query = """
            SELECT 
                qa.quiz_assignment_id,
                qa.quiz_id,
                q.quiz_name,
                u.user_id as student_id,
                u.first_name || ' ' || u.last_name as student_name,
                uqt.uqt_id,
                uqt.completed_time,
                uqt.total_correct,
                uqt.result,
                q.total_no_questions,
                CASE 
                    WHEN uqt.uqt_id IS NULL THEN 'Not Attempted'
                    WHEN uqt.completed_time IS NULL THEN 'In Progress'
                    ELSE 'Completed'
                END as attempt_status
            FROM "Quiz_Assignment" qa
            JOIN "Quiz" q ON qa.quiz_id = q.quiz_id
            JOIN "User" u ON qa.user_id = u.user_id
            LEFT JOIN "User_Quiz_Take" uqt ON qa.quiz_assignment_id = uqt.quiz_assignment_id
            WHERE qa.assigned_by = %s AND qa.user_id IS NOT NULL AND qa.user_id != qa.assigned_by
            ORDER BY qa.quiz_id, u.user_id
        """
        cursor.execute(query, (teacher_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_quiz_analytics_for_teacher(cursor: RealDictCursor, teacher_id: int) -> List[Dict]:
        """Get quiz-level analytics for all quizzes assigned by teacher"""
        query = """
            SELECT 
                q.quiz_id,
                q.quiz_name,
                q.total_no_questions,
                COUNT(DISTINCT qa.user_id) as total_students,
                COUNT(DISTINCT CASE WHEN uqt.completed_time IS NOT NULL THEN uqt.uqt_id END) as attempted,
                COALESCE(ROUND(AVG(CASE 
                    WHEN uqt.completed_time IS NOT NULL AND q.total_no_questions > 0 
                    THEN (uqt.total_correct::FLOAT / q.total_no_questions::FLOAT) * 100 
                    END), 1), 0) as average_score,
                COALESCE(ROUND(MAX(CASE 
                    WHEN uqt.completed_time IS NOT NULL AND q.total_no_questions > 0 
                    THEN (uqt.total_correct::FLOAT / q.total_no_questions::FLOAT) * 100 
                    END), 1), 0) as highest_score,
                COALESCE(ROUND(MIN(CASE 
                    WHEN uqt.completed_time IS NOT NULL AND q.total_no_questions > 0 
                    THEN (uqt.total_correct::FLOAT / q.total_no_questions::FLOAT) * 100 
                    END), 1), 0) as lowest_score
            FROM "Quiz" q
            INNER JOIN "Quiz_Assignment" qa ON q.quiz_id = qa.quiz_id
            LEFT JOIN "User_Quiz_Take" uqt ON qa.quiz_assignment_id = uqt.quiz_assignment_id
            WHERE qa.assigned_by = %s AND qa.user_id IS NOT NULL AND qa.user_id != qa.assigned_by
            GROUP BY q.quiz_id, q.quiz_name, q.total_no_questions
            ORDER BY q.quiz_id
        """
        cursor.execute(query, (teacher_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_question_difficulty_for_quiz(cursor: RealDictCursor, quiz_id: int, teacher_id: int) -> List[Dict]:
        """Get question difficulty analysis for a specific quiz"""
        query = """
            WITH question_attempts AS (
                SELECT 
                    q.question_id,
                    uqt.uqt_id,
                    -- Question is incorrect if no correct options were selected for this question in this attempt
                    CASE 
                        WHEN BOOL_OR(qtqa.is_correct = TRUE) = TRUE THEN FALSE
                        ELSE TRUE
                    END as is_incorrect
                FROM "Question" q
                INNER JOIN "Quiz_Take_Question_Answers" qtqa ON q.question_id = qtqa.question_id
                INNER JOIN "User_Quiz_Take" uqt ON qtqa.uqt_id = uqt.uqt_id
                WHERE q.quiz_id = %s 
                    AND uqt.completed_time IS NOT NULL
                GROUP BY q.question_id, uqt.uqt_id
            )
            SELECT 
                q.question_id,
                q.question_text,
                COALESCE(COUNT(DISTINCT qa.uqt_id), 0) as total_attempts,
                COALESCE(ROUND(
                    (COUNT(DISTINCT CASE WHEN qa.is_incorrect = TRUE THEN qa.uqt_id END)::FLOAT / 
                     NULLIF(COUNT(DISTINCT qa.uqt_id), 0)::FLOAT) * 100, 
                    1
                ), 0.0) as incorrect_percentage
            FROM "Question" q
            LEFT JOIN question_attempts qa ON q.question_id = qa.question_id
            WHERE q.quiz_id = %s
            GROUP BY q.question_id, q.question_text
            ORDER BY q.question_id
        """
        try:
            cursor.execute(query, (quiz_id, quiz_id))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"[ERROR] Failed to get question difficulty: {e}")
            return []
    
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

