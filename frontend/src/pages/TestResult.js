import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import { getTestResult } from '../api/api';

function TestResult({ user, onLogout }) {
  const { uqtId } = useParams();
  const navigate = useNavigate();
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadResult();
  }, [uqtId]);

  const loadResult = async () => {
    setLoading(true);
    try {
      const resultData = await getTestResult(uqtId);
      setResult(resultData);
    } catch (error) {
      console.error('Error loading result:', error);
      alert('Failed to load test results');
    } finally {
      setLoading(false);
    }
  };

  const getResultColor = (resultType) => {
    switch (resultType) {
      case 'EXCELLENT':
        return '#4caf50';
      case 'GOOD':
        return '#2196f3';
      case 'NEEDS_IMPROVEMENT':
        return '#ff9800';
      default:
        return '#666';
    }
  };

  if (loading) {
    return (
      <div className="app-layout">
        <Sidebar user={user} onLogout={onLogout} />
        <div className="main-content">
          <div className="loading">Loading results...</div>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="app-layout">
        <Sidebar user={user} onLogout={onLogout} />
        <div className="main-content">
          <div className="error-message">Results not found</div>
        </div>
      </div>
    );
  }

  return (
    <div className="app-layout">
      <Sidebar user={user} onLogout={onLogout} />
      
      <div className="main-content">
        <div className="result-container">
          <button className="back-btn" onClick={() => navigate('/home')}>
            ← Back to Home
          </button>

          <div className="result-header">
            <h1>Test Results</h1>
            <h2>{result.quiz_name}</h2>
          </div>

          <div className="result-summary">
            <div className="score-circle" style={{ borderColor: getResultColor(result.result) }}>
              <div className="score-value">{Math.round(result.score_percentage)}%</div>
              <div className="score-label">Score</div>
            </div>

            <div className="result-stats">
              <div className="stat">
                <span className="stat-label">Correct Answers</span>
                <span className="stat-value">{result.total_correct} / {result.total_questions}</span>
              </div>
              <div className="stat">
                <span className="stat-label">Result</span>
                <span
                  className="stat-value result-badge"
                  style={{ color: getResultColor(result.result) }}
                >
                  {result.result.replace('_', ' ')}
                </span>
              </div>
            </div>
          </div>

          <div className="feedback-box">
            <h3>Feedback</h3>
            <p>{result.feedback}</p>
          </div>

          <div className="answers-review">
            <h3>Detailed Review</h3>
            {result.details.map((detail, index) => (
              <div
                key={detail.question_id}
                className={`answer-card ${detail.is_correct ? 'correct' : 'incorrect'}`}
              >
                <div className="answer-header">
                  <h4>Question {index + 1}</h4>
                  <span className={`status-icon ${detail.is_correct ? 'correct' : 'incorrect'}`}>
                    {detail.is_correct ? '✓' : '✗'}
                  </span>
                </div>
                
                <p className="question-text">{detail.question_text}</p>
                
                <div className="answer-details">
                  <div className="user-answer">
                    <strong>Your Answer:</strong>
                    {detail.user_answers.length > 0 ? (
                      <ul>
                        {detail.user_answers.map((ans, i) => (
                          <li key={i}>{ans}</li>
                        ))}
                      </ul>
                    ) : (
                      <p className="no-answer">No answer provided</p>
                    )}
                  </div>
                  
                  {!detail.is_correct && (
                    <div className="correct-answer">
                      <strong>Correct Answer:</strong>
                      <ul>
                        {detail.correct_answers.map((ans, i) => (
                          <li key={i}>{ans}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="result-actions">
            <button className="btn-secondary" onClick={() => navigate('/home')}>
              Go to Home
            </button>
            <button
              className="btn-primary"
              onClick={() => navigate(`/quiz/${result.quiz_id || ''}`)}
            >
              Take Quiz Again
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default TestResult;

