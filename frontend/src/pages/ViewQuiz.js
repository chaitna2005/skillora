import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getQuiz } from '../services/api';
import '../styles/ViewQuiz.css';

const ViewQuiz = () => {
  const { quizId } = useParams();
  const navigate = useNavigate();
  const [quiz, setQuiz] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Format difficulty label for display (short form)
  const formatDifficultyLabel = (difficulty) => {
    if (!difficulty) return 'Med';
    const normalized = difficulty.charAt(0).toUpperCase() + difficulty.slice(1).toLowerCase();
    return normalized === 'Medium' ? 'Med' : normalized;
  };

  useEffect(() => {
    loadQuiz();
  }, [quizId]);

  const loadQuiz = async () => {
    try {
      setLoading(true);
      setError('');
      const quizData = await getQuiz(quizId);
      setQuiz(quizData);
    } catch (err) {
      setError('Failed to load quiz. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading quiz...</p>
      </div>
    );
  }

  if (error || !quiz) {
    return (
      <div className="error-container">
        <p>{error || 'Quiz not found'}</p>
        <button onClick={() => navigate('/')}>Go Back</button>
      </div>
    );
  }

  return (
    <div className="view-quiz-container">
      <div className="view-quiz-header">
        <div className="view-quiz-title-section">
          <h1>{quiz.quiz_name}</h1>
          <div className="quiz-meta">
            <span className={`difficulty-badge ${quiz.difficulty_level.toLowerCase()}`}>
              {formatDifficultyLabel(quiz.difficulty_level)}
            </span>
            <span>📝 {quiz.total_no_questions} questions</span>
          </div>
        </div>
        <div className="view-quiz-actions">
          <button onClick={() => navigate('/')} className="back-btn">
            ← Back to Dashboard
          </button>
          <button 
            onClick={() => navigate(`/take-test/${quizId}`)} 
            className="take-test-btn"
          >
            Take Test →
          </button>
        </div>
      </div>

      <div className="view-quiz-content">
        <div className="preview-notice">
          <p>📖 Preview Mode - Questions are shown for review only. Click "Take Test" to start the quiz.</p>
        </div>

        <div className="questions-list">
          {quiz.questions && quiz.questions.map((question, index) => (
            <div key={question.question_id} className="question-preview-card">
              <div className="question-preview-header">
                <h3>Question {index + 1}</h3>
                <span className="question-type-badge">
                  {question.question_type === 'CHECKLIST' ? '☑️ Multiple Choice' : '⭕ Single Choice'}
                </span>
              </div>
              
              <p className="question-preview-text">{question.question_text}</p>
              
              <div className="options-preview">
                {question.options && question.options.map((option, optIndex) => (
                  <div key={option.question_option_id} className="option-preview-item">
                    <span className="option-number">{optIndex + 1}.</span>
                    <span className="option-text">{option.option_text}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="view-quiz-footer">
        <button onClick={() => navigate('/')} className="back-btn">
          ← Back to Dashboard
        </button>
        <button 
          onClick={() => navigate(`/take-test/${quizId}`)} 
          className="take-test-btn"
        >
          Take Test →
        </button>
      </div>
    </div>
  );
};

export default ViewQuiz;

