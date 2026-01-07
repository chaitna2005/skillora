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
    SaveAnswerRequest,
    HintRequest,
    HintResponse
)
from app.models.test import TestModel
from app.models.question import QuestionModel
from app.models.user import UserModel
from app.services.test_service import TestService
from app.services.openai_service_direct import OpenAIService
from app.services.user_stats_service import UserStatsService
from typing import Dict, List


router = APIRouter(prefix="/test", tags=["Test"])


def _generate_feedback_for_details(
    details: List[TestResultDetail],
    quiz_questions: List[Dict]
) -> List[TestResultDetail]:
    """Generate AI feedback for each question detail
    
    This function adds feedback to each TestResultDetail by calling the OpenAI service.
    If LLM fails, fallback feedback is used.
    
    IMPORTANT: This function should be wrapped in try/except by the caller.
    It may raise exceptions that should not block test submission.
    """
    print(f"[DEBUG] _generate_feedback_for_details called with {len(details)} details")
    
    try:
        openai_service = OpenAIService()
        print("[DEBUG] OpenAI service initialized successfully")
    except Exception as e:
        print(f"[ERROR] Failed to initialize OpenAI service for feedback: {e}")
        import traceback
        traceback.print_exc()
        # Return details with fallback feedback
        try:
            return [
                TestResultDetail(
                    question_id=detail.question_id,
                    question_text=detail.question_text,
                    question_type=detail.question_type,
                    user_answers=detail.user_answers,
                    correct_answers=detail.correct_answers,
                    is_correct=detail.is_correct,
                    feedback="Review the key concepts related to this question to improve your understanding."
                )
                for detail in details
            ]
        except Exception as e2:
            print(f"[ERROR] Failed to create fallback details: {e2}")
            raise  # Re-raise if we can't even create fallback
    
    # Create a mapping of question_id to question data for quick lookup
    question_map = {q["question_id"]: q for q in quiz_questions}
    
    updated_details = []
    for detail in details:
        try:
            question_data = question_map.get(detail.question_id)
            if not question_data:
                # If question not found, use fallback
                print(f"[WARN] Question data not found for question_id {detail.question_id}")
                updated_details.append(TestResultDetail(
                    question_id=detail.question_id,
                    question_text=detail.question_text,
                    question_type=detail.question_type,
                    user_answers=detail.user_answers,
                    correct_answers=detail.correct_answers,
                    is_correct=detail.is_correct,
                    feedback="Review the key concepts related to this question to improve your understanding."
                ))
                continue
            
            # Get option texts
            option_texts = [opt.get("option_text", "") for opt in question_data.get("options", [])]
            
            # Get user answer text (first answer if multiple)
            user_answer_text = detail.user_answers[0] if detail.user_answers else "No answer provided"
            
            # Get correct answer text (first correct answer if multiple)
            correct_answer_text = detail.correct_answers[0] if detail.correct_answers else "Unknown"
            
            try:
                print(f"[DEBUG] Generating feedback for question {detail.question_id}")
                feedback_text = openai_service.generate_question_feedback(
                    question_text=detail.question_text,
                    options=option_texts,
                    user_answer=user_answer_text,
                    correct_answer=correct_answer_text,
                    is_correct=detail.is_correct
                )
                print(f"[DEBUG] Successfully generated feedback for question {detail.question_id}")
            except Exception as e:
                print(f"[ERROR] Error generating feedback for question {detail.question_id}: {e}")
                # Use fallback feedback
                feedback_text = "Unable to generate explanation. Please review the question and related topic concepts."
            
            updated_details.append(TestResultDetail(
                question_id=detail.question_id,
                question_text=detail.question_text,
                question_type=detail.question_type,
                user_answers=detail.user_answers,
                correct_answers=detail.correct_answers,
                is_correct=detail.is_correct,
                feedback=feedback_text
            ))
        except Exception as e:
            print(f"[ERROR] Error processing detail for question {detail.question_id}: {e}")
            # Even if individual detail processing fails, continue with fallback
            updated_details.append(TestResultDetail(
                question_id=detail.question_id,
                question_text=detail.question_text,
                question_type=detail.question_type,
                user_answers=detail.user_answers,
                correct_answers=detail.correct_answers,
                is_correct=detail.is_correct,
                feedback=None  # Set to None if we can't generate feedback
            ))
    
    print(f"[DEBUG] _generate_feedback_for_details returning {len(updated_details)} details")
    return updated_details


@router.post("/start", response_model=TestResponse, status_code=status.HTTP_201_CREATED)
def start_test(
    test_data: TestStart,
    user_id: int = Query(..., description="User ID starting the test"),
    cursor: RealDictCursor = Depends(get_db)
):
    """Start a new test attempt or resume existing pending test
    
    CRITICAL: Prevents duplicate attempts by ALWAYS checking for existing pending test first.
    
    Business Rules:
    - ALWAYS check for existing pending test (completed_time IS NULL) BEFORE creating new one
    - If existing pending test found: Resume it (return existing uqt_id)
    - If NO existing pending test: Create ONE new test attempt
    - This ensures ONLY ONE attempt exists per quiz+user+assignment combination
    """
    
    print(f"[DEBUG] start_test called: user_id={user_id}, quiz_id={test_data.quiz_id}, assignment_id={test_data.quiz_assignment_id}")
    
    # Handle quiz_assignment_id - convert 0 or None to None (NULL in DB)
    assignment_id = test_data.quiz_assignment_id
    if assignment_id is not None and assignment_id <= 0:
        assignment_id = None
    
    # CRITICAL: ALWAYS check for existing pending test FIRST (regardless of assignment_id)
    # This prevents duplicate attempts from being created
    existing_test = TestModel.get_pending_test_for_quiz(
        cursor, 
        user_id, 
        test_data.quiz_id, 
        assignment_id
    )
    
    if existing_test:
        # Found existing pending test - resume it (DO NOT create duplicate)
        print(f"[DEBUG] Found existing pending test: uqt_id={existing_test.get('uqt_id')}, resuming...")
        
        # Update to IN_PROGRESS if it's NOT_STARTED
        if existing_test.get("start_time") is None:
            updated_test = TestModel.update_test_to_in_progress(cursor, existing_test["uqt_id"])
            if updated_test:
                quiz_take = TestModel.get_quiz_take(cursor, updated_test["uqt_id"])
                print(f"[DEBUG] Updated NOT_STARTED to IN_PROGRESS: uqt_id={quiz_take.get('uqt_id')}")
                return quiz_take
        
        # Return existing test (already IN_PROGRESS)
        quiz_take = TestModel.get_quiz_take(cursor, existing_test["uqt_id"])
        print(f"[DEBUG] Resuming existing test: uqt_id={quiz_take.get('uqt_id')}")
        return quiz_take
    
    # NO existing pending test found - CREATE ONE new test attempt
    print(f"[DEBUG] No existing pending test found, creating new attempt...")
    take_data = {
        "user_id": user_id,
        "quiz_id": test_data.quiz_id,
        "quiz_assignment_id": assignment_id
    }
    
    # CRITICAL: Create ONLY ONE new attempt
    quiz_take = TestModel.create_quiz_take(cursor, take_data, set_start_time=True)
    
    # MANDATORY: Verify record was created
    if not quiz_take or not quiz_take.get("uqt_id"):
        print(f"[ERROR] Failed to create test attempt")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create test attempt"
        )
    
    print(f"[DEBUG] Created new test attempt: uqt_id={quiz_take.get('uqt_id')}")
    
    # Ensure status is IN_PROGRESS
    if quiz_take.get("status") != "IN_PROGRESS":
        quiz_take["status"] = "IN_PROGRESS"
    
    # Transaction commits automatically via get_db dependency when function returns
    return quiz_take


@router.post("/submit", response_model=TestResult)
def submit_test(
    submission: TestSubmit,
    cursor: RealDictCursor = Depends(get_db)
):
    """Submit test answers and get results
    
    CRITICAL: This endpoint ONLY UPDATES existing User_Quiz_Take records.
    It NEVER creates new records. Only start_test endpoint creates records.
    
    Flow:
    1. Fetch the MOST RECENT unfinished attempt by user_id + quiz_id
    2. Verify attempt exists and is not already completed
    3. Evaluate answers
    4. UPDATE the SAME ROW: SET completed_time = NOW(), total_correct, result
    5. Commit immediately
    6. Return results
    """
    
    print("=" * 60)
    print("SUBMIT TEST - Fetching most recent unfinished attempt")
    print(f"  - user_id: {submission.user_id}")
    print(f"  - quiz_id: {submission.quiz_id}")
    print(f"  - uqt_id (optional): {submission.uqt_id}")
    print("=" * 60)
    
    # MANDATORY: Validate user_id and quiz_id
    if not submission.user_id or submission.user_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user_id"
        )
    
    if not submission.quiz_id or submission.quiz_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid quiz_id"
        )
    
    # CRITICAL: Fetch the MOST RECENT unfinished attempt
    # Filter by user_id, quiz_id, and completed_time IS NULL
    # Order by start_time DESC to get the most recent
    quiz_take = TestModel.get_most_recent_unfinished_attempt(
        cursor, 
        submission.user_id, 
        submission.quiz_id
    )
    
    # MANDATORY: Verify attempt found
    if not quiz_take:
        print("[ERROR] No active attempt found")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active attempt found"
        )
    
    print("ATTEMPT FOUND:", quiz_take.get('uqt_id'))
    print(f"  - uqt_id: {quiz_take.get('uqt_id')}")
    print(f"  - user_id: {quiz_take.get('user_id')}")
    print(f"  - quiz_id: {quiz_take.get('quiz_id')}")
    print(f"  - start_time: {quiz_take.get('start_time')}")
    print(f"  - completed_time (BEFORE): {quiz_take.get('completed_time')}")
    print("=" * 60)
    
    # CRITICAL: Verify test is not already completed (completed_time IS NULL)
    # Use completed_time as single source of truth
    if quiz_take.get("completed_time"):
        print(f"[ERROR] Test already completed for uqt_id: {quiz_take.get('uqt_id')}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Test already submitted"
        )
    
    # Store uqt_id for evaluation
    uqt_id = quiz_take.get('uqt_id')
    
    # Validate submission has answers
    if not submission.answers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No answers provided"
        )
    
    # Format answers for evaluation
    answers = [
        {
            "question_id": ans.question_id,
            "question_option_ids": ans.question_option_ids
        }
        for ans in submission.answers
    ]
    
    print(f"[DEBUG] Evaluating {len(answers)} answers for uqt_id: {uqt_id}")
    
    try:
        # CRITICAL: evaluate_test UPDATES existing record via complete_quiz_take
        # complete_quiz_take does: UPDATE ... WHERE uqt_id = %s
        # This is the ONLY way completed_time is set - NO INSERT happens here
        # MANDATORY: This call will execute UPDATE and set completed_time
        print("CALLING evaluate_test (will UPDATE completed_time)...")
        evaluation = TestService.evaluate_test(cursor, uqt_id, answers)
        print(f"[DEBUG] Evaluation completed: total_correct={evaluation.get('total_correct')}, result={evaluation.get('result')}")
        print("evaluate_test RETURNED - UPDATE should be committed")
    except Exception as e:
        print(f"[ERROR] Test evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate test: {str(e)}"
        )
    
    # CRITICAL: Get updated quiz take AFTER evaluation
    # Evaluation sets completed_time = NOW() via UPDATE, so quiz_take now has completed_time
    # Re-fetch to get the updated record with completed_time
    print("RE-FETCHING attempt after UPDATE to verify completed_time...")
    quiz_take = TestModel.get_quiz_take(cursor, uqt_id)
    
    # CRITICAL: Verify completion was set on the SAME uqt_id (not a new record)
    if not quiz_take:
        print(f"[ERROR] Test not found after evaluation for uqt_id: {uqt_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Test not found after evaluation"
        )
    
    # Verify the uqt_id matches (ensures we didn't create a new record)
    if quiz_take.get("uqt_id") != uqt_id:
        print(f"[ERROR] uqt_id mismatch: expected {uqt_id}, got {quiz_take.get('uqt_id')}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Test ID mismatch after evaluation"
        )
    
    # MANDATORY DEBUG LOG: Verify completed_time was set
    print(f"VERIFICATION - completed_time (AFTER UPDATE): {quiz_take.get('completed_time')}")
    
    # Verify completed_time was set (this confirms UPDATE succeeded)
    if not quiz_take.get("completed_time"):
        print(f"[ERROR] Test evaluation succeeded but completed_time was not set for uqt_id: {uqt_id}")
        print(f"[ERROR] This indicates UPDATE did not set completed_time or commit failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Test evaluation completed but completion was not recorded"
        )
    
    print(f"[SUCCESS] Test successfully completed:")
    print(f"  - uqt_id: {quiz_take.get('uqt_id')}")
    print(f"  - completed_time: {quiz_take.get('completed_time')}")
    print(f"  - total_correct: {quiz_take.get('total_correct')}")
    print(f"  - result: {quiz_take.get('result')}")
    print("=" * 60)
    print("COMMIT DONE (committed automatically when function returns)")
    print("=" * 60)
    
    # Get detailed results
    # Shuffle questions and options for test integrity
    # Use uqt_id as seed for deterministic shuffling (consistent order per attempt)
    quiz = QuestionModel.get_quiz_with_questions(
        cursor, 
        quiz_take["quiz_id"], 
        shuffle=True, 
        seed=submission.uqt_id
    )
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
            # CHECKLIST: Exact match required - user must select ALL correct options and NO incorrect options
            # No partial marks
            is_correct = user_option_ids == correct_option_ids
        
        details.append(TestResultDetail(
            question_id=question_id,
            question_text=question["question_text"],
            question_type=question_type,
            user_answers=user_answers,
            correct_answers=correct_answers,
            is_correct=is_correct
        ))
    
    # Generate overall feedback message (this is safe and doesn't depend on AI)
    feedback = TestService.get_feedback_message(
        evaluation["result"],
        evaluation["score_percentage"]
    )
    
    # Generate AI feedback for each question (OPTIONAL - must not block submission)
    # This happens AFTER score calculation and database save
    print(f"[DEBUG] Starting AI feedback generation for {len(details)} questions")
    details_with_feedback = details  # Default to details without feedback
    
    try:
        details_with_feedback = _generate_feedback_for_details(details, quiz["questions"])
        print(f"[DEBUG] Successfully generated feedback for {len(details_with_feedback)} questions")
    except Exception as e:
        # CRITICAL: Log error but DO NOT fail submission
        print(f"[ERROR] AI feedback generation failed (non-blocking): {e}")
        import traceback
        traceback.print_exc()
        # Use details without feedback - submission still succeeds
        # Add null feedback to each detail to maintain schema consistency
        details_with_feedback = [
            TestResultDetail(
                question_id=detail.question_id,
                question_text=detail.question_text,
                question_type=detail.question_type,
                user_answers=detail.user_answers,
                correct_answers=detail.correct_answers,
                is_correct=detail.is_correct,
                feedback=None  # Explicitly set to None on failure
            )
            for detail in details
        ]
        print(f"[DEBUG] Using details without AI feedback - submission will succeed")
    
    # Update user stats (badges and streaks) - NON-BLOCKING
    # This happens AFTER successful quiz submission
    stats_update_result = None
    try:
        print(f"[DEBUG] Updating stats for user {quiz_take['user_id']}")
        stats_update_result = UserStatsService.update_stats_on_quiz_completion(
            cursor,
            quiz_take["user_id"]
        )
        print(f"[DEBUG] Stats updated: {stats_update_result}")
    except Exception as e:
        # CRITICAL: Stats update failure should NOT block submission
        print(f"[ERROR] Failed to update user stats (non-blocking): {e}")
        import traceback
        traceback.print_exc()
    
    # CRITICAL: Return success response regardless of stats update status
    result = TestResult(
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
        details=details_with_feedback
    )
    
    # Add stats update info to response if available (for frontend badge notification)
    if stats_update_result and stats_update_result.get("newly_unlocked_badges"):
        # Store in a way that frontend can access (we'll add this to response model later)
        # For now, we'll add it as an optional field
        pass  # Will handle in frontend via separate API call
    
    return result


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


@router.post("/hint/{question_id}", response_model=HintResponse)
def get_hint(
    question_id: int,
    hint_request: HintRequest,
    cursor: RealDictCursor = Depends(get_db)
):
    """Generate a helpful hint for a question during quiz attempt
    
    This endpoint generates hints dynamically using LLM without revealing the correct answer.
    Hints are educational and guide students toward understanding the concept.
    """
    
    try:
        # Initialize OpenAI service
        openai_service = OpenAIService()
        
        # Generate hint using LLM
        hint_text = openai_service.generate_hint(
            question_text=hint_request.question_text,
            options=hint_request.options
        )
        
        return HintResponse(
            hint=hint_text,
            question_id=question_id
        )
        
    except Exception as e:
        # If LLM fails, return fallback hint
        print(f"Error generating hint: {e}")
        fallback_hint = "Think carefully about the key concepts related to this question. Consider what you know about the topic and how it applies here."
        
        return HintResponse(
            hint=fallback_hint,
            question_id=question_id
        )


@router.get("/result", response_model=TestResult)
def get_test_result(
    user_id: int = Query(..., description="User ID"),
    quiz_id: int = Query(..., description="Quiz ID"),
    cursor: RealDictCursor = Depends(get_db)
):
    """Get detailed results for a completed test - READ ONLY
    
    CRITICAL: Fetches the LATEST COMPLETED attempt by user_id and quiz_id.
    Ignores uqt_id completely. Only returns results where completed_time IS NOT NULL.
    
    Behavior:
    - Fetches latest completed attempt (completed_time IS NOT NULL)
    - Orders by completed_time DESC to get most recent
    - If no completed attempt found, returns "Test not yet completed"
    """
    
    print("=" * 60)
    print(f"[DEBUG] get_test_result called with user_id: {user_id}, quiz_id: {quiz_id}")
    print("=" * 60)
    
    # MANDATORY: Fetch the LATEST COMPLETED attempt
    # Filter by user_id, quiz_id, and completed_time IS NOT NULL
    # Order by completed_time DESC to get the most recent completion
    quiz_take = TestModel.get_latest_completed_attempt(cursor, user_id, quiz_id)
    
    if not quiz_take:
        print(f"[ERROR] No completed attempt found for user_id: {user_id}, quiz_id: {quiz_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Test not yet completed"
        )
    
    print(f"[DEBUG] Found completed attempt: uqt_id={quiz_take.get('uqt_id')}, completed_time={quiz_take.get('completed_time')}")
    
    # CRITICAL: Verify completed_time is set (double-check)
    if not quiz_take.get("completed_time"):
        print(f"[ERROR] Attempt found but completed_time is NULL for uqt_id: {quiz_take.get('uqt_id')}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Test not yet completed"
        )
    
    uqt_id = quiz_take.get('uqt_id')
    
    # Step 2: Get quiz with questions
    quiz_id = quiz_take.get("quiz_id")
    if not quiz_id:
        print(f"[ERROR] quiz_id missing in quiz_take for uqt_id: {uqt_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid test data: quiz_id missing"
        )
    
    print(f"[DEBUG] Fetching quiz with questions for quiz_id: {quiz_id}")
    quiz = QuestionModel.get_quiz_with_questions(
        cursor, 
        quiz_id, 
        shuffle=True, 
        seed=uqt_id
    )
    
    if not quiz:
        print(f"[ERROR] Quiz not found for quiz_id: {quiz_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    if not quiz.get("questions") or len(quiz.get("questions", [])) == 0:
        print(f"[ERROR] Quiz has no questions for quiz_id: {quiz_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Quiz has no questions"
        )
    
    print(f"[DEBUG] Quiz retrieved with {len(quiz.get('questions', []))} questions")
    
    # Step 3: Get test answers
    test_answers = TestModel.get_test_answers(cursor, uqt_id)
    print(f"[DEBUG] Retrieved {len(test_answers) if test_answers else 0} test answers")
    
    if not test_answers:
        test_answers = []  # Ensure it's a list, not None
    
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
            # CHECKLIST: Exact match required - user must select ALL correct options and NO incorrect options
            # No partial marks
            is_correct = user_option_ids == correct_option_ids
        
        details.append(TestResultDetail(
            question_id=question_id,
            question_text=question.get("question_text", ""),
            question_type=question_type,
            user_answers=user_answers if user_answers else [],
            correct_answers=correct_answers if correct_answers else [],
            is_correct=is_correct
        ))
    
    print(f"[DEBUG] Built {len(details)} question details")
    
    # Step 5: Calculate totals and feedback (safe with defaults)
    total_questions = quiz_take.get("total_no_questions") or quiz_take.get("total_questions") or len(details) or 0
    total_correct = quiz_take.get("total_correct") or 0
    score_percentage = (total_correct / total_questions * 100) if total_questions > 0 else 0.0
    
    # Safe feedback message generation
    result_text = quiz_take.get("result") or "PENDING"
    try:
        feedback = TestService.get_feedback_message(result_text, score_percentage)
    except Exception as e:
        print(f"[WARN] Failed to generate feedback message: {e}")
        feedback = "Review your results to see how you did!"
    
    # Step 6: Generate AI feedback for each question (OPTIONAL - must not block result retrieval)
    print(f"[DEBUG] Starting AI feedback generation for {len(details)} questions in get_test_result")
    details_with_feedback = details  # Default to details without feedback
    
    try:
        if quiz and quiz.get("questions"):
            details_with_feedback = _generate_feedback_for_details(details, quiz["questions"])
            print(f"[DEBUG] Successfully generated feedback for {len(details_with_feedback)} questions")
        else:
            print(f"[WARN] Quiz or questions missing, skipping AI feedback generation")
    except Exception as e:
        # CRITICAL: Log error but DO NOT fail result retrieval
        print(f"[ERROR] AI feedback generation failed (non-blocking) in get_test_result: {e}")
        import traceback
        traceback.print_exc()
        # Use details without feedback - result retrieval still succeeds
        details_with_feedback = [
            TestResultDetail(
                question_id=detail.question_id,
                question_text=detail.question_text,
                question_type=detail.question_type,
                user_answers=detail.user_answers,
                correct_answers=detail.correct_answers,
                is_correct=detail.is_correct,
                feedback=None  # Explicitly set to None on failure
            )
            for detail in details
        ]
        print(f"[DEBUG] Using details without AI feedback - result retrieval will succeed")
    
    # Step 7: Build and return response (ensure all required fields exist)
    quiz_name = quiz_take.get("quiz_name") or quiz.get("quiz_name") or "Unknown Quiz"
    start_time = quiz_take.get("start_time")
    completed_time = quiz_take.get("completed_time")
    
    print(f"[DEBUG] Returning TestResult with {len(details_with_feedback)} details")
    
    return TestResult(
        uqt_id=quiz_take["uqt_id"],
        quiz_id=quiz_id,
        quiz_name=quiz_name,
        total_questions=total_questions,
        total_correct=total_correct,
        score_percentage=round(score_percentage, 1),
        result=result_text,
        feedback=feedback,
        start_time=start_time,
        completed_time=completed_time,
        details=details_with_feedback
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

