"""
User Schemas
Pydantic models for request/response validation
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    TEACHER = "TEACHER"
    STUDENT = "STUDENT"


class UserRegister(BaseModel):
    first_name: str
    last_name: str
    username: str
    password: str
    email_id: EmailStr
    role: UserRole = UserRole.STUDENT


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    user_id: int
    first_name: str
    last_name: str
    username: str
    email_id: str
    role: str
    created_at: Optional[datetime] = None


class LoginResponse(BaseModel):
    success: bool
    message: str
    user: Optional[UserResponse] = None
    access_token: Optional[str] = None


class UserStatsResponse(BaseModel):
    quiz_completion_count: int
    current_streak: int
    longest_streak: int
    last_active_date: Optional[datetime] = None
    unlocked_badges: list[str]
