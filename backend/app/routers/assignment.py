"""
Assignment Routes
API endpoints for assignment access and claiming
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from psycopg2.extras import RealDictCursor
from typing import Optional
from app.database import get_db
from app.schemas.quiz import (
    QuizAssignmentResponse,
    AssignmentInfoResponse,
    ClaimAssignmentResponse
)
from app.models.quiz import QuizModel
from app.models.test import TestModel
from app.models.user import UserModel


router = APIRouter(prefix="/assignments", tags=["Assignments"])


@router.get("/{token}", response_model=AssignmentInfoResponse)
def get_assignment_info(
    token: str,
    cursor: RealDictCursor = Depends(get_db)
):
    """Get assignment information by token - PUBLIC ACCESS"""
    
    assignment = QuizModel.get_assignment_by_token(cursor, token)
    if not assignment:
        return AssignmentInfoResponse(
            quiz_id=0,
            quiz_name="",
            total_questions=0,
            difficulty_level="",
            valid=False,
            message="Invalid or expired share link"
        )
    
    return AssignmentInfoResponse(
        quiz_id=assignment["quiz_id"],
        quiz_name=assignment["quiz_name"],
        total_questions=assignment["total_no_questions"],
        difficulty_level=assignment["difficulty_level"],
        valid=True,
        message=None
    )


@router.post("/{token}/claim", response_model=ClaimAssignmentResponse, status_code=status.HTTP_200_OK)
def claim_assignment(
    token: str,
    user_id: int = Query(..., description="User ID claiming the assignment"),
    cursor: RealDictCursor = Depends(get_db)
):
    """Claim an assignment using a share token - Requires login"""
    
    assignment = QuizModel.get_assignment_by_token(cursor, token)
    if not assignment:
        return ClaimAssignmentResponse(
            success=False,
            message="Invalid or expired share link",
            assignment=None
        )
    
    user = UserModel.get_user_by_id(cursor, user_id)
    if not user:
        return ClaimAssignmentResponse(
            success=False,
            message="User not found. Please log in.",
            assignment=None
        )
    
    if user.get("role") != "STUDENT":
        return ClaimAssignmentResponse(
            success=False,
            message="This assignment link is for students. Teachers can view assignment results in their dashboard.",
            assignment=None
        )
    
    claimed = QuizModel.claim_assignment(cursor, token, user_id)
    if not claimed:
        return ClaimAssignmentResponse(
            success=False,
            message="Assignment already claimed or invalid",
            assignment=None
        )
    
    take_data = {
        "user_id": user_id,
        "quiz_id": assignment["quiz_id"],
        "quiz_assignment_id": claimed["quiz_assignment_id"]
    }
    
    existing_test = TestModel.get_pending_test_for_quiz(
        cursor,
        user_id,
        assignment["quiz_id"],
        claimed["quiz_assignment_id"]
    )
    
    if not existing_test:
        TestModel.create_quiz_take(cursor, take_data, set_start_time=False)
    
    return ClaimAssignmentResponse(
        success=True,
        message="Assignment claimed successfully! You can now find it in Assigned Quizzes.",
        assignment=claimed
    )

