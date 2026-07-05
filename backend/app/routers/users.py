"""
User Routes
API endpoints for user registration and authentication
"""
from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash
from app.database import get_db
from app.schemas.user import UserRegister, UserLogin, UserResponse, LoginResponse, UserStatsResponse
from app.models.user import UserModel
from app.services.user_stats_service import UserStatsService
from app.utils.auth import create_access_token


router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: UserRegister, cursor: RealDictCursor = Depends(get_db)):
    """
    Register a new user
    
    IMPORTANT: Delete old database and recreate tables after password handling changes.
    Old password hashes are incompatible with werkzeug implementation.
    """
    
    print("=" * 80)
    print(f"[REGISTRATION] Attempting to register user: {user.username}")
    print("=" * 80)
    
    try:
        # Check if username already exists
        print(f"[STEP 1] Checking if username '{user.username}' exists...")
        existing_user = UserModel.get_user_by_username(cursor, user.username)
        if existing_user:
            print(f"[STEP 1] ❌ Username already exists")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        print(f"[STEP 1] ✓ Username available")
        
        # Check if email already exists
        print(f"[STEP 2] Checking if email '{user.email_id}' exists...")
        existing_email = UserModel.get_user_by_email(cursor, user.email_id)
        if existing_email:
            print(f"[STEP 2] ❌ Email already registered")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        print(f"[STEP 2] ✓ Email available")
        
        # Hash password using werkzeug directly (no custom helpers)
        print(f"[STEP 3] Hashing password...")
        hashed_password = generate_password_hash(user.password)
        print(f"[STEP 3] ✓ Password hashed (length: {len(hashed_password)})")
        
        # Create user
        user_data = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "password": hashed_password,
            "email_id": user.email_id,
            "role": user.role.value
        }
        
        print(f"[STEP 4] Trying to save user '{user.username}' to database...")
        created_user = UserModel.create_user(cursor, user_data)
        print(f"[STEP 4] ✅ User saved successfully! User ID: {created_user.get('user_id')}")
        print("=" * 80)
        
        return created_user
        
    except HTTPException:
        print("=" * 80)
        raise
    except Exception as e:
        print(f"[REGISTRATION ERROR] ❌ {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        print("=" * 80)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=LoginResponse)
def login_user(credentials: UserLogin, cursor: RealDictCursor = Depends(get_db)):
    """
    Authenticate user and return token
    Uses werkzeug.security.check_password_hash directly for password verification
    """
    
    try:
        # Get user by username
        user = UserModel.get_user_by_username(cursor, credentials.username)
        
        # User not found or password invalid
        if not user:
            return LoginResponse(
                success=False,
                message="Invalid username or password"
            )
        
        stored_hash = user.get("password")
        if not stored_hash:
            return LoginResponse(
                success=False,
                message="Invalid username or password"
            )
        
        # Verify password using werkzeug directly (no custom helpers)
        # check_password_hash(stored_hash, password) - NO direct comparison
        if not check_password_hash(stored_hash, credentials.password):
            return LoginResponse(
                success=False,
                message="Invalid username or password"
            )
        
        # Create access token
        access_token = create_access_token(data={
            "user_id": user["user_id"],
            "username": user["username"],
            "role": user["role"]
        })
        
        # Remove password from response
        user.pop("password", None)
        
        return LoginResponse(
            success=True,
            message="Login successful",
            user=user,
            access_token=access_token
        )
        
    except Exception as e:
        print(f"[ERROR] Login failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return LoginResponse(
            success=False,
            message=f"Login error: {str(e)}"
        )


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, cursor: RealDictCursor = Depends(get_db)):
    """Get user details by ID"""
    
    user = UserModel.get_user_by_id(cursor, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.get("/{user_id}/stats", response_model=UserStatsResponse)
def get_user_stats(user_id: int, cursor: RealDictCursor = Depends(get_db)):
    """Get user stats (badges and streaks)"""
    
    from app.models.user_stats import UserStatsModel
    
    stats = UserStatsModel.get_or_create_user_stats(cursor, user_id)
    
    return UserStatsResponse(
        quiz_completion_count=stats.get("quiz_completion_count", 0) or 0,
        current_streak=stats.get("current_streak", 0) or 0,
        longest_streak=stats.get("longest_streak", 0) or 0,
        last_active_date=stats.get("last_active_date"),
        unlocked_badges=stats.get("unlocked_badges", []) or []
    )

