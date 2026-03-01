-- ================================================
-- TestMyKnowledge Database Schema
-- Single PostgreSQL DDL for clean setup (Docker + local)
-- ================================================

DROP TABLE IF EXISTS "Quiz_Take_Question_Answers" CASCADE;
DROP TABLE IF EXISTS "User_Quiz_Take" CASCADE;
DROP TABLE IF EXISTS "QuestionOption" CASCADE;
DROP TABLE IF EXISTS "Question" CASCADE;
DROP TABLE IF EXISTS "Quiz_Assignment" CASCADE;
DROP TABLE IF EXISTS "Quiz" CASCADE;
DROP TABLE IF EXISTS "User_Stats" CASCADE;
DROP TABLE IF EXISTS "User" CASCADE;

-- ================================================
-- User
-- ================================================
CREATE TABLE "User" (
    user_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    username VARCHAR(150) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    email_id VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('TEACHER', 'STUDENT')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    quiz_completion_count INTEGER DEFAULT 0,
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    last_active_date DATE,
    unlocked_badges TEXT[] DEFAULT ARRAY[]::TEXT[]
);

-- ================================================
-- User_Stats (gamification)
-- ================================================
CREATE TABLE "User_Stats" (
    user_id INTEGER PRIMARY KEY REFERENCES "User"(user_id) ON DELETE CASCADE,
    quiz_completion_count INTEGER DEFAULT 0,
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    last_active_date DATE,
    unlocked_badges TEXT[] DEFAULT ARRAY[]::TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================
-- Quiz
-- ================================================
CREATE TABLE "Quiz" (
    quiz_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES "User"(user_id) ON DELETE CASCADE,
    prompt TEXT NOT NULL,
    total_no_questions INTEGER NOT NULL,
    difficulty_level VARCHAR(20) NOT NULL CHECK (difficulty_level IN ('EASY', 'MEDIUM', 'HARD')),
    quiz_name VARCHAR(255) NOT NULL,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================
-- Example_Prompt
-- ================================================
CREATE TABLE "Example_Prompt" (
    prompt_id SERIAL PRIMARY KEY,
    prompt_text TEXT NOT NULL UNIQUE,
    created_by INTEGER REFERENCES "User"(user_id) ON DELETE SET NULL,
    usage_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================
-- Quiz_Assignment (user_id nullable for share links)
-- ================================================
CREATE TABLE "Quiz_Assignment" (
    quiz_assignment_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES "User"(user_id) ON DELETE CASCADE,
    assigned_by INTEGER NOT NULL REFERENCES "User"(user_id) ON DELETE CASCADE,
    quiz_id INTEGER NOT NULL REFERENCES "Quiz"(quiz_id) ON DELETE CASCADE,
    assign_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    due_date TIMESTAMP,
    share_token VARCHAR(255) UNIQUE
);

-- ================================================
-- Question
-- ================================================
CREATE TABLE "Question" (
    question_id SERIAL PRIMARY KEY,
    quiz_id INTEGER NOT NULL REFERENCES "Quiz"(quiz_id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    question_type VARCHAR(20) NOT NULL CHECK (question_type IN ('RADIO', 'CHECKLIST'))
);

-- ================================================
-- QuestionOption
-- ================================================
CREATE TABLE "QuestionOption" (
    question_option_id SERIAL PRIMARY KEY,
    question_id INTEGER NOT NULL REFERENCES "Question"(question_id) ON DELETE CASCADE,
    option_text TEXT NOT NULL,
    is_correct BOOLEAN NOT NULL DEFAULT FALSE
);

-- ================================================
-- User_Quiz_Take (resume: current_question_index)
-- ================================================
CREATE TABLE "User_Quiz_Take" (
    uqt_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES "User"(user_id) ON DELETE CASCADE,
    quiz_id INTEGER NOT NULL REFERENCES "Quiz"(quiz_id) ON DELETE CASCADE,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_time TIMESTAMP,
    total_correct INTEGER,
    result VARCHAR(50),
    quiz_assignment_id INTEGER REFERENCES "Quiz_Assignment"(quiz_assignment_id) ON DELETE SET NULL,
    current_question_index INTEGER DEFAULT 0
);

-- ================================================
-- Quiz_Take_Question_Answers
-- ================================================
CREATE TABLE "Quiz_Take_Question_Answers" (
    qtqa_id SERIAL PRIMARY KEY,
    uqt_id INTEGER NOT NULL REFERENCES "User_Quiz_Take"(uqt_id) ON DELETE CASCADE,
    question_id INTEGER NOT NULL REFERENCES "Question"(question_id) ON DELETE CASCADE,
    question_option_id INTEGER NOT NULL REFERENCES "QuestionOption"(question_option_id) ON DELETE CASCADE,
    is_correct BOOLEAN NOT NULL DEFAULT FALSE
);

-- ================================================
-- Indexes
-- ================================================
CREATE INDEX idx_quiz_user_id ON "Quiz"(user_id);
CREATE INDEX idx_question_quiz_id ON "Question"(quiz_id);
CREATE INDEX idx_question_option_question_id ON "QuestionOption"(question_id);
CREATE INDEX idx_user_quiz_take_user_id ON "User_Quiz_Take"(user_id);
CREATE INDEX idx_user_quiz_take_quiz_id ON "User_Quiz_Take"(quiz_id);
CREATE INDEX idx_user_quiz_take_resume ON "User_Quiz_Take"(user_id, quiz_id, completed_time) WHERE completed_time IS NULL;
CREATE INDEX idx_quiz_assignment_user_id ON "Quiz_Assignment"(user_id);
CREATE INDEX idx_quiz_assignment_quiz_id ON "Quiz_Assignment"(quiz_id);
CREATE INDEX idx_quiz_assignment_share_token ON "Quiz_Assignment"(share_token);
CREATE INDEX idx_user_last_active_date ON "User"(last_active_date);
CREATE INDEX idx_qtqa_uqt_id ON "Quiz_Take_Question_Answers"(uqt_id);
