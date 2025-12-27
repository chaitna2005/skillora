-- ================================================
-- TestMyKnowledge Database Schema
-- PostgreSQL DDL Script
-- ================================================

-- Drop tables if they exist (for clean setup)
DROP TABLE IF EXISTS "Quiz_Take_Question_Answers" CASCADE;
DROP TABLE IF EXISTS "User_Quiz_Take" CASCADE;
DROP TABLE IF EXISTS "QuestionOption" CASCADE;
DROP TABLE IF EXISTS "Question" CASCADE;
DROP TABLE IF EXISTS "Quiz_Assignment" CASCADE;
DROP TABLE IF EXISTS "Quiz" CASCADE;
DROP TABLE IF EXISTS "User" CASCADE;

-- ================================================
-- User Table
-- Stores user information (Teachers and Students)
-- ================================================
CREATE TABLE "User" (
    user_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    email_id VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('TEACHER', 'STUDENT')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================
-- Quiz Table
-- Stores quiz metadata
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
-- Quiz Assignment Table
-- Tracks quiz assignments from teachers to students
-- ================================================
CREATE TABLE "Quiz_Assignment" (
    quiz_assignment_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES "User"(user_id) ON DELETE CASCADE,
    assigned_by INTEGER NOT NULL REFERENCES "User"(user_id) ON DELETE CASCADE,
    quiz_id INTEGER NOT NULL REFERENCES "Quiz"(quiz_id) ON DELETE CASCADE,
    assign_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    due_date TIMESTAMP
);

-- ================================================
-- Question Table
-- Stores individual questions for each quiz
-- ================================================
CREATE TABLE "Question" (
    question_id SERIAL PRIMARY KEY,
    quiz_id INTEGER NOT NULL REFERENCES "Quiz"(quiz_id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    question_type VARCHAR(20) NOT NULL CHECK (question_type IN ('RADIO', 'CHECKLIST'))
);

-- ================================================
-- QuestionOption Table
-- Stores options for each question
-- ================================================
CREATE TABLE "QuestionOption" (
    question_option_id SERIAL PRIMARY KEY,
    question_id INTEGER NOT NULL REFERENCES "Question"(question_id) ON DELETE CASCADE,
    option_text TEXT NOT NULL,
    is_correct BOOLEAN NOT NULL DEFAULT FALSE
);

-- ================================================
-- User Quiz Take Table
-- Tracks user attempts at taking quizzes
-- ================================================
CREATE TABLE "User_Quiz_Take" (
    uqt_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES "User"(user_id) ON DELETE CASCADE,
    quiz_id INTEGER NOT NULL REFERENCES "Quiz"(quiz_id) ON DELETE CASCADE,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_time TIMESTAMP,
    total_correct INTEGER,
    result VARCHAR(50),
    quiz_assignment_id INTEGER REFERENCES "Quiz_Assignment"(quiz_assignment_id) ON DELETE SET NULL
);

-- ================================================
-- Quiz Take Question Answers Table
-- Stores user answers for each question in a quiz attempt
-- ================================================
CREATE TABLE "Quiz_Take_Question_Answers" (
    qtqa_id SERIAL PRIMARY KEY,
    uqt_id INTEGER NOT NULL REFERENCES "User_Quiz_Take"(uqt_id) ON DELETE CASCADE,
    question_id INTEGER NOT NULL REFERENCES "Question"(question_id) ON DELETE CASCADE,
    question_option_id INTEGER NOT NULL REFERENCES "QuestionOption"(question_option_id) ON DELETE CASCADE,
    is_correct BOOLEAN NOT NULL DEFAULT FALSE
);

-- ================================================
-- Create Indexes for Performance
-- ================================================
CREATE INDEX idx_quiz_user_id ON "Quiz"(user_id);
CREATE INDEX idx_question_quiz_id ON "Question"(quiz_id);
CREATE INDEX idx_question_option_question_id ON "QuestionOption"(question_id);
CREATE INDEX idx_user_quiz_take_user_id ON "User_Quiz_Take"(user_id);
CREATE INDEX idx_user_quiz_take_quiz_id ON "User_Quiz_Take"(quiz_id);
CREATE INDEX idx_quiz_assignment_user_id ON "Quiz_Assignment"(user_id);
CREATE INDEX idx_quiz_assignment_quiz_id ON "Quiz_Assignment"(quiz_id);
CREATE INDEX idx_qtqa_uqt_id ON "Quiz_Take_Question_Answers"(uqt_id);

-- ================================================
-- Insert Sample Data (Optional - for testing)
-- ================================================

-- Sample Users
INSERT INTO "User" (first_name, last_name, username, password, email_id, role) VALUES
('John', 'Teacher', 'johnteacher', '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 'john.teacher@example.com', 'TEACHER'),
('Jane', 'Student', 'janestudent', '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 'jane.student@example.com', 'STUDENT');

-- Note: Password above is SHA256 hash of "password"
-- In production, use proper password hashing

-- ================================================
-- Helpful Queries for Development
-- ================================================

-- View all quizzes with creator info
-- SELECT q.*, u.username as creator FROM "Quiz" q JOIN "User" u ON q.user_id = u.user_id;

-- View all questions for a quiz with options
-- SELECT q.question_id, q.question_text, q.question_type, qo.option_text, qo.is_correct 
-- FROM "Question" q 
-- JOIN "QuestionOption" qo ON q.question_id = qo.question_id 
-- WHERE q.quiz_id = 1;

-- View user test history with scores
-- SELECT uqt.*, q.quiz_name, q.total_no_questions 
-- FROM "User_Quiz_Take" uqt 
-- JOIN "Quiz" q ON uqt.quiz_id = q.quiz_id 
-- WHERE uqt.user_id = 1 
-- ORDER BY uqt.start_time DESC;

-- ================================================
-- Schema Creation Complete
-- ================================================
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public';

SELECT user_id, username, role FROM "User";

SELECT indexname FROM pg_indexes WHERE schemaname = 'public';