"""
Quiz Schemas
Pydantic models for quiz-related requests/responses
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum


class DifficultyLevel(str, Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


class QuestionType(str, Enum):
    RADIO = "RADIO"
    CHECKLIST = "CHECKLIST"


class QuizCreate(BaseModel):
    prompt: str
    difficulty_level: DifficultyLevel
    total_no_questions: int = 10


class BulkDeleteRequest(BaseModel):
    ids: List[int]


class QuestionOptionResponse(BaseModel):
    question_option_id: int
    option_text: str
    is_correct: Optional[bool] = None  # Hidden from users during test


class QuestionResponse(BaseModel):
    question_id: int
    question_text: str
    question_type: QuestionType
    options: List[QuestionOptionResponse] = []


class QuizResponse(BaseModel):
    quiz_id: int
    user_id: int
    quiz_name: str
    prompt: str
    total_no_questions: int
    difficulty_level: DifficultyLevel
    created_date: datetime
    questions: Optional[List[QuestionResponse]] = None


class QuizAssignmentCreate(BaseModel):
    user_id: int  # Student to assign to
    quiz_id: int
    due_date: Optional[datetime] = None


class QuizAssignmentResponse(BaseModel):
    quiz_assignment_id: int
    user_id: Optional[int] = None
    assigned_by: int
    quiz_id: int
    assign_date: datetime
    due_date: Optional[datetime] = None
    share_token: Optional[str] = None


class ShareLinkResponse(BaseModel):
    share_token: str
    share_url: str
    quiz_assignment_id: int


class AssignmentResultResponse(BaseModel):
    quiz_assignment_id: int
    quiz_id: int
    quiz_name: str
    student_id: int
    student_name: str
    uqt_id: Optional[int] = None
    completed_time: Optional[datetime] = None
    total_correct: Optional[int] = None
    result: Optional[str] = None
    total_questions: int
    attempt_status: str


class AssignmentInfoResponse(BaseModel):
    quiz_id: int
    quiz_name: str
    total_questions: int
    difficulty_level: str
    valid: bool
    message: Optional[str] = None


class ClaimAssignmentResponse(BaseModel):
    success: bool
    message: str
    assignment: Optional[QuizAssignmentResponse] = None


class QuizAnalyticsResponse(BaseModel):
    quiz_id: int
    quiz_name: str
    total_students: int
    attempted: int
    average_score: float
    highest_score: float
    lowest_score: float
    total_questions: int


class QuestionDifficultyResponse(BaseModel):
    question_id: int
    question_text: str
    total_attempts: int
    incorrect_percentage: float

