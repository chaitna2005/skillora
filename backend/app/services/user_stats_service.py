"""
User Stats Service
Handles badge and streak logic for gamification
"""
from typing import List, Dict, Optional, Tuple
from datetime import date, timedelta, datetime
from psycopg2.extras import RealDictCursor
from app.models.user import UserModel


class UserStatsService:
    """Service for managing user badges and streaks"""
    
    # Badge definitions: {badge_id: {"name": str, "threshold": int}}
    BADGES = {
        "first_quiz": {
            "name": "First Quiz Completed",
            "threshold": 1
        },
        "five_quizzes": {
            "name": "5 Quizzes Completed",
            "threshold": 5
        },
        "ten_quizzes": {
            "name": "10 Quizzes Completed",
            "threshold": 10
        }
    }
    
    @staticmethod
    def calculate_streak(
        current_streak: int,
        last_active_date: Optional[date],
        today: date
    ) -> Tuple[int, int]:
        """Calculate updated streak based on last active date
        
        Returns:
            tuple: (new_current_streak, new_longest_streak)
        """
        if last_active_date is None:
            # First time completing a quiz
            return (1, 1)
        
        days_diff = (today - last_active_date).days
        
        if days_diff == 0:
            # Already completed a quiz today - don't increment streak
            return (current_streak, max(current_streak, current_streak))
        elif days_diff == 1:
            # Consecutive day - increment streak
            new_streak = current_streak + 1
            return (new_streak, max(new_streak, current_streak))
        else:
            # Streak broken - reset to 1
            return (1, max(1, current_streak))
    
    @staticmethod
    def get_unlocked_badges(
        current_badges: List[str],
        new_completion_count: int
    ) -> Tuple[List[str], List[str]]:
        """Determine newly unlocked badges
        
        Args:
            current_badges: List of already unlocked badge IDs
            new_completion_count: New total completion count after this quiz
        
        Returns:
            tuple: (all_unlocked_badges, newly_unlocked_badge_names)
        """
        all_unlocked = set(current_badges) if current_badges else set()
        newly_unlocked_names = []
        
        for badge_id, badge_info in UserStatsService.BADGES.items():
            if badge_id not in all_unlocked:
                if new_completion_count >= badge_info["threshold"]:
                    all_unlocked.add(badge_id)
                    newly_unlocked_names.append(badge_info["name"])
        
        return (list(all_unlocked), newly_unlocked_names)
    
    @staticmethod
    def update_stats_on_quiz_completion(
        cursor: RealDictCursor,
        user_id: int
    ) -> Dict[str, any]:
        """Update user stats after quiz completion
        
        This function:
        1. Gets current user stats
        2. Calculates new streak
        3. Increments completion count
        4. Determines newly unlocked badges
        5. Updates database
        
        Returns:
            dict with:
                - new_completion_count
                - new_current_streak
                - new_longest_streak
                - newly_unlocked_badges (list of badge names)
        """
        try:
            # Get current stats
            stats = UserModel.get_user_stats(cursor, user_id)
            if not stats:
                print(f"[WARN] User {user_id} not found for stats update")
                return {
                    "new_completion_count": 0,
                    "new_current_streak": 0,
                    "new_longest_streak": 0,
                    "newly_unlocked_badges": []
                }
            
            current_count = stats.get("quiz_completion_count", 0) or 0
            current_streak = stats.get("current_streak", 0) or 0
            longest_streak = stats.get("longest_streak", 0) or 0
            last_active = stats.get("last_active_date")
            current_badges = stats.get("unlocked_badges", []) or []
            
            # Convert last_active_date to date if it's a datetime
            if last_active and isinstance(last_active, datetime):
                last_active = last_active.date()
            
            # Calculate new values
            today = date.today()
            new_completion_count = current_count + 1
            
            # Calculate streak
            new_current_streak, new_longest_streak = UserStatsService.calculate_streak(
                current_streak,
                last_active,
                today
            )
            
            # Determine badges
            all_badges, newly_unlocked = UserStatsService.get_unlocked_badges(
                current_badges,
                new_completion_count
            )
            
            # Update database
            success = UserModel.update_user_stats(
                cursor,
                user_id,
                new_completion_count,
                new_current_streak,
                new_longest_streak,
                today,
                all_badges
            )
            
            if not success:
                print(f"[ERROR] Failed to update stats for user {user_id}")
            
            return {
                "new_completion_count": new_completion_count,
                "new_current_streak": new_current_streak,
                "new_longest_streak": new_longest_streak,
                "newly_unlocked_badges": newly_unlocked
            }
            
        except Exception as e:
            print(f"[ERROR] Error updating user stats: {e}")
            import traceback
            traceback.print_exc()
            return {
                "new_completion_count": 0,
                "new_current_streak": 0,
                "new_longest_streak": 0,
                "newly_unlocked_badges": []
            }

