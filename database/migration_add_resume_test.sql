-- ================================================
-- Migration: Add Resume Test Support
-- Adds current_question_index to User_Quiz_Take table
-- ================================================

-- Add current_question_index column to track user's progress
ALTER TABLE "User_Quiz_Take" 
ADD COLUMN IF NOT EXISTS current_question_index INTEGER DEFAULT 0;

-- Add index for performance
CREATE INDEX IF NOT EXISTS idx_user_quiz_take_resume 
ON "User_Quiz_Take"(user_id, quiz_id, completed_time) 
WHERE completed_time IS NULL;

-- Add comment for documentation
COMMENT ON COLUMN "User_Quiz_Take".current_question_index IS 
'Tracks the current question index (0-based) for resume functionality. Updated on every question navigation.';
