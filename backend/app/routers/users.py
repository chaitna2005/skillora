"""
User Routes
API endpoints for user registration and authentication
"""
from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extras import RealDictCursor
from app.database import get_db
from app.schemas.user import UserRegister, UserLogin, UserResponse, LoginResponse, UserStatsResponse
from app.models.user import UserModel
from app.services.user_stats_service import UserStatsService
from app.utils.auth import hash_password, verify_password, create_access_token


router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: UserRegister, cursor: RealDictCursor = Depends(get_db)):
    """Register a new user"""
    
    # Check if username already exists
    existing_user = UserModel.get_user_by_username(cursor, user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Check if email already exists
    existing_email = UserModel.get_user_by_email(cursor, user.email_id)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_password = hash_password(user.password)
    
    # Create user
    user_data = {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
        "password": hashed_password,
        "email_id": user.email_id,
        "role": user.role.value
    }
    
    created_user = UserModel.create_user(cursor, user_data)
    return created_user


@router.post("/login", response_model=LoginResponse)
def login_user(credentials: UserLogin, cursor: RealDictCursor = Depends(get_db)):
    """Authenticate user and return token"""
    
    # Get user by username
    user = UserModel.get_user_by_username(cursor, credentials.username)
    
    if not user:
        return LoginResponse(
            success=False,
            message="Invalid username or password"
        )
    
    # Verify password
    if not verify_password(credentials.password, user["password"]):
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

