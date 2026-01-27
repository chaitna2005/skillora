"""
Run migration to add resume test support
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from app.config import settings

def run_migration():
    """Run the resume test migration"""
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=settings.DATABASE_HOST,
            port=settings.DATABASE_PORT,
            database=settings.DATABASE_NAME,
            user=settings.DATABASE_USER,
            password=settings.DATABASE_PASSWORD
        )
        conn.autocommit = False
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("Connected to database successfully")
        
        # Read migration SQL
        with open('../database/migration_add_resume_test.sql', 'r') as f:
            migration_sql = f.read()
        
        print("Executing migration...")
        cursor.execute(migration_sql)
        conn.commit()
        
        print("Migration completed successfully!")
        print("Added current_question_index column to User_Quiz_Take table")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Migration failed: {e}")
        if conn:
            conn.rollback()
        raise

if __name__ == "__main__":
    run_migration()
