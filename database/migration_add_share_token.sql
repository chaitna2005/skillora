-- Migration: Add share_token to Quiz_Assignment and make user_id nullable
-- This enables shareable quiz assignment links

ALTER TABLE "Quiz_Assignment" 
ADD COLUMN IF NOT EXISTS share_token VARCHAR(255) UNIQUE;

-- Make user_id nullable to allow unclaimed assignments
ALTER TABLE "Quiz_Assignment" 
ALTER COLUMN user_id DROP NOT NULL;

-- Create index for share_token lookups
CREATE INDEX IF NOT EXISTS idx_quiz_assignment_share_token ON "Quiz_Assignment"(share_token);

