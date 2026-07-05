"""
Test Authentication System
Diagnostic script to verify registration and login functionality
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from app.config import settings
from app.utils.auth import hash_password, verify_password

def test_database_connection():
    """Test database connection"""
    try:
        conn = psycopg2.connect(
            host=settings.DATABASE_HOST,
            port=settings.DATABASE_PORT,
            database=settings.DATABASE_NAME,
            user=settings.DATABASE_USER,
            password=settings.DATABASE_PASSWORD
        )
        print("✅ Database connection successful")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_user_table_structure():
    """Check User table structure"""
    try:
        conn = psycopg2.connect(
            host=settings.DATABASE_HOST,
            port=settings.DATABASE_PORT,
            database=settings.DATABASE_NAME,
            user=settings.DATABASE_USER,
            password=settings.DATABASE_PASSWORD
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check table structure
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'User'
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        
        print("\n✅ User Table Structure:")
        for col in columns:
            print(f"   {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Failed to check User table: {e}")
        return False

def test_password_hashing():
    """Test password hashing functions"""
    try:
        test_password = "testpassword123"
        
        # Hash password
        hashed = hash_password(test_password)
        print(f"\n✅ Password Hashing Test:")
        print(f"   Plain: {test_password}")
        print(f"   Hash: {hashed}")
        
        # Verify correct password
        is_valid = verify_password(test_password, hashed)
        print(f"   Verify correct password: {is_valid}")
        
        # Verify wrong password
        is_invalid = verify_password("wrongpassword", hashed)
        print(f"   Verify wrong password: {is_invalid}")
        
        if is_valid and not is_invalid:
            print("✅ Password hashing works correctly")
            return True
        else:
            print("❌ Password hashing issue detected")
            return False
    except Exception as e:
        print(f"❌ Password hashing test failed: {e}")
        return False

def test_existing_users():
    """Check existing users in database"""
    try:
        conn = psycopg2.connect(
            host=settings.DATABASE_HOST,
            port=settings.DATABASE_PORT,
            database=settings.DATABASE_NAME,
            user=settings.DATABASE_USER,
            password=settings.DATABASE_PASSWORD
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute('SELECT COUNT(*) as count FROM "User"')
        count_result = cursor.fetchone()
        total_users = count_result['count'] if count_result else 0
        
        print(f"\n✅ Found {total_users} users in database")
        
        # Get first 5 users
        cursor.execute("""
            SELECT user_id, username, email_id, role, created_at
            FROM "User"
            ORDER BY user_id
            LIMIT 5
        """)
        users = cursor.fetchall()
        
        if users:
            print("   Sample users:")
            for user in users:
                print(f"   - ID: {user['user_id']}, Username: {user['username']}, Email: {user['email_id']}, Role: {user['role']}")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Failed to check existing users: {e}")
        return False

def test_registration_manually():
    """Test user registration manually"""
    try:
        conn = psycopg2.connect(
            host=settings.DATABASE_HOST,
            port=settings.DATABASE_PORT,
            database=settings.DATABASE_NAME,
            user=settings.DATABASE_USER,
            password=settings.DATABASE_PASSWORD
        )
        conn.autocommit = False
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Create test user
        test_username = f"testuser_{int(__import__('time').time())}"
        test_password = "testpass123"
        hashed = hash_password(test_password)
        
        user_data = {
            "first_name": "Test",
            "last_name": "User",
            "username": test_username,
            "password": hashed,
            "email_id": f"{test_username}@test.com",
            "role": "STUDENT"
        }
        
        cursor.execute("""
            INSERT INTO "User" (first_name, last_name, username, password, email_id, role)
            VALUES (%(first_name)s, %(last_name)s, %(username)s, %(password)s, %(email_id)s, %(role)s)
            RETURNING user_id, username
        """, user_data)
        
        result = cursor.fetchone()
        conn.commit()
        
        print(f"\n✅ Test Registration Successful:")
        print(f"   User ID: {result['user_id']}")
        print(f"   Username: {result['username']}")
        
        # Test login with this user
        cursor.execute("""
            SELECT user_id, username, password
            FROM "User"
            WHERE username = %s
        """, (test_username,))
        
        user = cursor.fetchone()
        if user:
            login_valid = verify_password(test_password, user['password'])
            print(f"   Login test: {'✅ PASS' if login_valid else '❌ FAIL'}")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Test registration failed: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("AUTHENTICATION SYSTEM DIAGNOSTIC")
    print("=" * 60)
    
    # Run tests
    db_ok = test_database_connection()
    table_ok = test_user_table_structure() if db_ok else False
    hash_ok = test_password_hashing()
    users_ok = test_existing_users() if db_ok else False
    reg_ok = test_registration_manually() if db_ok else False
    
    print("\n" + "=" * 60)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 60)
    print(f"Database Connection: {'✅ OK' if db_ok else '❌ FAILED'}")
    print(f"User Table Structure: {'✅ OK' if table_ok else '❌ FAILED'}")
    print(f"Password Hashing: {'✅ OK' if hash_ok else '❌ FAILED'}")
    print(f"Existing Users: {'✅ OK' if users_ok else '❌ FAILED'}")
    print(f"Test Registration: {'✅ OK' if reg_ok else '❌ FAILED'}")
    print("=" * 60)
    
    if all([db_ok, table_ok, hash_ok, reg_ok]):
        print("\n✅ ALL TESTS PASSED - Authentication system is working!")
    else:
        print("\n❌ SOME TESTS FAILED - Check errors above for details")
