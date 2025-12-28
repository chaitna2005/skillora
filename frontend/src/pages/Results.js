import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getTestResult } from '../services/api';
import '../styles/Results.css';

const Results = () => {
  const { uqtId } = useParams();
  const navigate = useNavigate();
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadResults();
  }, [uqtId]);

  const loadResults = async () => {
    try {
      setLoading(true);
      const data = await getTestResult(uqtId);
      setResult(data);
    } catch (err) {
      setError('Failed to load results. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getPerformanceLevel = (percentage) => {
    if (percentage >= 90) return { level: 'Excellent', emoji: '🌟', class: 'excellent' };
    if (percentage >= 70) return { level: 'Good', emoji: '👍', class: 'good' };
    if (percentage >= 50) return { level: 'Fair', emoji: '😊', class: 'fair' };
    return { level: 'Needs Improvement', emoji: '📚', class: 'poor' };
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading results...</p>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="error-container">
        <p>{error || 'Results not found'}</p>
        <button onClick={() => navigate('/')}>Go Back</button>
      </div>
    );
  }

  const performance = getPerformanceLevel(result.result);

  return (
    <div className="results-container">
      <div className="results-header">
        <h1>Test Results</h1>
        <h2>{result.quiz_name}</h2>
      </div>

      <div className="score-card">
        <div className={`score-circle ${performance.class}`}>
          <div className="score-value">{result.result}%</div>
          <div className="score-label">Score</div>
        </div>
        
        <div className="score-details">
          <div className="detail-item">
            <span className="detail-icon">✅</span>
            <div>
              <p className="detail-value">{result.total_correct}</p>
              <p className="detail-label">Correct</p>
            </div>
          </div>
          
          <div className="detail-item">
            <span className="detail-icon">❌</span>
            <div>
              <p className="detail-value">{result.total_questions - result.total_correct}</p>
              <p className="detail-label">Incorrect</p>
            </div>
          </div>
          
          <div className="detail-item">
            <span className="detail-icon">📝</span>
            <div>
              <p className="detail-value">{result.total_questions}</p>
              <p className="detail-label">Total</p>
            </div>
          </div>
        </div>

        <div className={`performance-badge ${performance.class}`}>
          {performance.emoji} {performance.level}
        </div>
      </div>

      <div className="questions-review">
        <h3>Detailed Review</h3>
        
        {result.questions.map((question, index) => (
          <div key={question.question_id} className="review-question">
            <div className="review-question-header">
              <h4>Question {index + 1}</h4>
              <span className={`answer-status ${question.is_correct ? 'correct' : 'incorrect'}`}>
                {question.is_correct ? '✓ Correct' : '✗ Incorrect'}
              </span>
            </div>
            
            <p className="review-question-text">{question.question_text}</p>
            
            <div className="review-options">
              {question.options.map(option => {
                const isUserAnswer = question.user_answers.includes(option.question_option_id);
                const isCorrectOption = option.is_correct;
                
                let optionClass = 'review-option';
                if (isCorrectOption) {
                  optionClass += ' correct-answer';
                }
                if (isUserAnswer && !isCorrectOption) {
                  optionClass += ' wrong-answer';
                }
                if (isUserAnswer) {
                  optionClass += ' user-selected';
                }
                
                return (
                  <div key={option.question_option_id} className={optionClass}>
                    <span className="option-indicator">
                      {isCorrectOption && '✓ '}
                      {isUserAnswer && !isCorrectOption && '✗ '}
                    </span>
                    <span className="option-text">{option.option_text}</span>
                    {isUserAnswer && <span className="badge">Your Answer</span>}
                    {isCorrectOption && <span className="badge correct">Correct Answer</span>}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      <div className="results-actions">
        <button onClick={() => navigate('/')} className="back-btn">
          ← Back to Dashboard
        </button>
        <button onClick={() => navigate(`/take-test/${result.quiz_id}`)} className="retake-btn">
          🔄 Retake Test
        </button>
      </div>
    </div>
  );
};

export default Results;

