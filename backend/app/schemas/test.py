"""
Test Schemas
Pydantic models for test-related requests/responses
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class TestStart(BaseModel):
    quiz_id: int
    quiz_assignment_id: Optional[int] = None


class TestAnswer(BaseModel):
    question_id: int
    question_option_ids: List[int]  # Can be multiple for CHECKLIST type


class SaveAnswerRequest(BaseModel):
    question_id: int
    question_option_ids: List[int]  # Can be multiple for CHECKLIST type


class TestSubmit(BaseModel):
    uqt_id: Optional[int] = None  # Optional - will use user_id + quiz_id if not provided
    user_id: int  # Required to identify user
    quiz_id: int  # Required to identify quiz
    answers: List[TestAnswer]


class BulkDeleteRequest(BaseModel):
    ids: List[int]


class TestResponse(BaseModel):
    uqt_id: int
    user_id: int
    quiz_id: int
    quiz_name: Optional[str] = None
    start_time: Optional[datetime] = None
    completed_time: Optional[datetime] = None
    total_correct: Optional[int] = None
    total_questions: Optional[int] = None
    result: Optional[str] = None
    status: str  # NOT_STARTED, IN_PROGRESS, or COMPLETED


class TestResultDetail(BaseModel):
    question_id: int
    question_text: str
    question_type: str
    user_answers: List[str]
    correct_answers: List[str]
    is_correct: bool
    feedback: Optional[str] = None  # AI-generated explanation for the answer


class TestResult(BaseModel):
    uqt_id: int
    quiz_id: int
    quiz_name: str
    total_questions: int
    total_correct: int
    score_percentage: float
    result: str
    feedback: str
    start_time: datetime
    completed_time: datetime
    details: List[TestResultDetail] = []


class TestSummary(BaseModel):
    total_tests_taken: int
    total_tests_completed: int
    total_tests_pending: int
    average_score: Optional[float] = None
    recent_tests: List[TestResponse] = []


class HintRequest(BaseModel):
    question_text: str
    options: List[str]  # List of option texts (without revealing which is correct)


class HintResponse(BaseModel):
    hint: str
    question_id: int


class SaveProgressRequest(BaseModel):
    """Request to save test progress for resume functionality"""
    uqt_id: int
    current_question_index: int
    answers: dict  # Dict[question_id: List[option_ids]]


class ProgressResponse(BaseModel):
    """Response with saved progress data"""
    success: bool
    message: str
    current_question_index: Optional[int] = 0
    answers: Optional[dict] = {}


class ResumeTestResponse(BaseModel):
    """Response for resuming a test"""
    uqt_id: int
    quiz_id: int
    user_id: int
    has_progress: bool
    current_question_index: int
    answers: dict  # Dict[question_id: List[option_ids]]
    status: str
