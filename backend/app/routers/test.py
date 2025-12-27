"""
Test Routes
API endpoints for taking tests and viewing results
"""
from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extras import RealDictCursor
from typing import List
from app.database import get_db
from app.schemas.test import (
    TestStart,
    TestSubmit,
    TestResponse,
    TestResult,
    TestSummary,
    TestResultDetail
)
from app.models.test import TestModel
from app.models.question import QuestionModel
from app.services.test_service import TestService


router = APIRouter(prefix="/test", tags=["Test"])


@router.post("/start", response_model=TestResponse, status_code=status.HTTP_201_CREATED)
def start_test(
    test_data: TestStart,
    user_id: int,
    cursor: RealDictCursor = Depends(get_db)
):
    """Start a new test attempt"""
    
    take_data = {
        "user_id": user_id,
        "quiz_id": test_data.quiz_id,
        "quiz_assignment_id": test_data.quiz_assignment_id
    }
    
    quiz_take = TestModel.create_quiz_take(cursor, take_data)
    return quiz_take


@router.post("/submit", response_model=TestResult)
def submit_test(
    submission: TestSubmit,
    cursor: RealDictCursor = Depends(get_db)
):
    """Submit test answers and get results"""
    
    # Verify test exists
    quiz_take = TestModel.get_quiz_take(cursor, submission.uqt_id)
    if not quiz_take:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found"
        )
    
    # Check if already completed
    if quiz_take.get("completed_time"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Test already submitted"
        )
    
    # Evaluate answers
    answers = [
        {
            "question_id": ans.question_id,
            "question_option_ids": ans.question_option_ids
        }
        for ans in submission.answers
    ]
    
    evaluation = TestService.evaluate_test(cursor, submission.uqt_id, answers)
    
    # Get updated quiz take
    quiz_take = TestModel.get_quiz_take(cursor, submission.uqt_id)
    
    # Get detailed results
    quiz = QuestionModel.get_quiz_with_questions(cursor, quiz_take["quiz_id"])
    test_answers = TestModel.get_test_answers(cursor, submission.uqt_id)
    
    # Build detailed results
    details = []
    for question in quiz["questions"]:
        question_id = question["question_id"]
        
        # Get user's answers for this question
        user_answer_records = [
            ans for ans in test_answers 
            if ans["question_id"] == question_id
        ]
        
        user_answers = [ans["option_text"] for ans in user_answer_records]
        
        # Get correct answers
        correct_answers = [
            opt["option_text"] 
            for opt in question["options"] 
            if opt["is_correct"]
        ]
        
        # Check if correct
        is_correct = any(ans.get("is_correct", False) for ans in user_answer_records)
        if question["question_type"] == "CHECKLIST":
            # For checklist, all must be correct
            is_correct = (
                len(user_answer_records) == len(correct_answers) and
                all(ans.get("is_correct", False) for ans in user_answer_records)
            )
        
        details.append(TestResultDetail(
            question_id=question_id,
            question_text=question["question_text"],
            question_type=question["question_type"],
            user_answers=user_answers,
            correct_answers=correct_answers,
            is_correct=is_correct
        ))
    
    # Generate feedback
    feedback = TestService.get_feedback_message(
        evaluation["result"],
        evaluation["score_percentage"]
    )
    
    return TestResult(
        uqt_id=quiz_take["uqt_id"],
        quiz_name=quiz_take["quiz_name"],
        total_questions=evaluation["total_questions"],
        total_correct=evaluation["total_correct"],
        score_percentage=evaluation["score_percentage"],
        result=evaluation["result"],
        feedback=feedback,
        start_time=quiz_take["start_time"],
        completed_time=quiz_take["completed_time"],
        details=details
    )


@router.get("/result/{uqt_id}", response_model=TestResult)
def get_test_result(uqt_id: int, cursor: RealDictCursor = Depends(get_db)):
    """Get detailed results for a completed test"""
    
    quiz_take = TestModel.get_quiz_take(cursor, uqt_id)
    
    if not quiz_take:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found"
        )
    
    if not quiz_take.get("completed_time"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Test not yet completed"
        )
    
    # Get quiz and answers
    quiz = QuestionModel.get_quiz_with_questions(cursor, quiz_take["quiz_id"])
    test_answers = TestModel.get_test_answers(cursor, uqt_id)
    
    # Build detailed results
    details = []
    for question in quiz["questions"]:
        question_id = question["question_id"]
        
        user_answer_records = [
            ans for ans in test_answers 
            if ans["question_id"] == question_id
        ]
        
        user_answers = [ans["option_text"] for ans in user_answer_records]
        
        correct_answers = [
            opt["option_text"] 
            for opt in question["options"] 
            if opt["is_correct"]
        ]
        
        is_correct = any(ans.get("is_correct", False) for ans in user_answer_records)
        if question["question_type"] == "CHECKLIST":
            is_correct = (
                len(user_answer_records) == len(correct_answers) and
                all(ans.get("is_correct", False) for ans in user_answer_records)
            )
        
        details.append(TestResultDetail(
            question_id=question_id,
            question_text=question["question_text"],
            question_type=question["question_type"],
            user_answers=user_answers,
            correct_answers=correct_answers,
            is_correct=is_correct
        ))
    
    score_percentage = (quiz_take["total_correct"] / quiz_take["total_no_questions"] * 100)
    feedback = TestService.get_feedback_message(quiz_take["result"], score_percentage)
    
    return TestResult(
        uqt_id=quiz_take["uqt_id"],
        quiz_name=quiz_take["quiz_name"],
        total_questions=quiz_take["total_no_questions"],
        total_correct=quiz_take["total_correct"],
        score_percentage=score_percentage,
        result=quiz_take["result"],
        feedback=feedback,
        start_time=quiz_take["start_time"],
        completed_time=quiz_take["completed_time"],
        details=details
    )


@router.get("/user/{user_id}", response_model=List[TestResponse])
def get_user_tests(user_id: int, cursor: RealDictCursor = Depends(get_db)):
    """Get all tests taken by a user"""
    
    tests = TestModel.get_all_user_tests(cursor, user_id)
    return tests


@router.get("/user/{user_id}/pending", response_model=List[TestResponse])
def get_pending_tests(user_id: int, cursor: RealDictCursor = Depends(get_db)):
    """Get all pending (incomplete) tests for a user"""
    
    tests = TestModel.get_pending_tests(cursor, user_id)
    return tests


@router.get("/user/{user_id}/completed", response_model=List[TestResponse])
def get_completed_tests(user_id: int, cursor: RealDictCursor = Depends(get_db)):
    """Get all completed tests for a user"""
    
    tests = TestModel.get_completed_tests(cursor, user_id)
    return tests


@router.get("/summary/{user_id}", response_model=TestSummary)
def get_test_summary(user_id: int, cursor: RealDictCursor = Depends(get_db)):
    """Get test summary and statistics for a user"""
    
    all_tests = TestModel.get_all_user_tests(cursor, user_id)
    pending_tests = TestModel.get_pending_tests(cursor, user_id)
    completed_tests = TestModel.get_completed_tests(cursor, user_id)
    
    # Calculate average score
    total_score = 0
    scored_tests = 0
    
    for test in completed_tests:
        if test.get("total_correct") is not None and test.get("total_no_questions"):
            total_score += (test["total_correct"] / test["total_no_questions"] * 100)
            scored_tests += 1
    
    average_score = total_score / scored_tests if scored_tests > 0 else None
    
    # Get recent tests (last 5)
    recent_tests = all_tests[:5]
    
    return TestSummary(
        total_tests_taken=len(all_tests),
        total_tests_completed=len(completed_tests),
        total_tests_pending=len(pending_tests),
        average_score=average_score,
        recent_tests=recent_tests
    )

