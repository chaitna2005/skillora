"""
Example Prompt Model
Handles example prompt database operations
"""
from typing import Optional, Dict, Any, List
from psycopg2.extras import RealDictCursor


class ExamplePromptModel:
    
    @staticmethod
    def create_prompt(cursor: RealDictCursor, prompt_data: Dict[str, Any]) -> Optional[Dict]:
        """Create a new example prompt"""
        query = """
            INSERT INTO "Example_Prompt" (prompt_text, created_by, usage_count, is_active, created_at)
            VALUES (%(prompt_text)s, %(created_by)s, 0, TRUE, NOW())
            RETURNING prompt_id, prompt_text, created_by, usage_count, is_active, created_at
        """
        cursor.execute(query, prompt_data)
        return dict(cursor.fetchone())
    
    @staticmethod
    def get_prompt_by_text(cursor: RealDictCursor, prompt_text: str) -> Optional[Dict]:
        """Get prompt by text"""
        query = """
            SELECT prompt_id, prompt_text, created_by, usage_count, is_active, created_at
            FROM "Example_Prompt"
            WHERE prompt_text = %s
        """
        cursor.execute(query, (prompt_text,))
        result = cursor.fetchone()
        return dict(result) if result else None
    
    @staticmethod
    def get_active_prompts(cursor: RealDictCursor) -> List[Dict]:
        """Get all active example prompts ordered by usage_count DESC, created_at DESC"""
        query = """
            SELECT prompt_id, prompt_text, created_by, usage_count, is_active, created_at
            FROM "Example_Prompt"
            WHERE is_active = TRUE
            ORDER BY usage_count DESC, created_at DESC
        """
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_user_prompts(cursor: RealDictCursor, user_id: int) -> List[Dict]:
        """Get active example prompts created by a specific user"""
        query = """
            SELECT prompt_id, prompt_text, created_by, usage_count, is_active, created_at
            FROM "Example_Prompt"
            WHERE is_active = TRUE AND created_by = %s
            ORDER BY usage_count DESC, created_at DESC
        """
        cursor.execute(query, (user_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def increment_usage_count(cursor: RealDictCursor, prompt_id: int) -> Optional[Dict]:
        """Increment usage_count for a prompt"""
        query = """
            UPDATE "Example_Prompt"
            SET usage_count = usage_count + 1
            WHERE prompt_id = %s
            RETURNING prompt_id, prompt_text, created_by, usage_count, is_active, created_at
        """
        cursor.execute(query, (prompt_id,))
        result = cursor.fetchone()
        return dict(result) if result else None

