import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import { getQuiz, getUserTests, startTest } from '../api/api';

function QuizDetail({ user, onLogout }) {
  const { quizId } = useParams();
  const navigate = useNavigate();
  const [quiz, setQuiz] = useState(null);
  const [attempts, setAttempts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [startingTest, setStartingTest] = useState(false);

  useEffect(() => {
    loadQuizData();
  }, [quizId]);

  const loadQuizData = async () => {
    setLoading(true);
    try {
      const [quizData, allTests] = await Promise.all([
        getQuiz(quizId),
        getUserTests(user.user_id),
      ]);

      setQuiz(quizData);
      
      // Filter attempts for this quiz
      const quizAttempts = allTests.filter(test => test.quiz_id === parseInt(quizId));
      setAttempts(quizAttempts);
    } catch (error) {
      console.error('Error loading quiz:', error);
      alert('Failed to load quiz details');
    } finally {
      setLoading(false);
    }
  };

  const handleStartTest = async () => {
    setStartingTest(true);
    try {
      const testData = { quiz_id: parseInt(quizId) };
      await startTest(user.user_id, testData);
      navigate(`/take-test/${quizId}`);
    } catch (error) {
      console.error('Error starting test:', error);
      alert('Failed to start test');
    } finally {
      setStartingTest(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getDifficultyColor = (level) => {
    switch (level) {
      case 'EASY':
        return '#4caf50';
      case 'MEDIUM':
        return '#ff9800';
      case 'HARD':
        return '#f44336';
      default:
        return '#666';
    }
  };

  if (loading) {
    return (
      <div className="app-layout">
        <Sidebar user={user} onLogout={onLogout} />
        <div className="main-content">
          <div className="loading">Loading quiz...</div>
        </div>
      </div>
    );
  }

  if (!quiz) {
    return (
      <div className="app-layout">
        <Sidebar user={user} onLogout={onLogout} />
        <div className="main-content">
          <div className="error-message">Quiz not found</div>
        </div>
      </div>
    );
  }

  return (
    <div className="app-layout">
      <Sidebar user={user} onLogout={onLogout} />
      
      <div className="main-content">
        <div className="quiz-detail-container">
          <button className="back-btn" onClick={() => navigate('/home')}>
            ← Back to Home
          </button>

          <div className="quiz-header">
            <h1>{quiz.quiz_name}</h1>
            <span
              className="difficulty-badge"
              style={{ backgroundColor: getDifficultyColor(quiz.difficulty_level) }}
            >
              {quiz.difficulty_level}
            </span>
          </div>

          <div className="quiz-info">
            <p><strong>Prompt:</strong> {quiz.prompt}</p>
            <p><strong>Total Questions:</strong> {quiz.total_no_questions}</p>
            <p><strong>Created:</strong> {formatDate(quiz.created_date)}</p>
          </div>

          <div className="quiz-actions">
            <button
              className="btn-primary btn-large"
              onClick={handleStartTest}
              disabled={startingTest}
            >
              {startingTest ? 'Starting...' : '🎯 Take Test'}
            </button>
          </div>

          {attempts.length > 0 && (
            <div className="attempts-section">
              <h2>Your Attempts</h2>
              <div className="attempts-list">
                {attempts.map((attempt, index) => (
                  <div key={attempt.uqt_id} className="attempt-card">
                    <div className="attempt-header">
                      <h4>Attempt {attempts.length - index}</h4>
                      {attempt.completed_time ? (
                        <span className="status-badge completed">Completed</span>
                      ) : (
                        <span className="status-badge pending">In Progress</span>
                      )}
                    </div>
                    <p>Started: {formatDate(attempt.start_time)}</p>
                    {attempt.completed_time && (
                      <>
                        <p>Completed: {formatDate(attempt.completed_time)}</p>
                        <p className="score">
                          Score: {attempt.total_correct}/{quiz.total_no_questions} (
                          {Math.round((attempt.total_correct / quiz.total_no_questions) * 100)}%)
                        </p>
                        <button
                          className="btn-secondary"
                          onClick={() => navigate(`/test-result/${attempt.uqt_id}`)}
                        >
                          View Results
                        </button>
                      </>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default QuizDetail;

