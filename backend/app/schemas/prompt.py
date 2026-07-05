"""
Prompt Schemas
Pydantic models for prompt-related requests/responses
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ExamplePromptResponse(BaseModel):
    prompt_id: int
    prompt_text: str
    created_by: Optional[int]
    usage_count: int
    is_active: bool
    created_at: datetime

