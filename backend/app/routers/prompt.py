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
def get_example_prompts(
    user_id: int,
    cursor: RealDictCursor = Depends(get_db)
):
    """Get active example prompts created by the specified user"""
    prompts = ExamplePromptModel.get_user_prompts(cursor, user_id)
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


@router.delete("/{prompt_id}")
def delete_prompt(
    prompt_id: int,
    user_id: int,
    cursor: RealDictCursor = Depends(get_db)
):
    """Delete a specific prompt (only if owned by user)"""
    deleted = ExamplePromptModel.delete_prompt(cursor, prompt_id, user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt not found or you don't have permission to delete it"
        )
    return {"message": "Prompt deleted successfully"}


@router.post("/bulk-delete")
def delete_prompts_bulk(
    prompt_ids: List[int],
    user_id: int,
    cursor: RealDictCursor = Depends(get_db)
):
    """Delete multiple prompts (only if owned by user)"""
    deleted_count = ExamplePromptModel.delete_prompts_bulk(cursor, prompt_ids, user_id)
    return {
        "message": f"Successfully deleted {deleted_count} prompt(s)",
        "deleted_count": deleted_count
    }

