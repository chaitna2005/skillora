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
        try:
            query = """
                INSERT INTO "User" (first_name, last_name, username, password, email_id, role)
                VALUES (%(first_name)s, %(last_name)s, %(username)s, %(password)s, %(email_id)s, %(role)s)
                RETURNING user_id, first_name, last_name, username, email_id, role, created_at
            """
            print(f"[USER_MODEL] Executing INSERT for username: {user_data.get('username')}")
            cursor.execute(query, user_data)
            result = cursor.fetchone()
            if result:
                print(f"[USER_MODEL] User created successfully: {dict(result)}")
                return dict(result)
            else:
                print(f"[USER_MODEL ERROR] INSERT returned no result")
                return None
        except Exception as e:
            print(f"[USER_MODEL ERROR] Failed to create user: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    @staticmethod
    def get_user_by_username(cursor: RealDictCursor, username: str) -> Optional[Dict]:
        """Get user by username"""
        try:
            query = """
                SELECT user_id, first_name, last_name, username, password, email_id, role, created_at
                FROM "User"
                WHERE username = %s
            """
            cursor.execute(query, (username,))
            result = cursor.fetchone()
            if result:
                print(f"[USER_MODEL] Found user: {username}, ID: {result['user_id']}")
                return dict(result)
            else:
                print(f"[USER_MODEL] User not found: {username}")
                return None
        except Exception as e:
            print(f"[USER_MODEL ERROR] Failed to fetch user {username}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def get_user_by_id(cursor: RealDictCursor, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        query = """
            SELECT user_id, first_name, last_name, username, email_id, role, created_at
            FROM "User"
            WHERE user_id = %s
        """
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        return dict(result) if result else None
    
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

