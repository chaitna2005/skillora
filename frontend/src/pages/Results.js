import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getTestResult } from '../services/api';
import '../styles/Results.css';

const Results = () => {
  const { quizId } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expandedFeedback, setExpandedFeedback] = useState({}); // Track which feedback sections are expanded

  useEffect(() => {
    loadResults();
  }, [quizId, user]);

  const loadResults = async () => {
    try {
      setLoading(true);
      setError(''); // Clear any previous errors
      
      // CRITICAL: Get user_id and quiz_id for fetching latest completed attempt
      const userId = user?.user_id || user?.id || user?.userId;
      const currentQuizId = quizId || searchParams.get('quiz_id');
      
      if (!userId || !currentQuizId) {
        throw new Error('User ID or Quiz ID is missing');
      }
      
      console.log(`[DEBUG] Loading results for user_id: ${userId}, quiz_id: ${currentQuizId}`);
      
      const data = await getTestResult(userId, currentQuizId);
      
      // Validate response structure
      if (!data) {
        throw new Error('Empty response from server');
      }
      
      // Ensure required fields exist with defaults
      const validatedData = {
        ...data,
        total_questions: data.total_questions || 0,
        total_correct: data.total_correct || 0,
        score_percentage: data.score_percentage || 0,
        details: data.details || [],
        quiz_name: data.quiz_name || 'Unknown Quiz'
      };
      
      console.log(`[DEBUG] Results loaded successfully:`, {
        quiz_name: validatedData.quiz_name,
        total_questions: validatedData.total_questions,
        details_count: validatedData.details.length
      });
      
      setResult(validatedData);
    } catch (err) {
      console.error('[ERROR] Failed to load results:', err);
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load results. Please try again.';
      setError(errorMessage);
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

  const performance = getPerformanceLevel(result.score_percentage);

  return (
    <div className="results-container">
      <div className="results-header">
        <h1>Test Results</h1>
        <h2>{result.quiz_name}</h2>
      </div>

      <div className="score-card">
        <div className={`score-circle ${performance.class}`}>
          <div className="score-value">{result.score_percentage.toFixed(1)}%</div>
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
        
        {result.details && result.details.map((detail, index) => (
          <div key={detail.question_id} className="review-question">
            <div className="review-question-header">
              <h4>Question {index + 1}</h4>
              <span className={`answer-status ${detail.is_correct ? 'correct' : 'incorrect'}`}>
                {detail.is_correct ? '✓ Correct' : '✗ Incorrect'}
              </span>
            </div>
            
            <p className="review-question-text">{detail.question_text}</p>
            
            <div className="review-options">
              <div className="review-answer-section">
                <div className="answer-group">
                  <h5>Your Answer:</h5>
                  {detail.user_answers && detail.user_answers.length > 0 ? (
                    detail.user_answers.map((answer, idx) => (
                      <div key={idx} className={`review-option ${detail.is_correct ? 'correct-answer' : 'wrong-answer'} user-selected`}>
                        <span className="option-indicator">{detail.is_correct ? '✓ ' : '✗ '}</span>
                        <span className="option-text">{answer}</span>
                        <span className="badge">Your Answer</span>
                      </div>
                    ))
                  ) : (
                    <div className="review-option wrong-answer">
                      <span className="option-indicator">✗ </span>
                      <span className="option-text">No answer provided</span>
                    </div>
                  )}
                </div>
                
                <div className="answer-group">
                  <h5>Correct Answer:</h5>
                  {detail.correct_answers && detail.correct_answers.length > 0 ? (
                    detail.correct_answers.map((answer, idx) => (
                      <div key={idx} className="review-option correct-answer">
                        <span className="option-indicator">✓ </span>
                        <span className="option-text">{answer}</span>
                        <span className="badge correct">Correct Answer</span>
                      </div>
                    ))
                  ) : (
                    <div className="review-option">
                      <span className="option-text">No correct answer</span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Feedback Section */}
            {detail.feedback && (
              <div style={{
                marginTop: '20px',
                padding: '15px',
                backgroundColor: '#F6F8FF',
                border: '1px solid #E0E5FF',
                borderRadius: '8px',
                borderLeft: `4px solid ${detail.is_correct ? '#4CAF50' : '#A78BFA'}`
              }}>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    cursor: 'pointer',
                    marginBottom: expandedFeedback[detail.question_id] ? '12px' : '0'
                  }}
                  onClick={() => setExpandedFeedback(prev => ({
                    ...prev,
                    [detail.question_id]: !prev[detail.question_id]
                  }))}
                >
                  <h5 style={{
                    margin: 0,
                    fontSize: '14px',
                    fontWeight: '600',
                    color: '#1F2937',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}>
                    <span>💡</span>
                    <span>Explanation</span>
                  </h5>
                  <span style={{
                    fontSize: '18px',
                    color: '#6B7280',
                    transition: 'transform 0.2s',
                    transform: expandedFeedback[detail.question_id] ? 'rotate(180deg)' : 'rotate(0deg)'
                  }}>
                    ▼
                  </span>
                </div>
                {expandedFeedback[detail.question_id] && (
                  <p style={{
                    margin: 0,
                    fontSize: '14px',
                    color: '#1F2937',
                    lineHeight: '1.6',
                    paddingTop: '8px',
                    borderTop: '1px solid #E0E5FF'
                  }}>
                    {detail.feedback}
                  </p>
                )}
              </div>
            )}
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

