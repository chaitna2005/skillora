# Quick Auth Fix Reference

## What Was Wrong

❌ **WRONG:** Used SHA256 hashing (insecure, no salt)  
❌ **WRONG:** Parameter order in `verify_password()` was inconsistent

## What's Fixed Now

✅ **Correct Password Hashing Functions:**

```python
# backend/app/utils/auth.py

from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password: str) -> str:
    return generate_password_hash(password)

def verify_password(stored_hash: str, password: str) -> bool:
    return check_password_hash(stored_hash, password)
```

✅ **Correct Login Route:**

```python
# backend/app/routers/users.py (line 105)

stored_hash = user.get("password")
password_valid = verify_password(stored_hash, credentials.password)  # hash first, password second
```

✅ **Correct Registration Route:**

```python
# backend/app/routers/users.py (line 43)

hashed_password = hash_password(user.password)
user_data = {
    "password": hashed_password,
    # ... other fields
}
```

## Apply the Fix in 4 Steps

```bash
# 1. Test password utilities (optional)
cd backend
python test_password_utils.py

# 2. Install werkzeug if not installed
pip install werkzeug>=3.0.0

# 3. Reset database (⚠️ deletes all data!)
python reset_database.py

# 4. Restart backend
python run.py
```

## Verify It Works

### Test Registration:
```bash
curl -X POST http://localhost:8000/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123",
    "first_name": "Test",
    "last_name": "User",
    "email_id": "test@example.com",
    "role": "STUDENT"
  }'
```

Expected: `201 Created` with user data

### Test Login:
```bash
curl -X POST http://localhost:8000/users/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123"
  }'
```

Expected: `200 OK` with `success: true` and access token

## Key Changes

| File | Change |
|------|--------|
| `backend/app/utils/auth.py` | ✅ Fixed: Now uses werkzeug's `generate_password_hash` and `check_password_hash` |
| `backend/app/utils/auth.py` | ✅ Fixed: Parameter order is now `verify_password(hash, password)` |
| `backend/app/routers/users.py` | ✅ Fixed: Login route passes parameters in correct order |
| `database/schema.sql` | ✅ Fixed: Username column is now `VARCHAR(150)` |
| `backend/requirements.txt` | ✅ Added: `werkzeug>=3.0.0` |

## Important Notes

⚠️ **All users must re-register** after database reset  
⚠️ **Old password hashes are incompatible** with the new system  
✅ **No frontend changes needed**  
✅ **Password column VARCHAR(255) is sufficient**  

## Troubleshooting

**If registration still fails:**
- Check if werkzeug is installed: `pip list | grep werkzeug`
- Check backend logs for import errors
- Verify database connection

**If login still fails:**
- Make sure database was reset (old hashes won't work)
- Check if user was registered AFTER the fix
- Run `python test_password_utils.py` to verify functions work
- Check backend logs for verification result

**If imports fail:**
- Run: `pip install werkzeug>=3.0.0`
- Restart the backend server
