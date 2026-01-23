"""
Quiz Routes
API endpoints for quiz creation and management
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import Response
from psycopg2.extras import RealDictCursor
from typing import List, Optional
import secrets
import csv
import io
from datetime import datetime
from app.database import get_db
from app.schemas.quiz import (
    QuizCreate, 
    QuizResponse, 
    QuizAssignmentCreate,
    QuizAssignmentResponse,
    BulkDeleteRequest,
    ShareLinkResponse,
    AssignmentResultResponse,
    QuizAnalyticsResponse,
    QuestionDifficultyResponse
)
from app.models.quiz import QuizModel
from app.models.question import QuestionModel
from app.models.test import TestModel
from app.models.user import UserModel
from app.services.quiz_service import QuizService
from app.config import settings


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
    
    print(f"[API] get_user_quizzes called with user_id: {user_id}")
    quizzes = QuizModel.get_quizzes_by_user(cursor, user_id)
    print(f"[API] get_user_quizzes returned {len(quizzes)} quizzes")
    if quizzes:
        print(f"[API] First quiz sample: {quizzes[0] if quizzes else 'None'}")
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


@router.delete("/user/{user_id}/all")
def delete_all_user_quizzes(
    user_id: int,
    cursor: RealDictCursor = Depends(get_db)
):
    """Delete all quizzes created by a user"""
    
    deleted_count = QuizModel.delete_all_user_quizzes(cursor, user_id)
    
    return {
        "message": f"Successfully deleted {deleted_count} quiz(zes)",
        "deleted_count": deleted_count
    }


@router.delete("/assigned/{user_id}/all")
def delete_all_assigned_quizzes(
    user_id: int,
    cursor: RealDictCursor = Depends(get_db)
):
    """Delete all quiz assignments for a user (unassign all quizzes)"""
    
    deleted_count = QuizModel.delete_all_assigned_quizzes(cursor, user_id)
    
    return {
        "message": f"Successfully unassigned {deleted_count} quiz(zes)",
        "deleted_count": deleted_count
    }


@router.post("/bulk-delete")
def bulk_delete_quizzes(
    request: BulkDeleteRequest,
    user_id: int = Query(..., description="User ID deleting quizzes"),
    cursor: RealDictCursor = Depends(get_db)
):
    """Bulk delete specific quizzes by IDs"""
    
    if not request.ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No IDs provided"
        )
    
    deleted_count = QuizModel.delete_quizzes_by_ids(cursor, request.ids, user_id)
    
    return {
        "message": f"Successfully deleted {deleted_count} quiz(zes)",
        "deleted_count": deleted_count,
        "requested_count": len(request.ids)
    }


@router.post("/assigned/bulk-delete")
def bulk_delete_assigned_quizzes(
    request: BulkDeleteRequest,
    user_id: int = Query(..., description="User ID unassigning quizzes"),
    cursor: RealDictCursor = Depends(get_db)
):
    """Bulk unassign specific quizzes by assignment IDs"""
    
    print(f"[API] bulk_delete_assigned_quizzes called:")
    print(f"  - user_id: {user_id}")
    print(f"  - assignment_ids: {request.ids}")
    
    if not request.ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No IDs provided"
        )
    
    # Check if user is a teacher
    user = UserModel.get_user_by_id(cursor, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    is_teacher = user.get("role") == "TEACHER"
    print(f"[API] User role: {user.get('role')}, is_teacher: {is_teacher}")
    
    deleted_count = QuizModel.delete_assigned_quizzes_by_ids(cursor, request.ids, user_id, is_teacher)
    
    print(f"[API] Successfully unassigned {deleted_count} out of {len(request.ids)} requested")
    
    return {
        "message": f"Successfully unassigned {deleted_count} quiz(zes)",
        "deleted_count": deleted_count,
        "requested_count": len(request.ids)
    }


@router.get("/assigned/{user_id}")
def get_assigned_quizzes(user_id: int, cursor: RealDictCursor = Depends(get_db)):
    """Get assigned quizzes based on user role
    - STUDENTS: Get quizzes assigned to them
    - TEACHERS: Get quizzes they have assigned to students (with submission counts)
    """
    
    print(f"[API] get_assigned_quizzes called with user_id: {user_id}")
    
    # Check user role
    user = UserModel.get_user_by_id(cursor, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.get("role") == "TEACHER":
        # Teachers see quizzes they have assigned to students (assigned_by = teacher_id)
        print(f"[API] User {user_id} is TEACHER. Returning quizzes they assigned to students.")
        quizzes = QuizModel.get_teacher_assigned_quizzes(cursor, user_id)
        print(f"[API] get_assigned_quizzes returned {len(quizzes)} teacher-assigned quizzes")
        if quizzes:
            print(f"[API] First teacher-assigned quiz sample: {quizzes[0]}")
        return quizzes
    
    # Students get their assigned quizzes
    quizzes = QuizModel.get_assigned_quizzes(cursor, user_id)
    print(f"[API] get_assigned_quizzes returned {len(quizzes)} quizzes for STUDENT")
    if quizzes:
        print(f"[API] First assigned quiz sample: {quizzes[0] if quizzes else 'None'}")
    return quizzes


@router.get("/{quiz_id}", response_model=QuizResponse)
def get_quiz(
    quiz_id: int, 
    for_test: bool = False,
    uqt_id: Optional[int] = None,
    cursor: RealDictCursor = Depends(get_db)
):
    """Get quiz details with questions
    
    Args:
        quiz_id: Quiz ID
        for_test: If True, shuffle questions and options for test integrity
        uqt_id: Optional test attempt ID for deterministic shuffling
    """
    
    if for_test:
        # Shuffle for test attempts - use uqt_id as seed if provided for consistency
        quiz = QuestionModel.get_quiz_with_questions(
            cursor, 
            quiz_id, 
            shuffle=True, 
            seed=uqt_id
        )
    else:
        # Normal view - no shuffling
        quiz = QuestionModel.get_quiz_with_questions(cursor, quiz_id, shuffle=False)
    
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
    
    # Create the assignment
    result = QuizModel.create_quiz_assignment(cursor, assignment_data)
    
    # Create a NOT_STARTED test record for this assignment
    # Check if test record already exists
    existing_test = TestModel.get_pending_test_for_quiz(
        cursor,
        assignment.user_id,
        assignment.quiz_id,
        result["quiz_assignment_id"]
    )
    
    if not existing_test:
        # Create NOT_STARTED test record
        take_data = {
            "user_id": assignment.user_id,
            "quiz_id": assignment.quiz_id,
            "quiz_assignment_id": result["quiz_assignment_id"]
        }
        TestModel.create_quiz_take(cursor, take_data, set_start_time=False)
    
    return result


@router.post("/{quiz_id}/assign", response_model=ShareLinkResponse, status_code=status.HTTP_201_CREATED)
def create_assignment(
    quiz_id: int,
    teacher_id: int = Query(..., description="Teacher ID creating the assignment"),
    cursor: RealDictCursor = Depends(get_db)
):
    """Create a quiz assignment and generate shareable link - TEACHER ONLY"""
    
    quiz = QuizModel.get_quiz_by_id(cursor, quiz_id)
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    teacher = UserModel.get_user_by_id(cursor, teacher_id)
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    if teacher.get("role") != "TEACHER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can create assignments"
        )
    
    if quiz["user_id"] != teacher_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only quiz creator can create assignments"
        )
    
    try:
        assignment = QuizModel.create_shareable_assignment(cursor, teacher_id, quiz_id, "")
        
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create assignment"
            )
        
        import base64
        import json
        assignment_id = assignment["quiz_assignment_id"]
        token_data = {"assignment_id": assignment_id, "quiz_id": quiz_id}
        token_json = json.dumps(token_data)
        share_token = base64.urlsafe_b64encode(token_json.encode()).decode().rstrip('=')
        
        frontend_url = settings.CORS_ORIGINS[0] if settings.CORS_ORIGINS else "http://localhost:3000"
        share_url = f"{frontend_url}/assign/{share_token}"
        
        return {
            "share_token": share_token,
            "share_url": share_url,
            "quiz_assignment_id": assignment_id
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create assignment: {str(e)}"
        )




@router.get("/assign/results/{teacher_id}", response_model=List[AssignmentResultResponse])
def get_assignment_results(
    teacher_id: int,
    cursor: RealDictCursor = Depends(get_db)
):
    """Get all assignment results for quizzes assigned by teacher"""
    
    teacher = UserModel.get_user_by_id(cursor, teacher_id)
    if not teacher or teacher.get("role") != "TEACHER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can view assignment results"
        )
    
    results = QuizModel.get_assignment_results_for_teacher(cursor, teacher_id)
    
    print(f"[API] get_assignment_results found {len(results)} total results")
    
    formatted_results = []
    for result in results:
        formatted_results.append({
            "quiz_assignment_id": result["quiz_assignment_id"],
            "quiz_id": result["quiz_id"],
            "quiz_name": result["quiz_name"],
            "student_id": result["student_id"],
            "student_name": result["student_name"],
            "uqt_id": result.get("uqt_id"),
            "completed_time": result.get("completed_time"),
            "total_correct": result.get("total_correct"),
            "result": result.get("result"),
            "total_questions": result["total_no_questions"],
            "attempt_status": result["attempt_status"]
        })
    
    if formatted_results:
        completed_count = sum(1 for r in formatted_results if r["attempt_status"] == "COMPLETED")
        print(f"[API] Returning {len(formatted_results)} results, {completed_count} completed")
        print(f"[API] Sample result: {formatted_results[0]}")
    
    return formatted_results


@router.get("/assign/analytics/{teacher_id}", response_model=List[QuizAnalyticsResponse])
def get_quiz_analytics(
    teacher_id: int,
    cursor: RealDictCursor = Depends(get_db)
):
    """Get quiz-level analytics for all quizzes assigned by teacher"""
    
    teacher = UserModel.get_user_by_id(cursor, teacher_id)
    if not teacher or teacher.get("role") != "TEACHER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can view quiz analytics"
        )
    
    analytics = QuizModel.get_quiz_analytics_for_teacher(cursor, teacher_id)
    
    formatted_analytics = []
    for item in analytics:
        formatted_analytics.append({
            "quiz_id": item["quiz_id"],
            "quiz_name": item["quiz_name"],
            "total_students": item["total_students"],
            "attempted": item["attempted"],
            "average_score": float(item["average_score"]) if item["average_score"] is not None else 0.0,
            "highest_score": float(item["highest_score"]) if item["highest_score"] is not None else 0.0,
            "lowest_score": float(item["lowest_score"]) if item["lowest_score"] is not None else 0.0,
            "total_questions": item["total_no_questions"]
        })
    
    return formatted_analytics


@router.get("/{quiz_id}/question-difficulty/{teacher_id}", response_model=List[QuestionDifficultyResponse])
def get_question_difficulty(
    quiz_id: int,
    teacher_id: int,
    cursor: RealDictCursor = Depends(get_db)
):
    """Get question difficulty analysis for a specific quiz"""
    
    teacher = UserModel.get_user_by_id(cursor, teacher_id)
    if not teacher or teacher.get("role") != "TEACHER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can view question difficulty"
        )
    
    quiz = QuizModel.get_quiz_by_id(cursor, quiz_id)
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    if quiz["user_id"] != teacher_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only quiz creator can view question difficulty"
        )
    
    try:
        difficulty_data = QuizModel.get_question_difficulty_for_quiz(cursor, quiz_id, teacher_id)
        
        if not difficulty_data:
            return []
        
        formatted_difficulty = []
        for item in difficulty_data:
            try:
                formatted_difficulty.append({
                    "question_id": int(item.get("question_id", 0)),
                    "question_text": str(item.get("question_text", "")),
                    "total_attempts": int(item.get("total_attempts", 0)) if item.get("total_attempts") is not None else 0,
                    "incorrect_percentage": float(item.get("incorrect_percentage", 0.0)) if item.get("incorrect_percentage") is not None else 0.0
                })
            except (ValueError, TypeError) as e:
                print(f"[WARNING] Skipping invalid question difficulty item: {item}, error: {e}")
                continue
        
        return formatted_difficulty
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve question difficulty: {str(e)}"
        )


@router.get("/export/results/{teacher_id}", response_class=Response)
def export_quiz_results_csv(
    teacher_id: int,
    quiz_id: Optional[int] = Query(None, description="Optional quiz ID to filter results"),
    cursor: RealDictCursor = Depends(get_db)
):
    """Export quiz results as CSV - TEACHER ONLY"""
    
    teacher = UserModel.get_user_by_id(cursor, teacher_id)
    if not teacher or teacher.get("role") != "TEACHER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can export quiz results"
        )
    
    if quiz_id:
        quiz = QuizModel.get_quiz_by_id(cursor, quiz_id)
        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quiz not found"
            )
        if quiz["user_id"] != teacher_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only quiz creator can export results"
            )
    
    results = QuizModel.get_assignment_results_for_teacher(cursor, teacher_id)
    
    if quiz_id:
        results = [r for r in results if r["quiz_id"] == quiz_id]
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "Student Name",
        "Quiz Title",
        "Score",
        "Total Questions",
        "Percentage",
        "Result",
        "Attempt Date",
        "Status"
    ])
    
    for result in results:
        student_name = result.get("student_name", "Unknown")
        quiz_name = result.get("quiz_name", "Unknown")
        total_correct = result.get("total_correct")
        total_questions = result.get("total_no_questions", 0)
        result_text = result.get("result", "N/A")
        completed_time = result.get("completed_time")
        attempt_status = result.get("attempt_status", "Unknown")
        
        if total_correct is not None and total_questions > 0:
            percentage = round((total_correct / total_questions) * 100, 1)
            score = f"'{total_correct}/{total_questions}"
        else:
            percentage = 0.0
            score = "'N/A"
        
        if completed_time:
            attempt_date = completed_time.strftime("%Y-%m-%d %H:%M:%S") if isinstance(completed_time, datetime) else str(completed_time)
        else:
            attempt_date = "N/A"
        
        writer.writerow([
            student_name,
            quiz_name,
            score,
            total_questions,
            f"{percentage}%",
            result_text,
            attempt_date,
            attempt_status
        ])
    
    csv_content = output.getvalue()
    output.close()
    
    filename = f"quiz_results_{quiz_id}.csv" if quiz_id else f"all_quiz_results_{teacher_id}.csv"
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )

