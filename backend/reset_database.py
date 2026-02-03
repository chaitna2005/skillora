"""
Database Reset Script
Drops and recreates all tables with the updated schema
WARNING: This will delete ALL data in the database!
"""
import psycopg2
from app.config import settings
import sys


def reset_database():
    """Drop and recreate database tables"""
    try:
        print("=" * 60)
        print("DATABASE RESET SCRIPT")
        print("=" * 60)
        print("\n⚠️  WARNING: This will DELETE ALL DATA in the database!")
        print("\nDatabase:", settings.DATABASE_NAME)
        print("Host:", settings.DATABASE_HOST)
        
        response = input("\nType 'YES' to continue: ")
        if response != 'YES':
            print("\n❌ Database reset cancelled.")
            sys.exit(0)
        
        # Connect to database
        print("\n🔌 Connecting to database...")
        conn = psycopg2.connect(
            host=settings.DATABASE_HOST,
            port=settings.DATABASE_PORT,
            database=settings.DATABASE_NAME,
            user=settings.DATABASE_USER,
            password=settings.DATABASE_PASSWORD
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # First, drop all tables forcefully
        print("🗑️  Dropping existing tables...")
        drop_tables_sql = """
        DROP TABLE IF EXISTS "Quiz_Take_Question_Answers" CASCADE;
        DROP TABLE IF EXISTS "User_Quiz_Take" CASCADE;
        DROP TABLE IF EXISTS "QuestionOption" CASCADE;
        DROP TABLE IF EXISTS "Question" CASCADE;
        DROP TABLE IF EXISTS "Quiz_Assignment" CASCADE;
        DROP TABLE IF EXISTS "Quiz" CASCADE;
        DROP TABLE IF EXISTS "Example_Prompt" CASCADE;
        DROP TABLE IF EXISTS "User_Stats" CASCADE;
        DROP TABLE IF EXISTS "User" CASCADE;
        """
        cursor.execute(drop_tables_sql)
        print("  ✓ All tables dropped")
        
        # Read schema file
        print("📄 Reading schema file...")
        with open('../database/schema.sql', 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # Execute schema (create tables)
        print("🏗️  Creating new tables with updated schema...")
        cursor.execute(schema_sql)
        
        print("\n✅ Database reset completed successfully!")
        print("\nNew schema changes:")
        print("  • Username column: VARCHAR(150) ✓")
        print("  • Password column: VARCHAR(255) ✓")
        print("  • All tables recreated")
        
        # Close connection
        cursor.close()
        conn.close()
        
        print("\n⚠️  IMPORTANT: You must register new users.")
        print("   Old password hashes are incompatible with the new system.")
        
    except FileNotFoundError:
        print("\n❌ Error: schema.sql file not found!")
        print("   Expected location: ../database/schema.sql")
        sys.exit(1)
    except psycopg2.Error as e:
        print(f"\n❌ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    reset_database()
