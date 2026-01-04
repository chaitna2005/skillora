"""
Prompt Routes
API endpoints for example prompts
"""
from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extras import RealDictCursor
from typing import List
from app.database import get_db
from app.schemas.prompt import ExamplePromptResponse
from app.models.prompt import ExamplePromptModel


router = APIRouter(prefix="/prompts", tags=["Prompts"])


@router.get("/examples", response_model=List[ExamplePromptResponse])
def get_example_prompts(cursor: RealDictCursor = Depends(get_db)):
    """Get all active example prompts ordered by usage_count DESC, created_at DESC"""
    prompts = ExamplePromptModel.get_active_prompts(cursor)
    return prompts


@router.post("/{prompt_id}/use", response_model=ExamplePromptResponse)
def use_prompt(prompt_id: int, cursor: RealDictCursor = Depends(get_db)):
    """Increment usage_count for a prompt"""
    prompt = ExamplePromptModel.increment_usage_count(cursor, prompt_id)
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt not found"
        )
    return prompt

