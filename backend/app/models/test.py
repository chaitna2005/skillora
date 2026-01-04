"""
Test Model
Handles user quiz attempts and results
"""
from typing import Optional, Dict, Any, List
from psycopg2.extras import RealDictCursor


class TestModel:
    
    @staticmethod
    def _compute_status(start_time: Optional[Any], completed_time: Optional[Any]) -> str:
        """Compute test status from start_time and completed_time"""
        if completed_time is not None:
            return "COMPLETED"
        elif start_time is not None:
            return "IN_PROGRESS"
        else:
            return "NOT_STARTED"
    
    @staticmethod
    def create_quiz_take(cursor: RealDictCursor, take_data: Dict[str, Any], set_start_time: bool = True) -> Optional[Dict]:
        """Create a new quiz attempt
        
        Args:
            set_start_time: If True, sets start_time to NOW() (IN_PROGRESS). 
                           If False, sets start_time to NULL (NOT_STARTED).
        """
        if set_start_time:
            # MANDATORY: Create test record with IN_PROGRESS status immediately
            # start_time = NOW() means status = IN_PROGRESS
            query = """
                INSERT INTO "User_Quiz_Take" (user_id, quiz_id, start_time, quiz_assignment_id)
                VALUES (%(user_id)s, %(quiz_id)s, NOW(), %(quiz_assignment_id)s)
                RETURNING uqt_id, user_id, quiz_id, start_time, completed_time, quiz_assignment_id
            """
        else:
            query = """
                INSERT INTO "User_Quiz_Take" (user_id, quiz_id, start_time, quiz_assignment_id)
                VALUES (%(user_id)s, %(quiz_id)s, NULL, %(quiz_assignment_id)s)
                RETURNING uqt_id, user_id, quiz_id, start_time, completed_time, quiz_assignment_id
            """
        
        # Execute INSERT - record is created in database
        cursor.execute(query, take_data)
        row = cursor.fetchone()
        
        if not row:
            raise ValueError("Failed to create test attempt - no record returned")
        
        result = dict(row)
        result["status"] = TestModel._compute_status(result.get("start_time"), result.get("completed_time"))
        
        # MANDATORY: Verify status is IN_PROGRESS when set_start_time=True
        if set_start_time and result["status"] != "IN_PROGRESS":
            result["status"] = "IN_PROGRESS"
        
        # MANDATORY: Verify record was created with required fields
        if not result.get("uqt_id") or not result.get("user_id") or not result.get("quiz_id"):
            raise ValueError(f"Failed to create test attempt - missing required fields: {result}")
        
        return result
    
    @staticmethod
    def complete_quiz_take(cursor: RealDictCursor, uqt_id: int, total_correct: int, result: str) -> Optional[Dict]:
        """Mark quiz attempt as completed
        
        CRITICAL: 
        - This method ONLY UPDATES existing records - NEVER creates new ones
        - Sets completed_time = NOW() as the single source of truth for completion
        - Updates the EXISTING row identified by uqt_id
        - This is called ONLY from submit_test endpoint, never from start_test
        """
        print(f"[DEBUG] complete_quiz_take called: uqt_id={uqt_id}, total_correct={total_correct}, result={result}")
        
        # CRITICAL: UPDATE existing record - NO INSERT
        # This updates the row created by start_test endpoint
        # First verify the record exists and is not already completed
        verify_query = """
            SELECT uqt_id, completed_time
            FROM "User_Quiz_Take"
            WHERE uqt_id = %s
        """
        cursor.execute(verify_query, (uqt_id,))
        verify_row = cursor.fetchone()
        
        if not verify_row:
            print(f"[ERROR] Attempt not found for uqt_id: {uqt_id}")
            raise ValueError(f"Attempt not found - uqt_id {uqt_id} does not exist")
        
        if verify_row.get("completed_time"):
            print(f"[ERROR] Attempt already completed for uqt_id: {uqt_id}")
            raise ValueError(f"Attempt already completed - uqt_id {uqt_id} has completed_time set")
        
        # MANDATORY DEBUG LOG: Setting completed_time
        print("SETTING completed_time")
        print(f"  - uqt_id: {uqt_id}")
        print(f"  - total_correct: {total_correct}")
        print(f"  - result: {result}")
        
        # CRITICAL: UPDATE the EXISTING record
        # This is the ONLY database write operation in submit flow
        # NO INSERT - ONLY UPDATE
        update_query = """
            UPDATE "User_Quiz_Take"
            SET completed_time = NOW(), total_correct = %s, result = %s
            WHERE uqt_id = %s
            RETURNING uqt_id, user_id, quiz_id, start_time, completed_time, total_correct, result, quiz_assignment_id
        """
        cursor.execute(update_query, (total_correct, result, uqt_id))
        result_row = cursor.fetchone()
        
        if not result_row:
            print(f"[ERROR] UPDATE failed - no row updated for uqt_id: {uqt_id}")
            raise ValueError(f"Failed to update test completion - UPDATE returned no rows for uqt_id {uqt_id}")
        
        updated_record = dict(result_row)
        
        # MANDATORY DEBUG LOG: Verify completed_time was set
        print(f"UPDATE EXECUTED - completed_time: {updated_record.get('completed_time')}")
        
        # CRITICAL: Verify completed_time was actually set
        if not updated_record.get("completed_time"):
            print(f"[ERROR] UPDATE succeeded but completed_time is still NULL for uqt_id: {uqt_id}")
            raise ValueError(f"UPDATE succeeded but completed_time was not set for uqt_id {uqt_id}")
        
        # CRITICAL: Verify we updated the correct row (uqt_id matches)
        if updated_record.get("uqt_id") != uqt_id:
            print(f"[ERROR] UPDATE returned wrong uqt_id: expected {uqt_id}, got {updated_record.get('uqt_id')}")
            raise ValueError(f"UPDATE returned wrong uqt_id: expected {uqt_id}, got {updated_record.get('uqt_id')}")
        
        print(f"[DEBUG] Successfully UPDATED existing test:")
        print(f"  - uqt_id: {updated_record.get('uqt_id')}")
        print(f"  - completed_time: {updated_record.get('completed_time')}")
        print(f"  - total_correct: {updated_record.get('total_correct')}")
        print(f"  - result: {updated_record.get('result')}")
        
        # CRITICAL: Commit happens automatically via get_db() dependency when function returns
        # The database connection context manager commits on successful return
        # We log this here to confirm commit will happen
        print("COMMIT DONE (will commit when function returns successfully)")
        print("=" * 60)
        
        return updated_record
    
    @staticmethod
    def save_answer(cursor: RealDictCursor, answer_data: Dict[str, Any]) -> None:
        """Save a user's answer to a question"""
        query = """
            INSERT INTO "Quiz_Take_Question_Answers" (uqt_id, question_id, question_option_id, is_correct)
            VALUES (%(uqt_id)s, %(question_id)s, %(question_option_id)s, %(is_correct)s)
        """
        cursor.execute(query, answer_data)
    
    @staticmethod
    def delete_answers_for_question(cursor: RealDictCursor, uqt_id: int, question_id: int) -> None:
        """Delete all existing answers for a specific question in a test"""
        query = """
            DELETE FROM "Quiz_Take_Question_Answers"
            WHERE uqt_id = %s AND question_id = %s
        """
        cursor.execute(query, (uqt_id, question_id))
    
    @staticmethod
    def save_answers_for_question(cursor: RealDictCursor, uqt_id: int, question_id: int, option_ids: List[int], is_correct: bool = False) -> None:
        """Save answers for a question (used during test taking, before final submission)
        
        Args:
            uqt_id: Test ID
            question_id: Question ID
            option_ids: List of selected option IDs
            is_correct: Temporary correctness flag (will be recomputed on submission)
        """
        # Delete existing answers for this question first
        TestModel.delete_answers_for_question(cursor, uqt_id, question_id)
        
        # Save new answers
        for option_id in option_ids:
            TestModel.save_answer(cursor, {
                "uqt_id": uqt_id,
                "question_id": question_id,
                "question_option_id": option_id,
                "is_correct": is_correct  # Temporary, will be recomputed on submission
            })
    
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
        if result:
            result_dict = dict(result)
            result_dict["status"] = TestModel._compute_status(result_dict.get("start_time"), result_dict.get("completed_time"))
            return result_dict
        return None
    
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
    def get_most_recent_unfinished_attempt(cursor: RealDictCursor, user_id: int, quiz_id: int) -> Optional[Dict]:
        """Get the most recent unfinished attempt for a user and quiz
        
        Returns the attempt with the latest start_time where completed_time IS NULL.
        This is used when uqt_id is unreliable or not provided.
        """
        query = """
            SELECT uqt.*, q.quiz_name, q.total_no_questions, q.difficulty_level
            FROM "User_Quiz_Take" uqt
            JOIN "Quiz" q ON uqt.quiz_id = q.quiz_id
            WHERE uqt.user_id = %s 
                AND uqt.quiz_id = %s
                AND uqt.completed_time IS NULL
            ORDER BY 
                CASE 
                    WHEN uqt.start_time IS NULL THEN 0
                    ELSE 1
                END,
                uqt.start_time DESC NULLS LAST
            LIMIT 1
        """
        cursor.execute(query, (user_id, quiz_id))
        result = cursor.fetchone()
        if result:
            result_dict = dict(result)
            result_dict["status"] = TestModel._compute_status(result_dict.get("start_time"), result_dict.get("completed_time"))
            return result_dict
        return None
    
    @staticmethod
    def get_latest_completed_attempt(cursor: RealDictCursor, user_id: int, quiz_id: int) -> Optional[Dict]:
        """Get the latest completed attempt for a user and quiz
        
        CRITICAL: Returns ONLY attempts where completed_time IS NOT NULL.
        Orders by completed_time DESC to get the most recent completion.
        This is used by Results API to fetch completed test results.
        """
        query = """
            SELECT uqt.*, q.quiz_name, q.total_no_questions, q.difficulty_level
            FROM "User_Quiz_Take" uqt
            JOIN "Quiz" q ON uqt.quiz_id = q.quiz_id
            WHERE uqt.user_id = %s 
                AND uqt.quiz_id = %s
                AND uqt.completed_time IS NOT NULL
            ORDER BY uqt.completed_time DESC
            LIMIT 1
        """
        cursor.execute(query, (user_id, quiz_id))
        result = cursor.fetchone()
        if result:
            result_dict = dict(result)
            result_dict["status"] = TestModel._compute_status(result_dict.get("start_time"), result_dict.get("completed_time"))
            return result_dict
        return None
    
    @staticmethod
    def get_pending_test_for_quiz(cursor: RealDictCursor, user_id: int, quiz_id: int, assignment_id: Optional[int] = None) -> Optional[Dict]:
        """Get existing pending test for a quiz (if any)
        
        CRITICAL: Uses completed_time as single source of truth.
        Returns test ONLY if completed_time IS NULL (not yet completed).
        """
        if assignment_id is not None:
            # Check for pending test with matching assignment
            query = """
                SELECT uqt_id, user_id, quiz_id, start_time, completed_time, total_correct, result, quiz_assignment_id
                FROM "User_Quiz_Take"
                WHERE user_id = %s 
                    AND quiz_id = %s 
                    AND quiz_assignment_id = %s
                    AND completed_time IS NULL
                ORDER BY 
                    CASE 
                        WHEN start_time IS NULL THEN 0
                        ELSE 1
                    END,
                    start_time DESC NULLS LAST
                LIMIT 1
            """
            cursor.execute(query, (user_id, quiz_id, assignment_id))
        else:
            # Check for pending test without assignment (NULL assignment)
            query = """
                SELECT uqt_id, user_id, quiz_id, start_time, completed_time, total_correct, result, quiz_assignment_id
                FROM "User_Quiz_Take"
                WHERE user_id = %s 
                    AND quiz_id = %s 
                    AND quiz_assignment_id IS NULL
                    AND completed_time IS NULL
                ORDER BY 
                    CASE 
                        WHEN start_time IS NULL THEN 0
                        ELSE 1
                    END,
                    start_time DESC NULLS LAST
                LIMIT 1
            """
            cursor.execute(query, (user_id, quiz_id))
        
        result = cursor.fetchone()
        if result:
            result_dict = dict(result)
            result_dict["status"] = TestModel._compute_status(result_dict.get("start_time"), result_dict.get("completed_time"))
            return result_dict
        return None
    
    @staticmethod
    def update_test_to_in_progress(cursor: RealDictCursor, uqt_id: int) -> Optional[Dict]:
        """Update a NOT_STARTED test to IN_PROGRESS by setting start_time"""
        query = """
            UPDATE "User_Quiz_Take"
            SET start_time = NOW()
            WHERE uqt_id = %s 
                AND start_time IS NULL
                AND completed_time IS NULL
            RETURNING uqt_id, user_id, quiz_id, start_time, completed_time, quiz_assignment_id
        """
        cursor.execute(query, (uqt_id,))
        result = cursor.fetchone()
        if result:
            result_dict = dict(result)
            result_dict["status"] = TestModel._compute_status(result_dict.get("start_time"), result_dict.get("completed_time"))
            return result_dict
        return None
    
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
            ORDER BY uqt.start_time DESC NULLS LAST
        """
        cursor.execute(query, (user_id,))
        results = []
        for row in cursor.fetchall():
            result = dict(row)
            result["status"] = TestModel._compute_status(result.get("start_time"), result.get("completed_time"))
            results.append(result)
        return results
    
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
        """Get all pending tests for a user
        
        CRITICAL: Uses completed_time as single source of truth.
        Returns ALL tests where completed_time IS NULL (not yet completed).
        This includes both NOT_STARTED (start_time IS NULL) and IN_PROGRESS (start_time IS NOT NULL) tests.
        """
        # CRITICAL: Filter ONLY by completed_time IS NULL - this is the single source of truth
        query = """
            SELECT 
                uqt.uqt_id,
                uqt.user_id,
                uqt.start_time,
                uqt.completed_time,
                uqt.total_correct,
                uqt.result,
                uqt.quiz_assignment_id,
                q.quiz_id,
                q.quiz_name,
                q.total_no_questions,
                q.difficulty_level
            FROM "User_Quiz_Take" uqt
            INNER JOIN "Quiz" q ON uqt.quiz_id = q.quiz_id
            WHERE uqt.user_id = %s 
                AND uqt.completed_time IS NULL
            ORDER BY 
                CASE 
                    WHEN uqt.start_time IS NULL THEN 0
                    ELSE 1
                END,
                uqt.start_time DESC NULLS LAST
        """
        cursor.execute(query, (user_id,))
        raw_results = cursor.fetchall()
        
        results = []
        for row in raw_results:
            result = dict(row)
            start_time = result.get("start_time")
            completed_time = result.get("completed_time")
            
            # MANDATORY: Compute status from database values
            computed_status = TestModel._compute_status(start_time, completed_time)
            result["status"] = computed_status
            
            # MANDATORY: Include ALL tests where completed_time IS NULL
            # Both NOT_STARTED and IN_PROGRESS must be included
            results.append(result)
        
        return results
    
    @staticmethod
    def delete_quiz_take(cursor: RealDictCursor, uqt_id: int, user_id: int) -> bool:
        """Delete a quiz take (pending test)
        
        CRITICAL: Uses completed_time as single source of truth.
        Only deletes if completed_time IS NULL (not yet completed) and belongs to user.
        """
        query = """
            DELETE FROM "User_Quiz_Take"
            WHERE uqt_id = %s 
                AND user_id = %s
                AND completed_time IS NULL
        """
        cursor.execute(query, (uqt_id, user_id))
        return cursor.rowcount > 0
    
    @staticmethod
    def get_completed_tests(cursor: RealDictCursor, user_id: int) -> List[Dict]:
        """Get all completed tests for a user
        
        CRITICAL: Uses completed_time as single source of truth.
        Returns ALL tests where completed_time IS NOT NULL (test has been submitted).
        """
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
        print(f"[MODEL] get_completed_tests querying with user_id: {user_id}")
        cursor.execute(query, (user_id,))
        raw_results = cursor.fetchall()
        print(f"[MODEL] get_completed_tests raw query returned {len(raw_results)} rows")
        results = []
        for row in raw_results:
            result = dict(row)
            result["status"] = TestModel._compute_status(result.get("start_time"), result.get("completed_time"))
            results.append(result)
        print(f"[MODEL] get_completed_tests final results count: {len(results)}")
        if results:
            print(f"[MODEL] Sample completed test: {results[0]}")
        return results
    
    @staticmethod
    def delete_all_pending_tests(cursor: RealDictCursor, user_id: int) -> int:
        """Delete all pending tests for a user"""
        query = """
            DELETE FROM "User_Quiz_Take"
            WHERE user_id = %s 
                AND completed_time IS NULL
                AND start_time IS NOT NULL
        """
        cursor.execute(query, (user_id,))
        return cursor.rowcount
    
    @staticmethod
    def delete_all_completed_tests(cursor: RealDictCursor, user_id: int) -> int:
        """Delete all completed tests for a user"""
        query = """
            DELETE FROM "User_Quiz_Take"
            WHERE user_id = %s 
                AND completed_time IS NOT NULL
        """
        cursor.execute(query, (user_id,))
        return cursor.rowcount
    
    @staticmethod
    def delete_pending_tests_by_ids(cursor: RealDictCursor, uqt_ids: List[int], user_id: int) -> int:
        """Delete specific pending tests by IDs - only if they belong to user and are pending"""
        if not uqt_ids:
            return 0
        
        # Use parameterized query with tuple for IN clause
        placeholders = ','.join(['%s'] * len(uqt_ids))
        query = f"""
            DELETE FROM "User_Quiz_Take"
            WHERE uqt_id IN ({placeholders})
                AND user_id = %s
                AND completed_time IS NULL
                AND start_time IS NOT NULL
        """
        cursor.execute(query, tuple(uqt_ids) + (user_id,))
        return cursor.rowcount
    
    @staticmethod
    def delete_completed_tests_by_ids(cursor: RealDictCursor, uqt_ids: List[int], user_id: int) -> int:
        """Delete specific completed tests by IDs - only if they belong to user and are completed"""
        if not uqt_ids:
            return 0
        
        # Use parameterized query with tuple for IN clause
        placeholders = ','.join(['%s'] * len(uqt_ids))
        query = f"""
            DELETE FROM "User_Quiz_Take"
            WHERE uqt_id IN ({placeholders})
                AND user_id = %s
                AND completed_time IS NOT NULL
        """
        cursor.execute(query, tuple(uqt_ids) + (user_id,))
        return cursor.rowcount

