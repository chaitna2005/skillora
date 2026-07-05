# Database Debugging Steps

## Your Tech Stack

**NOT Flask + SQLAlchemy** → You have **FastAPI + PostgreSQL**

This means:
- ❌ No `app.config['SQLALCHEMY_DATABASE_URI']`
- ❌ No `db.create_all()`
- ❌ No `@app.before_first_request`

✅ You have PostgreSQL with manual schema management

## Step 1: Check Database Configuration

```bash
cd backend
python check_database.py
```

This will show:
- ✅ Database connection details (host, port, database name)
- ✅ Which database is being used
- ✅ What tables exist
- ✅ User table structure
- ✅ Whether database is writable

## Step 2: Start Backend with Diagnostics

```bash
python run.py
```

You'll see at startup:
```
================================================================================
DATABASE CONFIGURATION
================================================================================
DATABASE URI: postgresql://user:pass@localhost:5432/testmyknowledge
Host: localhost
Port: 5432
Database: testmyknowledge
User: postgres
================================================================================
[OK] Database connection pool initialized

[DATABASE TABLES]
  ✓ User
  ✓ Quiz
  ✓ Question
  ...
```

**If you see "⚠️  WARNING: No tables found!"**, run:
```bash
python reset_database.py
```

## Step 3: Test Registration with Debug Output

```bash
curl -X POST http://localhost:8000/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "debugtest",
    "password": "DebugPass123!",
    "first_name": "Debug",
    "last_name": "Test",
    "email_id": "debug@test.com",
    "role": "STUDENT"
  }'
```

Backend terminal will show:
```
================================================================================
[REGISTRATION] Attempting to register user: debugtest
================================================================================
[STEP 1] Checking if username 'debugtest' exists...
[STEP 1] ✓ Username available
[STEP 2] Checking if email 'debug@test.com' exists...
[STEP 2] ✓ Email available
[STEP 3] Hashing password...
[STEP 3] ✓ Password hashed (length: 102)
[STEP 4] Trying to save user 'debugtest' to database...
[STEP 4] ✅ User saved successfully! User ID: 1
================================================================================
```

## Common Issues & Fixes

### Issue 1: No tables found
```
[DATABASE TABLES]
  ⚠️  WARNING: No tables found!
```
**Fix:** Run `python reset_database.py`

### Issue 2: Database doesn't exist
```
❌ Connection failed!
Error: database "testmyknowledge" does not exist
```
**Fix:** Create database:
```sql
CREATE DATABASE testmyknowledge;
```
Then run `python reset_database.py`

### Issue 3: Wrong database path
```
DATABASE URI: postgresql://postgres:pass@localhost:5432/wrong_db_name
```
**Fix:** Check your `.env` file:
```
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=testmyknowledge
DATABASE_USER=postgres
DATABASE_PASSWORD=your_password
```

### Issue 4: User table doesn't exist
```
[STEP 4] ❌ relation "User" does not exist
```
**Fix:** Run `python reset_database.py`

### Issue 5: Password column too small
```
[REGISTRATION ERROR] ❌ DataError: value too long for type character varying(60)
```
**Fix:** Your schema is outdated. Run `python reset_database.py`

## Debug Flow Summary

```
1. python check_database.py
   ↓
   Shows database path and tables

2. python run.py
   ↓
   Startup shows database URI and tables

3. Test registration
   ↓
   Shows each step of registration

4. If any step fails
   ↓
   Backend terminal shows EXACT error
```

## Files Modified

1. `backend/app/main.py`
   - Added database URI printing at startup
   - Added table existence check at startup

2. `backend/app/routers/users.py`
   - Added step-by-step registration logging
   - Shows exactly where registration fails

3. `backend/check_database.py` (NEW)
   - Comprehensive database diagnostic tool

## Expected Output (Working System)

### Startup:
```
DATABASE URI: postgresql://postgres:***@localhost:5432/testmyknowledge
[OK] Database connection pool initialized
[DATABASE TABLES]
  ✓ User
  ✓ Quiz
  ✓ Question
  ...
```

### Registration:
```
[STEP 1] ✓ Username available
[STEP 2] ✓ Email available
[STEP 3] ✓ Password hashed (length: 102)
[STEP 4] ✅ User saved successfully! User ID: 1
```

### Login:
```
[LOGIN] User found: debugtest
[LOGIN] Password verification: True
[LOGIN] ✅ Login successful
```

## Next Actions

1. Run `python check_database.py` - See what database is being used
2. If no tables: Run `python reset_database.py`
3. Start backend: `python run.py` - Verify tables shown at startup
4. Test registration - Watch backend terminal for step-by-step output
5. Check where it fails - Exact step will be shown

The debug output will show you EXACTLY:
- Which database is being used
- Whether tables exist
- Which step of registration fails
- The exact error message
