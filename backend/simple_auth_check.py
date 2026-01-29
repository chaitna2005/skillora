"""
Standalone Authentication Check (no app imports)
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib

# DB config
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "testmyknowledge"
DB_USER = "postgres"
DB_PASSWORD = "Ch@itu_password2005!"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain, hashed):
    return hash_password(plain) == hashed

print("="*60)
print("STANDALONE AUTH CHECK")
print("="*60)

try:
    # Connect
    print("\n1. Connecting to database...")
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    print("   [OK] Connected")
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Check User table
    print("\n2. Checking User table...")
    cursor.execute('SELECT COUNT(*) as count FROM "User"')
    count = cursor.fetchone()['count']
    print(f"   [OK] Found {count} users")
    
    # Check columns
    cursor.execute("""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = 'User'
        ORDER BY ordinal_position
    """)
    cols = cursor.fetchall()
    print("   Columns:")
    for c in cols:
        maxlen = f"({c['character_maximum_length']})" if c['character_maximum_length'] else ""
        print(f"     - {c['column_name']}: {c['data_type']}{maxlen}")
    
    # Test password hashing
    print("\n3. Testing password hashing...")
    test_pwd = "password"
    hashed = hash_password(test_pwd)
    print(f"   Plain: {test_pwd}")
    print(f"   Hash: {hashed}")
    print(f"   Hash length: {len(hashed)}")
    print(f"   Verification: {verify_password(test_pwd, hashed)}")
    
    # Test registration
    print("\n4. Testing user creation...")
    import time
    test_username = f"debuguser_{int(time.time())}"
    test_email = f"{test_username}@test.com"
    test_password = "TestPass123"
    
    try:
        cursor.execute("""
            INSERT INTO "User" (first_name, last_name, username, password, email_id, role)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING user_id, username, email_id
        """, ("Debug", "User", test_username, hash_password(test_password), test_email, "STUDENT"))
        
        new_user = cursor.fetchone()
        conn.commit()
        
        print(f"   [OK] User created:")
        print(f"     ID: {new_user['user_id']}")
        print(f"     Username: {new_user['username']}")
        print(f"     Email: {new_user['email_id']}")
        
        # Verify it's in DB
        cursor.execute('SELECT * FROM "User" WHERE username = %s', (test_username,))
        saved_user = cursor.fetchone()
        
        if saved_user:
            print(f"   [OK] User found in DB after commit")
            
            # Test password
            pwd_match = verify_password(test_password, saved_user['password'])
            print(f"   Password match: {pwd_match}")
            
            if pwd_match:
                print(f"\n[SUCCESS] Full registration+login flow works!")
            else:
                print(f"\n[ERROR] Password verification failed!")
                print(f"     Stored: {saved_user['password']}")
                print(f"     Expected: {hash_password(test_password)}")
        
    except Exception as reg_err:
        conn.rollback()
        print(f"   [ERROR] Registration failed: {reg_err}")
        import traceback
        traceback.print_exc()
    
    # List existing users
    print(f"\n5. Existing users:")
    cursor.execute('SELECT user_id, username, email_id, role, LENGTH(password) as pwd_len FROM "User" ORDER BY user_id LIMIT 5')
    users = cursor.fetchall()
    for u in users:
        print(f"   ID:{u['user_id']} | {u['username']} | {u['email_id']} | {u['role']} | PwdLen:{u['pwd_len']}")
    
    cursor.close()
    conn.close()
    
    print(f"\n" + "="*60)
    print("[COMPLETE] Check results above")
    print("="*60)
    
except Exception as e:
    print(f"\n[CRITICAL ERROR] {e}")
    import traceback
    traceback.print_exc()
