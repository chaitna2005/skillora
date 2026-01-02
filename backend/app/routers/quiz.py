"""
Quiz Routes
API endpoints for quiz creation and management
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from psycopg2.extras import RealDictCursor
from typing import List
from app.database import get_db
from app.schemas.quiz import (
    QuizCreate, 
    QuizResponse, 
    QuizAssignmentCreate,
    QuizAssignmentResponse
)
from app.models.quiz import QuizModel
from app.models.question import QuestionModel
from app.services.quiz_service import QuizService


router = APIRouter(prefix="/quiz", tags=["Quiz"])


@router.post("/create", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
def create_quiz(
    quiz_data: QuizCreate,
    user_id: int = Query(..., description="User ID creating the quiz"),
    cursor: RealDictCursor = Depends(get_db)
):
    """Create a new quiz with AI-generated questions"""
    
    try:
        quiz_service = QuizService()
        
        quiz = quiz_service.create_quiz_with_questions(
            cursor=cursor,
            user_id=user_id,
            prompt=quiz_data.prompt,
            difficulty_level=quiz_data.difficulty_level.value,
            total_no_questions=quiz_data.total_no_questions
        )
        
        return quiz
        
    except Exception as e:
        # Log full traceback
        import traceback
        print("[ERROR] Quiz creation failed:")
        traceback.print_exc()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create quiz: {str(e)}"
        )


@router.get("/user/{user_id}", response_model=List[QuizResponse])
def get_user_quizzes(user_id: int, cursor: RealDictCursor = Depends(get_db)):
    """Get all quizzes created by a user"""
    
    quizzes = QuizModel.get_quizzes_by_user(cursor, user_id)
    return quizzes


@router.delete("/{quiz_id}")
def delete_quiz(
    quiz_id: int,
    user_id: int = Query(..., description="User ID deleting the quiz"),
    cursor: RealDictCursor = Depends(get_db)
):
    """Delete a quiz"""
    
    # Verify quiz exists and belongs to user
    quiz = QuizModel.get_quiz_by_id(cursor, quiz_id)
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    if quiz["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own quizzes"
        )
    
    deleted = QuizModel.delete_quiz(cursor, quiz_id, user_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete quiz"
        )
    
    return {"message": "Quiz deleted successfully"}


@router.get("/assigned/{user_id}")
def get_assigned_quizzes(user_id: int, cursor: RealDictCursor = Depends(get_db)):
    """Get all quizzes assigned to a student"""
    
    quizzes = QuizModel.get_assigned_quizzes(cursor, user_id)
    return quizzes


@router.get("/{quiz_id}", response_model=QuizResponse)
def get_quiz(quiz_id: int, cursor: RealDictCursor = Depends(get_db)):
    """Get quiz details with questions"""
    
    quiz = QuestionModel.get_quiz_with_questions(cursor, quiz_id)
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    # Hide correct answers for users (but keep option_id for submission)
    for question in quiz.get("questions", []):
        for option in question.get("options", []):
            # Keep option_id and option_text, remove is_correct
            if "is_correct" in option:
                del option["is_correct"]
    
    return quiz


@router.get("/{quiz_id}/with-answers")
def get_quiz_with_answers(quiz_id: int, cursor: RealDictCursor = Depends(get_db)):
    """Get quiz details with correct answers (for creators/results)"""
    
    quiz = QuestionModel.get_quiz_with_questions(cursor, quiz_id)
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    return quiz


@router.post("/assign", response_model=QuizAssignmentResponse, status_code=status.HTTP_201_CREATED)
def assign_quiz(
    assignment: QuizAssignmentCreate,
    assigned_by: int = Query(..., description="Teacher ID assigning the quiz"),
    cursor: RealDictCursor = Depends(get_db)
):
    """Assign a quiz to a student"""
    
    # Verify quiz exists
    quiz = QuizModel.get_quiz_by_id(cursor, assignment.quiz_id)
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    assignment_data = {
        "user_id": assignment.user_id,
        "assigned_by": assigned_by,
        "quiz_id": assignment.quiz_id,
        "due_date": assignment.due_date
    }
    
    result = QuizModel.create_quiz_assignment(cursor, assignment_data)
    return result

