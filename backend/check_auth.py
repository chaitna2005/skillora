"""
Simple Authentication System Check
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv('.env')

import psycopg2
from psycopg2.extras import RealDictCursor
from app.utils.auth import hash_password, verify_password
import os

print("="*60)
print("AUTHENTICATION DEBUG")
print("="*60)

# Get DB credentials
DB_HOST = os.getenv('DATABASE_HOST')
DB_PORT = os.getenv('DATABASE_PORT', 5432)
DB_NAME = os.getenv('DATABASE_NAME')
DB_USER = os.getenv('DATABASE_USER')
DB_PASSWORD = os.getenv('DATABASE_PASSWORD')

print(f"\nDatabase Config:")
print(f"  HOST: {DB_HOST}")
print(f"  PORT: {DB_PORT}")
print(f"  NAME: {DB_NAME}")
print(f"  USER: {DB_USER}")

# Test connection
print(f"\nTesting database connection...")
try:
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    print("  [OK] Connected to database")
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Check User table
    cursor.execute("SELECT COUNT(*) as count FROM \"User\"")
    count = cursor.fetchone()['count']
    print(f"  [OK] User table found with {count} users")
    
    # Check table structure
    cursor.execute("""
        SELECT column_name, data_type, character_maximum_length 
        FROM information_schema.columns
        WHERE table_name = 'User'
        ORDER BY ordinal_position
    """)
    cols = cursor.fetchall()
    print(f"\n  User Table Columns:")
    for col in cols:
        max_len = f"({col['character_maximum_length']})" if col['character_maximum_length'] else ""
        print(f"    {col['column_name']}: {col['data_type']}{max_len}")
    
    # Test password hashing
    print(f"\nPassword Hashing Test:")
    test_pwd = "password"
    hashed = hash_password(test_pwd)
    print(f"  Plain: {test_pwd}")
    print(f"  Hash: {hashed}")
    print(f"  Length: {len(hashed)} chars")
    
    is_match = verify_password(test_pwd, hashed)
    print(f"  Verification: {is_match}")
    
    # Test registration
    print(f"\nTest Registration:")
    import time
    test_user = f"test_{int(time.time())}"
    test_email = f"{test_user}@test.com"
    
    try:
        cursor.execute("""
            INSERT INTO "User" (first_name, last_name, username, password, email_id, role)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING user_id, username
        """, ("Test", "User", test_user, hash_password("testpass"), test_email, "STUDENT"))
        
        result = cursor.fetchone()
        conn.commit()
        
        print(f"  [OK] User created: ID={result['user_id']}, Username={result['username']}")
        
        # Test fetching the user
        cursor.execute('SELECT * FROM "User" WHERE username = %s', (test_user,))
        saved_user = cursor.fetchone()
        
        if saved_user:
            print(f"  [OK] User retrieved from DB")
            
            # Test password verification
            is_valid = verify_password("testpass", saved_user['password'])
            print(f"  [OK] Password verification: {is_valid}")
            
            if is_valid:
                print(f"\n[SUCCESS] Registration and login flow works!")
            else:
                print(f"\n[ERROR] Password verification failed")
        
    except Exception as reg_err:
        conn.rollback()
        print(f"  [ERROR] Registration failed: {reg_err}")
        import traceback
        traceback.print_exc()
    
    # Check sample existing users
    print(f"\nExisting Users:")
    cursor.execute('SELECT user_id, username, email_id, role, LENGTH(password) as pwd_len FROM "User" LIMIT 3')
    users = cursor.fetchall()
    for u in users:
        print(f"  ID:{u['user_id']} | {u['username']} | {u['email_id']} | {u['role']} | PwdLen:{u['pwd_len']}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()

print(f"\n" + "="*60)
print("DEBUG COMPLETE")
print("="*60)
