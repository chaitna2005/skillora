"""
User Model
Handles user-related database operations
"""
from typing import Optional, Dict, Any, List
from psycopg2.extras import RealDictCursor
from datetime import date


class UserModel:
    
    @staticmethod
    def create_user(cursor: RealDictCursor, user_data: Dict[str, Any]) -> Optional[Dict]:
        """Create a new user"""
        query = """
            INSERT INTO "User" (first_name, last_name, username, password, email_id, role)
            VALUES (%(first_name)s, %(last_name)s, %(username)s, %(password)s, %(email_id)s, %(role)s)
            RETURNING user_id, first_name, last_name, username, email_id, role, created_at
        """
        cursor.execute(query, user_data)
        return dict(cursor.fetchone())
    
    @staticmethod
    def get_user_by_username(cursor: RealDictCursor, username: str) -> Optional[Dict]:
        """Get user by username"""
        query = """
            SELECT user_id, first_name, last_name, username, password, email_id, role, created_at
            FROM "User"
            WHERE username = %s
        """
        cursor.execute(query, (username,))
        result = cursor.fetchone()
        return dict(result) if result else None
    
    @staticmethod
    def get_user_by_id(cursor: RealDictCursor, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        query = """
            SELECT user_id, first_name, last_name, username, email_id, role, created_at,
                   quiz_completion_count, current_streak, longest_streak, last_active_date, unlocked_badges
            FROM "User"
            WHERE user_id = %s
        """
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        return dict(result) if result else None
    
    @staticmethod
    def get_user_stats(cursor: RealDictCursor, user_id: int) -> Optional[Dict]:
        """Get user stats (badges and streaks)"""
        query = """
            SELECT quiz_completion_count, current_streak, longest_streak, last_active_date, unlocked_badges
            FROM "User"
            WHERE user_id = %s
        """
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        return dict(result) if result else None
    
    @staticmethod
    def update_user_stats(
        cursor: RealDictCursor,
        user_id: int,
        quiz_completion_count: int,
        current_streak: int,
        longest_streak: int,
        last_active_date: date,
        unlocked_badges: List[str]
    ) -> bool:
        """Update user stats after quiz completion"""
        query = """
            UPDATE "User"
            SET quiz_completion_count = %s,
                current_streak = %s,
                longest_streak = %s,
                last_active_date = %s,
                unlocked_badges = %s
            WHERE user_id = %s
        """
        try:
            cursor.execute(query, (
                quiz_completion_count,
                current_streak,
                longest_streak,
                last_active_date,
                unlocked_badges,
                user_id
            ))
            return True
        except Exception as e:
            print(f"Error updating user stats: {e}")
            return False
    
    @staticmethod
    def get_user_by_email(cursor: RealDictCursor, email: str) -> Optional[Dict]:
        """Get user by email"""
        query = """
            SELECT user_id, first_name, last_name, username, email_id, role, created_at
            FROM "User"
            WHERE email_id = %s
        """
        cursor.execute(query, (email,))
        result = cursor.fetchone()
        return dict(result) if result else None

