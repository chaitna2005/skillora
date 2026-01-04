-- Migration: Add Badges and Streaks to User Table
-- Adds columns for tracking user gamification stats

ALTER TABLE "User"
ADD COLUMN IF NOT EXISTS quiz_completion_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS current_streak INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS longest_streak INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_active_date DATE,
ADD COLUMN IF NOT EXISTS unlocked_badges TEXT[] DEFAULT ARRAY[]::TEXT[];

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_user_last_active_date ON "User"(last_active_date);

-- Initialize existing users with default values (if needed)
UPDATE "User"
SET 
    quiz_completion_count = COALESCE(quiz_completion_count, 0),
    current_streak = COALESCE(current_streak, 0),
    longest_streak = COALESCE(longest_streak, 0),
    unlocked_badges = COALESCE(unlocked_badges, ARRAY[]::TEXT[])
WHERE quiz_completion_count IS NULL;

