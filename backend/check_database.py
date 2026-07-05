"""
Database Diagnostic Script
Verifies database connection, tables, and schema
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from app.config import settings


def check_database():
    """Check database connection and tables"""
    
    print("=" * 80)
    print("DATABASE DIAGNOSTIC CHECK")
    print("=" * 80)
    
    # Print connection details
    print("\n1. DATABASE CONFIGURATION:")
    print(f"   Host: {settings.DATABASE_HOST}")
    print(f"   Port: {settings.DATABASE_PORT}")
    print(f"   Database: {settings.DATABASE_NAME}")
    print(f"   User: {settings.DATABASE_USER}")
    print(f"   Full URI: {settings.database_url}")
    
    # Try to connect
    print("\n2. TESTING CONNECTION:")
    try:
        conn = psycopg2.connect(
            host=settings.DATABASE_HOST,
            port=settings.DATABASE_PORT,
            database=settings.DATABASE_NAME,
            user=settings.DATABASE_USER,
            password=settings.DATABASE_PASSWORD
        )
        print("   ✅ Connection successful!")
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check PostgreSQL version
        cursor.execute("SELECT version()")
        version = cursor.fetchone()
        print(f"   PostgreSQL version: {version['version'][:50]}...")
        
        # List all tables
        print("\n3. TABLES IN DATABASE:")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        
        if tables:
            for table in tables:
                print(f"   ✅ {table['table_name']}")
        else:
            print("   ❌ NO TABLES FOUND!")
            print("   → Run: python reset_database.py")
        
        # Check User table structure
        print("\n4. USER TABLE STRUCTURE:")
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'User'
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        
        if columns:
            print("   ✅ User table exists")
            for col in columns:
                length = f"({col['character_maximum_length']})" if col['character_maximum_length'] else ""
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                print(f"   - {col['column_name']}: {col['data_type']}{length} {nullable}")
        else:
            print("   ❌ User table does NOT exist!")
            print("   → Run: python reset_database.py")
        
        # Check if User table has any rows
        print("\n5. USER TABLE DATA:")
        try:
            cursor.execute('SELECT COUNT(*) as count FROM "User"')
            count = cursor.fetchone()
            user_count = count['count']
            print(f"   User count: {user_count}")
            
            if user_count > 0:
                cursor.execute('SELECT user_id, username, email_id, role FROM "User" LIMIT 5')
                users = cursor.fetchall()
                print("   Recent users:")
                for user in users:
                    print(f"   - ID {user['user_id']}: {user['username']} ({user['email_id']}) - {user['role']}")
            else:
                print("   ℹ️  No users in database yet")
        except Exception as e:
            print(f"   ❌ Cannot query User table: {e}")
        
        # Test INSERT capability
        print("\n6. DATABASE WRITE TEST:")
        try:
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            print(f"   ✅ Database is readable (test query returned: {result['test']})")
            
            # Check if we can write (rollback after)
            cursor.execute("BEGIN")
            cursor.execute("SELECT COUNT(*) FROM \"User\"")
            cursor.execute("ROLLBACK")
            print("   ✅ Database is writable (transaction test passed)")
        except Exception as e:
            print(f"   ❌ Database write test failed: {e}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 80)
        print("DIAGNOSTIC COMPLETE")
        print("=" * 80)
        
        if not tables:
            print("\n⚠️  ACTION REQUIRED: Run 'python reset_database.py' to create tables")
        
    except psycopg2.OperationalError as e:
        print(f"   ❌ Connection failed!")
        print(f"   Error: {e}")
        print("\n   Possible issues:")
        print("   - PostgreSQL is not running")
        print("   - Wrong host/port in .env file")
        print("   - Database does not exist")
        print("   - Wrong username/password")
        
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        check_database()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
