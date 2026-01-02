"""
Test Routes
API endpoints for taking tests and viewing results
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from psycopg2.extras import RealDictCursor
from typing import List
from app.database import get_db
from app.schemas.test import (
    TestStart,
    TestSubmit,
    TestResponse,
    TestResult,
    TestSummary,
    TestResultDetail,
    BulkDeleteRequest,
    SaveAnswerRequest
)
from app.models.test import TestModel
from app.models.question import QuestionModel
from app.services.test_service import TestService


router = APIRouter(prefix="/test", tags=["Test"])


@router.post("/start", response_model=TestResponse, status_code=status.HTTP_201_CREATED)
def start_test(
    test_data: TestStart,
    user_id: int = Query(..., description="User ID starting the test"),
    cursor: RealDictCursor = Depends(get_db)
):
    """Start a new test attempt or resume existing pending test
    
    Business Rules:
    - Always check for existing pending test (regardless of assignment_id)
    - If existing test found: Resume it (handles continuation from Pending Tests)
    - If no existing test: Create new test
    - This ensures:
      * First click from My Quizzes → creates new test (no existing test)
      * Click from Pending Tests → resumes existing test (if exists)
      * Subsequent clicks from My Quizzes → creates new test (if no existing test)
    """
    
    # Handle quiz_assignment_id - convert 0 or None to None (NULL in DB)
    assignment_id = test_data.quiz_assignment_id
    if assignment_id is not None and assignment_id <= 0:
        assignment_id = None
    
    # MANDATORY: Create test attempt IMMEDIATELY when "Take Test" is clicked
    # This test MUST appear in Pending Tests with status IN_PROGRESS
    # Test is persisted BEFORE questions are rendered
    
    # Check for existing pending test ONLY if assignment_id exists (from Pending Tests)
    # If assignment_id is NULL (from My Quizzes), always create new test
    if assignment_id is not None:
        # Coming from Pending Tests - check for existing test to resume
        existing_test = TestModel.get_pending_test_for_quiz(
            cursor, 
            user_id, 
            test_data.quiz_id, 
            assignment_id
        )
        
        if existing_test:
            # Found existing test - resume it
            if existing_test.get("status") == "NOT_STARTED":
                updated_test = TestModel.update_test_to_in_progress(cursor, existing_test["uqt_id"])
                if updated_test:
                    quiz_take = TestModel.get_quiz_take(cursor, updated_test["uqt_id"])
                    return quiz_take
            
            # Return existing IN_PROGRESS test (resume)
            quiz_take = TestModel.get_quiz_take(cursor, existing_test["uqt_id"])
            return quiz_take
    
    # No assignment_id (My Quizzes) OR no existing test - CREATE NEW TEST
    # This ensures a test is ALWAYS created when clicking "Take Test" from My Quizzes
    take_data = {
        "user_id": user_id,
        "quiz_id": test_data.quiz_id,
        "quiz_assignment_id": assignment_id
    }
    
    # CRITICAL: set_start_time=True ensures status = IN_PROGRESS immediately
    # INSERT happens here - record is created in database
    quiz_take = TestModel.create_quiz_take(cursor, take_data, set_start_time=True)
    
    # MANDATORY: Verify record was created
    if not quiz_take or not quiz_take.get("uqt_id"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create test attempt"
        )
    
    # Ensure status is IN_PROGRESS
    if quiz_take.get("status") != "IN_PROGRESS":
        quiz_take["status"] = "IN_PROGRESS"
    
    # Transaction commits automatically via get_db dependency when function returns
    # Record is now persisted in database and will appear in Pending Tests
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
    
    # Validate submission has answers
    if not submission.answers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No answers provided"
        )
    
    # Evaluate answers
    answers = [
        {
            "question_id": ans.question_id,
            "question_option_ids": ans.question_option_ids
        }
        for ans in submission.answers
    ]
    
    try:
        evaluation = TestService.evaluate_test(cursor, submission.uqt_id, answers)
    except Exception as e:
        print(f"[ERROR] Test evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate test: {str(e)}"
        )
    
    # Get updated quiz take
    quiz_take = TestModel.get_quiz_take(cursor, submission.uqt_id)
    
    # Get detailed results
    quiz = QuestionModel.get_quiz_with_questions(cursor, quiz_take["quiz_id"])
    test_answers = TestModel.get_test_answers(cursor, submission.uqt_id)
    
    # Build detailed results using set-based comparison (consistent with evaluation logic)
    details = []
    for question in quiz["questions"]:
        question_id = question["question_id"]
        question_type = question.get("question_type", "RADIO")
        
        # Get user's answers for this question (normalize to integers)
        user_answer_records = [
            ans for ans in test_answers 
            if ans["question_id"] == question_id
        ]
        user_option_ids = set(int(ans["question_option_id"]) for ans in user_answer_records)
        
        user_answers = [ans["option_text"] for ans in user_answer_records]
        
        # CRITICAL: Re-compute correct options deterministically (same as TestService)
        correct_option_ids = TestService._determine_correct_options(
            question["question_text"],
            question_type,
            question["options"]
        )
        
        correct_answers = [
            opt["option_text"] 
            for opt in question["options"] 
            if int(opt["question_option_id"]) in correct_option_ids
        ]
        
        # Evaluate using VALUE-based comparison (same as TestService.evaluate_test)
        if question_type == "RADIO":
            # RADIO: Compare VALUES, not option IDs
            if len(user_option_ids) != 1:
                is_correct = False
            else:
                # Get the value of user's selected option
                user_selected_id = next(iter(user_option_ids))
                user_option = next((opt for opt in question["options"] if int(opt["question_option_id"]) == user_selected_id), None)
                
                if user_option is None:
                    is_correct = False
                else:
                    # Always use value-based comparison for consistency
                    is_math = TestService._is_math_question(question["question_text"])
                    
                    if is_math:
                        # Compute correct answer value
                        correct_answer_value = TestService._compute_correct_answer(question["question_text"], question_type)
                        if correct_answer_value is not None:
                            # Extract value from user's selected option
                            user_option_value = TestService._extract_math_value(user_option.get("option_text", ""))
                            if user_option_value is not None:
                                # Compare values (with tolerance for floating point)
                                is_correct = abs(user_option_value - correct_answer_value) < 0.0001
                            else:
                                # Can't extract value, check if option text matches any correct option
                                user_option_text = user_option.get("option_text", "").strip()
                                is_correct = False
                                for opt in question["options"]:
                                    if opt.get("option_text", "").strip() == user_option_text:
                                        opt_value = TestService._extract_math_value(opt.get("option_text", ""))
                                        if opt_value is not None and abs(opt_value - correct_answer_value) < 0.0001:
                                            is_correct = True
                                            break
                                if not is_correct:
                                    is_correct = user_selected_id in correct_option_ids
                        else:
                            # Can't compute correct answer, fall back to option ID comparison
                            is_correct = user_selected_id in correct_option_ids
                    else:
                        # Non-math question: compare option text values (normalized)
                        def normalize_string(value: str) -> str:
                            if not isinstance(value, str):
                                return str(value).strip().lower()
                            return value.strip().lower()
                        
                        user_option_text = normalize_string(user_option.get("option_text", ""))
                        # Check if any correct option has the same text
                        is_correct = False
                        for opt in question["options"]:
                            if int(opt["question_option_id"]) in correct_option_ids:
                                correct_option_text = normalize_string(opt.get("option_text", ""))
                                if correct_option_text == user_option_text:
                                    is_correct = True
                                    break
                        # Fallback to option ID comparison
                        if not is_correct:
                            is_correct = user_selected_id in correct_option_ids
        else:  # CHECKLIST
            # CHECKLIST: Mark as correct if user selected at least one correct option
            # Partial correctness is allowed - selecting correct options is rewarded
            # Extra incorrect selections do not automatically fail the question
            is_correct = len(user_option_ids & correct_option_ids) > 0
        
        details.append(TestResultDetail(
            question_id=question_id,
            question_text=question["question_text"],
            question_type=question_type,
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
        quiz_id=quiz_take["quiz_id"],
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


@router.get("/answers/{uqt_id}")
def get_test_answers(uqt_id: int, cursor: RealDictCursor = Depends(get_db)):
    """Get existing answers for a test (for resuming)"""
    
    quiz_take = TestModel.get_quiz_take(cursor, uqt_id)
    
    if not quiz_take:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found"
        )
    
    # Get answers grouped by question_id
    test_answers = TestModel.get_test_answers(cursor, uqt_id)
    
    # Format as { question_id: [option_id1, option_id2, ...] }
    answers_by_question = {}
    for answer in test_answers:
        question_id = answer["question_id"]
        option_id = answer["question_option_id"]
        if question_id not in answers_by_question:
            answers_by_question[question_id] = []
        answers_by_question[question_id].append(option_id)
    
    return {
        "uqt_id": uqt_id,
        "answers": answers_by_question
    }


@router.post("/save-answer/{uqt_id}")
def save_answer(
    uqt_id: int,
    answer_data: SaveAnswerRequest,
    cursor: RealDictCursor = Depends(get_db)
):
    """Save answer for a question during test taking (before final submission)"""
    
    # Verify test exists and is not completed
    quiz_take = TestModel.get_quiz_take(cursor, uqt_id)
    
    if not quiz_take:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found"
        )
    
    # Check if already completed
    if quiz_take.get("completed_time"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot save answers for completed test"
        )
    
    # Save answers (without correctness evaluation - that happens on submission)
    TestModel.save_answers_for_question(
        cursor,
        uqt_id,
        answer_data.question_id,
        answer_data.question_option_ids,
        is_correct=False  # Will be recomputed on submission
    )
    
    return {
        "message": "Answer saved successfully",
        "uqt_id": uqt_id,
        "question_id": answer_data.question_id
    }


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
    
    # Build detailed results using set-based comparison (consistent with evaluation logic)
    details = []
    for question in quiz["questions"]:
        question_id = question["question_id"]
        question_type = question.get("question_type", "RADIO")
        
        # Get user's answers for this question (normalize to integers)
        user_answer_records = [
            ans for ans in test_answers 
            if ans["question_id"] == question_id
        ]
        user_option_ids = set(int(ans["question_option_id"]) for ans in user_answer_records)
        
        user_answers = [ans["option_text"] for ans in user_answer_records]
        
        # CRITICAL: Re-compute correct options deterministically (same as TestService)
        correct_option_ids = TestService._determine_correct_options(
            question["question_text"],
            question_type,
            question["options"]
        )
        
        correct_answers = [
            opt["option_text"] 
            for opt in question["options"] 
            if int(opt["question_option_id"]) in correct_option_ids
        ]
        
        # Evaluate using VALUE-based comparison (same as TestService.evaluate_test)
        if question_type == "RADIO":
            # RADIO: Compare VALUES, not option IDs
            if len(user_option_ids) != 1:
                is_correct = False
            else:
                # Get the value of user's selected option
                user_selected_id = next(iter(user_option_ids))
                user_option = next((opt for opt in question["options"] if int(opt["question_option_id"]) == user_selected_id), None)
                
                if user_option is None:
                    is_correct = False
                else:
                    # Always use value-based comparison for consistency
                    is_math = TestService._is_math_question(question["question_text"])
                    
                    if is_math:
                        # Compute correct answer value
                        correct_answer_value = TestService._compute_correct_answer(question["question_text"], question_type)
                        if correct_answer_value is not None:
                            # Extract value from user's selected option
                            user_option_value = TestService._extract_math_value(user_option.get("option_text", ""))
                            if user_option_value is not None:
                                # Compare values (with tolerance for floating point)
                                is_correct = abs(user_option_value - correct_answer_value) < 0.0001
                            else:
                                # Can't extract value, check if option text matches any correct option
                                user_option_text = user_option.get("option_text", "").strip()
                                is_correct = False
                                for opt in question["options"]:
                                    if opt.get("option_text", "").strip() == user_option_text:
                                        opt_value = TestService._extract_math_value(opt.get("option_text", ""))
                                        if opt_value is not None and abs(opt_value - correct_answer_value) < 0.0001:
                                            is_correct = True
                                            break
                                if not is_correct:
                                    is_correct = user_selected_id in correct_option_ids
                        else:
                            # Can't compute correct answer, fall back to option ID comparison
                            is_correct = user_selected_id in correct_option_ids
                    else:
                        # Non-math question: compare option text values (normalized)
                        def normalize_string(value: str) -> str:
                            if not isinstance(value, str):
                                return str(value).strip().lower()
                            return value.strip().lower()
                        
                        user_option_text = normalize_string(user_option.get("option_text", ""))
                        # Check if any correct option has the same text
                        is_correct = False
                        for opt in question["options"]:
                            if int(opt["question_option_id"]) in correct_option_ids:
                                correct_option_text = normalize_string(opt.get("option_text", ""))
                                if correct_option_text == user_option_text:
                                    is_correct = True
                                    break
                        # Fallback to option ID comparison
                        if not is_correct:
                            is_correct = user_selected_id in correct_option_ids
        else:  # CHECKLIST
            # CHECKLIST: Mark as correct if user selected at least one correct option
            # Partial correctness is allowed - selecting correct options is rewarded
            # Extra incorrect selections do not automatically fail the question
            is_correct = len(user_option_ids & correct_option_ids) > 0
        
        details.append(TestResultDetail(
            question_id=question_id,
            question_text=question["question_text"],
            question_type=question_type,
            user_answers=user_answers,
            correct_answers=correct_answers,
            is_correct=is_correct
        ))
    
    total_questions = quiz_take.get("total_no_questions") or quiz_take.get("total_questions", 0)
    score_percentage = (quiz_take["total_correct"] / total_questions * 100) if total_questions > 0 else 0
    feedback = TestService.get_feedback_message(quiz_take["result"], score_percentage)
    
    return TestResult(
        uqt_id=quiz_take["uqt_id"],
        quiz_id=quiz_take["quiz_id"],
        quiz_name=quiz_take["quiz_name"],
        total_questions=total_questions,
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
    
    print(f"[API] get_user_tests called with user_id: {user_id}")
    tests = TestModel.get_all_user_tests(cursor, user_id)
    print(f"[API] get_user_tests returned {len(tests)} tests from database")
    
    # Map total_no_questions to total_questions for schema compatibility
    # Ensure all required fields are present
    validated_tests = []
    for test in tests:
        if "total_no_questions" in test:
            test["total_questions"] = test.pop("total_no_questions")
        
        # Ensure status is present
        if "status" not in test:
            test["status"] = TestModel._compute_status(test.get("start_time"), test.get("completed_time"))
        
        # Ensure all required TestResponse fields are present
        if "uqt_id" in test and "user_id" in test and "quiz_id" in test:
            validated_tests.append(test)
        else:
            print(f"[API] WARNING: Test missing required fields: {test}")
    
    print(f"[API] get_user_tests validated count: {len(validated_tests)}")
    return validated_tests


@router.get("/user/{user_id}/pending", response_model=List[TestResponse])
def get_pending_tests(user_id: int, cursor: RealDictCursor = Depends(get_db)):
    """Get all pending (incomplete) tests for a user - includes NOT_STARTED and IN_PROGRESS"""
    
    # MANDATORY: Query MUST return all tests where completed_time IS NULL
    # This includes both NOT_STARTED and IN_PROGRESS tests
    tests = TestModel.get_pending_tests(cursor, user_id)
    
    # MANDATORY: Return ALL pending tests including IN_PROGRESS
    # Map total_no_questions to total_questions for schema compatibility
    # Ensure all required fields are present
    validated_tests = []
    for test in tests:
        # Map field name for schema compatibility
        if "total_no_questions" in test:
            test["total_questions"] = test.pop("total_no_questions")
        
        # MANDATORY: Ensure status is computed correctly
        # Query already filters by completed_time IS NULL, so status should be NOT_STARTED or IN_PROGRESS
        if "status" not in test:
            test["status"] = TestModel._compute_status(test.get("start_time"), test.get("completed_time"))
        
        # MANDATORY: Include ALL tests with required fields
        # Do NOT filter by status - include ALL tests returned by query
        if "uqt_id" in test and "user_id" in test and "quiz_id" in test:
            validated_tests.append(test)
    
    return validated_tests


@router.delete("/pending/{uqt_id}")
def delete_pending_test(
    uqt_id: int,
    user_id: int = Query(..., description="User ID deleting the test"),
    cursor: RealDictCursor = Depends(get_db)
):
    """Delete a pending test"""
    
    deleted = TestModel.delete_quiz_take(cursor, uqt_id, user_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pending test not found or already completed"
        )
    
    return {"message": "Pending test deleted successfully"}


@router.delete("/pending/all")
def delete_all_pending_tests(
    user_id: int = Query(..., description="User ID deleting all pending tests"),
    cursor: RealDictCursor = Depends(get_db)
):
    """Delete all pending tests for a user"""
    
    deleted_count = TestModel.delete_all_pending_tests(cursor, user_id)
    
    return {
        "message": f"Successfully deleted {deleted_count} pending test(s)",
        "deleted_count": deleted_count
    }


@router.delete("/completed/all")
def delete_all_completed_tests(
    user_id: int = Query(..., description="User ID deleting all completed tests"),
    cursor: RealDictCursor = Depends(get_db)
):
    """Delete all completed tests for a user"""
    
    deleted_count = TestModel.delete_all_completed_tests(cursor, user_id)
    
    return {
        "message": f"Successfully deleted {deleted_count} completed test(s)",
        "deleted_count": deleted_count
    }


@router.post("/pending/bulk-delete")
def bulk_delete_pending_tests(
    request: BulkDeleteRequest,
    user_id: int = Query(..., description="User ID deleting tests"),
    cursor: RealDictCursor = Depends(get_db)
):
    """Bulk delete specific pending tests by IDs"""
    
    if not request.ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No IDs provided"
        )
    
    deleted_count = TestModel.delete_pending_tests_by_ids(cursor, request.ids, user_id)
    
    return {
        "message": f"Successfully deleted {deleted_count} pending test(s)",
        "deleted_count": deleted_count,
        "requested_count": len(request.ids)
    }


@router.post("/completed/bulk-delete")
def bulk_delete_completed_tests(
    request: BulkDeleteRequest,
    user_id: int = Query(..., description="User ID deleting tests"),
    cursor: RealDictCursor = Depends(get_db)
):
    """Bulk delete specific completed tests by IDs"""
    
    if not request.ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No IDs provided"
        )
    
    deleted_count = TestModel.delete_completed_tests_by_ids(cursor, request.ids, user_id)
    
    return {
        "message": f"Successfully deleted {deleted_count} completed test(s)",
        "deleted_count": deleted_count,
        "requested_count": len(request.ids)
    }


@router.get("/user/{user_id}/completed", response_model=List[TestResponse])
def get_completed_tests(user_id: int, cursor: RealDictCursor = Depends(get_db)):
    """Get all completed tests for a user"""
    
    print(f"[API] get_completed_tests called with user_id: {user_id}")
    tests = TestModel.get_completed_tests(cursor, user_id)
    print(f"[API] get_completed_tests returned {len(tests)} tests from database")
    
    # Map total_no_questions to total_questions for schema compatibility
    # Ensure all required fields are present
    validated_tests = []
    for test in tests:
        if "total_no_questions" in test:
            test["total_questions"] = test.pop("total_no_questions")
        
        # Ensure status is present
        if "status" not in test:
            test["status"] = TestModel._compute_status(test.get("start_time"), test.get("completed_time"))
        
        # Ensure all required TestResponse fields are present
        if "uqt_id" in test and "user_id" in test and "quiz_id" in test:
            validated_tests.append(test)
        else:
            print(f"[API] WARNING: Test missing required fields: {test}")
    
    print(f"[API] get_completed_tests validated count: {len(validated_tests)}")
    if validated_tests:
        print(f"[API] First completed test sample: {validated_tests[0]}")
    
    return validated_tests


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
    
    # Get recent tests (last 5) and map field names
    recent_tests = all_tests[:5]
    for test in recent_tests:
        if "total_no_questions" in test:
            test["total_questions"] = test.pop("total_no_questions")
    
    return TestSummary(
        total_tests_taken=len(all_tests),
        total_tests_completed=len(completed_tests),
        total_tests_pending=len(pending_tests),
        average_score=average_score,
        recent_tests=recent_tests
    )

