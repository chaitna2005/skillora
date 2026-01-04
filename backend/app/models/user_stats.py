"""
User Stats Model
Handles user stats (badges and streaks) database operations
"""
from typing import Optional, Dict, List
from psycopg2.extras import RealDictCursor
from datetime import date


class UserStatsModel:
    """Model for User_Stats table operations"""
    
    @staticmethod
    def get_user_stats(cursor: RealDictCursor, user_id: int) -> Optional[Dict]:
        """Get user stats (badges and streaks)"""
        query = """
            SELECT user_id, quiz_completion_count, current_streak, longest_streak, 
                   last_active_date, unlocked_badges, created_at, updated_at
            FROM "User_Stats"
            WHERE user_id = %s
        """
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        return dict(result) if result else None
    
    @staticmethod
    def create_user_stats(
        cursor: RealDictCursor,
        user_id: int,
        quiz_completion_count: int = 0,
        current_streak: int = 0,
        longest_streak: int = 0,
        last_active_date: Optional[date] = None,
        unlocked_badges: List[str] = None
    ) -> Optional[Dict]:
        """Create initial user stats record"""
        if unlocked_badges is None:
            unlocked_badges = []
        
        query = """
            INSERT INTO "User_Stats" 
                (user_id, quiz_completion_count, current_streak, longest_streak, 
                 last_active_date, unlocked_badges)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING user_id, quiz_completion_count, current_streak, longest_streak,
                      last_active_date, unlocked_badges, created_at, updated_at
        """
        cursor.execute(query, (
            user_id,
            quiz_completion_count,
            current_streak,
            longest_streak,
            last_active_date,
            unlocked_badges
        ))
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
            UPDATE "User_Stats"
            SET quiz_completion_count = %s,
                current_streak = %s,
                longest_streak = %s,
                last_active_date = %s,
                unlocked_badges = %s,
                updated_at = CURRENT_TIMESTAMP
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
    def get_or_create_user_stats(cursor: RealDictCursor, user_id: int) -> Dict:
        """Get user stats, creating default record if it doesn't exist"""
        stats = UserStatsModel.get_user_stats(cursor, user_id)
        if stats:
            return stats
        
        # Create default stats record
        default_stats = UserStatsModel.create_user_stats(
            cursor,
            user_id,
            quiz_completion_count=0,
            current_streak=0,
            longest_streak=0,
            last_active_date=None,
            unlocked_badges=[]
        )
        return default_stats if default_stats else {
            "user_id": user_id,
            "quiz_completion_count": 0,
            "current_streak": 0,
            "longest_streak": 0,
            "last_active_date": None,
            "unlocked_badges": []
        }

