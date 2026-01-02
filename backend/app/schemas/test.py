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
    uqt_id: int
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

