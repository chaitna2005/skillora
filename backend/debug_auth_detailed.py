"""
Detailed Authentication System Debugging
This script traces the exact failure point
"""
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("AUTHENTICATION SYSTEM DETAILED DEBUG")
print("=" * 80)

# Step 1: Check .env file
print("\n[STEP 1] Checking .env configuration...")
try:
    # Load .env file manually first
    from dotenv import load_dotenv
    import os
    
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    print(f"   Looking for .env at: {env_path}")
    
    if os.path.exists(env_path):
        print(f"   .env file exists: YES")
        load_dotenv(env_path)
    else:
        print(f"   .env file exists: NO")
        print(f"   Trying parent directory...")
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend', '.env')
        if os.path.exists(env_path):
            print(f"   Found .env at: {env_path}")
            load_dotenv(env_path)
    
    from app.config import settings
    print(f"   DATABASE_HOST: {settings.DATABASE_HOST}")
    print(f"   DATABASE_PORT: {settings.DATABASE_PORT}")
    print(f"   DATABASE_NAME: {settings.DATABASE_NAME}")
    print(f"   DATABASE_USER: {settings.DATABASE_USER}")
    print(f"   DATABASE_PASSWORD: {'*' * 10}")
except Exception as e:
    print(f"X Failed to load settings: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 2: Test database connection
print("\n[STEP 2] Testing database connection...")
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    conn = psycopg2.connect(
        host=settings.DATABASE_HOST,
        port=settings.DATABASE_PORT,
        database=settings.DATABASE_NAME,
        user=settings.DATABASE_USER,
        password=settings.DATABASE_PASSWORD
    )
    print("✅ Database connection successful")
    
    # Check if User table exists
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'User'
        )
    """)
    table_exists = cursor.fetchone()['exists']
    
    if not table_exists:
        print("❌ CRITICAL: 'User' table does NOT exist!")
        print("   Run: psql -U postgres -d testmyknowledge -f database/schema.sql")
        cursor.close()
        conn.close()
        sys.exit(1)
    else:
        print("✅ 'User' table exists")
    
    # Check table structure
    cursor.execute("""
        SELECT column_name, data_type, character_maximum_length, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'User'
        ORDER BY ordinal_position
    """)
    columns = cursor.fetchall()
    
    print("\n   User Table Structure:")
    for col in columns:
        nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
        max_len = f"({col['character_maximum_length']})" if col['character_maximum_length'] else ""
        print(f"   - {col['column_name']}: {col['data_type']}{max_len} {nullable}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Database error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 3: Test password hashing
print("\n[STEP 3] Testing password hashing...")
try:
    from app.utils.auth import hash_password, verify_password
    
    test_password = "testpass123"
    hashed = hash_password(test_password)
    
    print(f"✅ Plain password: {test_password}")
    print(f"✅ Hashed password: {hashed}")
    print(f"✅ Hash length: {len(hashed)} characters")
    
    # Test verification
    is_valid = verify_password(test_password, hashed)
    is_invalid = verify_password("wrongpass", hashed)
    
    if is_valid and not is_invalid:
        print(f"✅ Password verification works correctly")
    else:
        print(f"❌ Password verification BROKEN: valid={is_valid}, invalid={is_invalid}")
        
except Exception as e:
    print(f"❌ Password hashing failed: {e}")
    import traceback
    traceback.print_exc()

# Step 4: Count existing users
print("\n[STEP 4] Checking existing users...")
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
    count = cursor.fetchone()['count']
    
    print(f"✅ Total users in database: {count}")
    
    if count > 0:
        cursor.execute("""
            SELECT user_id, username, email_id, role, 
                   LENGTH(password) as password_length
            FROM "User"
            ORDER BY user_id
            LIMIT 5
        """)
        users = cursor.fetchall()
        
        print("   Sample users:")
        for u in users:
            print(f"   - ID:{u['user_id']} | User:{u['username']} | Email:{u['email_id']} | Role:{u['role']} | PwdLen:{u['password_length']}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Failed to query users: {e}")

# Step 5: Test complete registration flow
print("\n[STEP 5] Testing registration flow (manual simulation)...")
try:
    from app.models.user import UserModel
    from app.utils.auth import hash_password
    import time
    
    conn = psycopg2.connect(
        host=settings.DATABASE_HOST,
        port=settings.DATABASE_PORT,
        database=settings.DATABASE_NAME,
        user=settings.DATABASE_USER,
        password=settings.DATABASE_PASSWORD
    )
    conn.autocommit = False
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Simulate registration
    test_user = f"diagtest_{int(time.time())}"
    test_email = f"{test_user}@test.com"
    test_password = "TestPass123!"
    
    print(f"   Creating test user: {test_user}")
    
    # Hash password
    hashed_pwd = hash_password(test_password)
    print(f"   Password hashed: {hashed_pwd[:20]}... (length: {len(hashed_pwd)})")
    
    # Create user data
    user_data = {
        "first_name": "Test",
        "last_name": "User",
        "username": test_user,
        "password": hashed_pwd,
        "email_id": test_email,
        "role": "STUDENT"
    }
    
    # Insert
    print("   Executing INSERT...")
    created_user = UserModel.create_user(cursor, user_data)
    
    print(f"   User object returned: {created_user}")
    
    # Commit
    print("   Committing transaction...")
    conn.commit()
    print("   ✅ COMMIT successful")
    
    # Verify user was saved
    cursor.execute('SELECT * FROM "User" WHERE username = %s', (test_user,))
    saved_user = cursor.fetchone()
    
    if saved_user:
        print(f"   ✅ User saved to DB: ID={saved_user['user_id']}, Username={saved_user['username']}")
        
        # Test login/password verification
        print(f"\n   Testing password verification for saved user...")
        stored_hash = saved_user['password']
        print(f"   Stored hash: {stored_hash[:20]}...")
        
        is_valid = verify_password(test_password, stored_hash)
        print(f"   Password verification: {is_valid}")
        
        if is_valid:
            print("   ✅ Registration and login flow works!")
        else:
            print("   ❌ Password verification FAILED after save")
    else:
        print("   ❌ User NOT found in DB after commit")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"   ❌ Registration test failed: {e}")
    import traceback
    traceback.print_exc()
    if 'conn' in locals():
        conn.rollback()

# Step 6: Test login with existing user
print("\n[STEP 6] Testing login with existing user (if any)...")
try:
    conn = psycopg2.connect(
        host=settings.DATABASE_HOST,
        port=settings.DATABASE_PORT,
        database=settings.DATABASE_NAME,
        user=settings.DATABASE_USER,
        password=settings.DATABASE_PASSWORD
    )
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get first user
    cursor.execute('SELECT * FROM "User" ORDER BY user_id LIMIT 1')
    first_user = cursor.fetchone()
    
    if first_user:
        print(f"   Testing with user: {first_user['username']}")
        print(f"   Stored password hash: {first_user['password'][:30]}...")
        print(f"   Hash length: {len(first_user['password'])}")
        
        # Try to verify with "password" (common default)
        test_passwords = ["password", "Password", "password123", "testpass"]
        
        for pwd in test_passwords:
            is_match = verify_password(pwd, first_user['password'])
            if is_match:
                print(f"   ✅ Password '{pwd}' matches for {first_user['username']}")
                break
        else:
            print(f"   ⚠️ None of the test passwords matched")
            print(f"   Note: If this is an old user, password may be stored differently")
    else:
        print("   No users in database to test")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"   ❌ Login test failed: {e}")

print("\n" + "=" * 80)
print("DEBUG COMPLETE - Check output above for issues")
print("=" * 80)
