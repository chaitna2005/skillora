# Quick Start - Database Debugging

## Your System

❌ **NOT Flask + SQLAlchemy**  
✅ **FastAPI + PostgreSQL**

This means no `app.config` or `db.create_all()`. You use PostgreSQL with SQL schema files.

## 3-Step Debug Process

### Step 1: Check Database Status

```bash
cd backend
python check_database.py
```

**This will show:**
- ✅ Which database is being used (path/URI)
- ✅ Whether connection works
- ✅ What tables exist
- ✅ User table structure

**If you see "No tables found":**
```bash
python reset_database.py
```

### Step 2: Start Backend (Watch Output)

```bash
python run.py
```

**At startup, you'll see:**
```
================================================================================
DATABASE CONFIGURATION
================================================================================
DATABASE URI: postgresql://user:pass@localhost:5432/testmyknowledge
Host: localhost
Port: 5432
Database: testmyknowledge
================================================================================

[DATABASE TABLES]
  ✓ User
  ✓ Quiz
  ✓ Question
  ...
```

**If no tables shown:** Run `python reset_database.py` and restart.

### Step 3: Test Registration (Watch Backend Terminal)

In a **NEW terminal**:
```bash
curl -X POST http://localhost:8000/users/register \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"test1\",\"password\":\"Pass123!\",\"first_name\":\"Test\",\"last_name\":\"User\",\"email_id\":\"test@test.com\",\"role\":\"STUDENT\"}"
```

**Backend terminal will show each step:**
```
================================================================================
[REGISTRATION] Attempting to register user: test1
================================================================================
[STEP 1] Checking if username 'test1' exists...
[STEP 1] ✓ Username available
[STEP 2] Checking if email 'test@test.com' exists...
[STEP 2] ✓ Email available
[STEP 3] Hashing password...
[STEP 3] ✓ Password hashed (length: 102)
[STEP 4] Trying to save user 'test1' to database...
[STEP 4] ✅ User saved successfully! User ID: 1
================================================================================
```

**If any step fails, you'll see EXACTLY where and why.**

## Common Issues

### ❌ "No tables found"
**Fix:**
```bash
python reset_database.py
```

### ❌ "database does not exist"
**Fix:** Create database first:
```sql
-- In PostgreSQL:
CREATE DATABASE testmyknowledge;
```
Then run:
```bash
python reset_database.py
```

### ❌ "relation 'User' does not exist"
**Fix:**
```bash
python reset_database.py
```

### ❌ "value too long for type character varying(60)"
**Fix:** Schema outdated. Run:
```bash
python reset_database.py
```

### ❌ "could not connect to server"
**Fix:**
1. Check PostgreSQL is running
2. Check `.env` file has correct credentials:
   ```
   DATABASE_HOST=localhost
   DATABASE_PORT=5432
   DATABASE_NAME=testmyknowledge
   DATABASE_USER=postgres
   DATABASE_PASSWORD=your_password
   ```

## What to Look For

✅ **At Startup:**
- Database URI shown
- Tables list shown
- No error messages

✅ **During Registration:**
- All 4 steps complete with ✓
- "User saved successfully"
- User ID returned

❌ **If Registration Fails:**
- Backend terminal shows EXACT step that failed
- Shows EXACT error message
- No need to guess

## Files You Need

1. `backend/.env` - Database credentials
   ```
   DATABASE_HOST=localhost
   DATABASE_PORT=5432
   DATABASE_NAME=testmyknowledge
   DATABASE_USER=postgres
   DATABASE_PASSWORD=your_password
   OPENAI_API_KEY=your_key
   ```

2. Run once to create tables:
   ```bash
   python reset_database.py
   ```

## Summary

Your system now shows:
1. **At startup:** Which database is being used + what tables exist
2. **During registration:** Each step with success/fail
3. **On error:** Exact error message with stack trace

No more guessing where it fails. The backend terminal tells you everything.

## Quick Commands

```bash
# 1. Check database
python check_database.py

# 2. Create/reset tables
python reset_database.py

# 3. Start backend
python run.py

# 4. Test registration (in new terminal)
curl -X POST http://localhost:8000/users/register -H "Content-Type: application/json" -d "{\"username\":\"test1\",\"password\":\"Pass123!\",\"first_name\":\"Test\",\"last_name\":\"User\",\"email_id\":\"test@test.com\",\"role\":\"STUDENT\"}"
```

The backend terminal will show you EXACTLY what's happening at each step.
