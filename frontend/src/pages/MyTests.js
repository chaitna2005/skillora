import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getUserTests, getTestSummary } from '../services/api';
import '../styles/MyTests.css';

const MyTests = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [tests, setTests] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [user]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [testsData, summaryData] = await Promise.all([
        getUserTests(user.user_id),
        getTestSummary(user.user_id)
      ]);
      setTests(testsData);
      setSummary(summaryData);
    } catch (error) {
      console.error('Error loading tests:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const handleViewResult = (test) => {
    // CRITICAL: Navigate using quiz_id (backend will fetch latest completed attempt)
    // test can be either uqtId (number) or test object with quiz_id
    const quizId = typeof test === 'object' ? test.quiz_id : tests.find(t => t.uqt_id === test)?.quiz_id;
    if (quizId) {
      navigate(`/results/${quizId}`);
    } else {
      console.error('[ERROR] quiz_id not found for test:', test);
      alert('Quiz ID not found. Cannot view results.');
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading your tests...</p>
      </div>
    );
  }

  return (
    <div className="my-tests-container">
      <div className="page-header">
        <h1>My Test History</h1>
        <p>View all your completed tests and scores</p>
      </div>

      {summary && (
        <div className="summary-cards">
          <div className="summary-card">
            <div className="summary-icon">📊</div>
            <div className="summary-content">
              <h3>{summary.total_tests_taken}</h3>
              <p>Tests Taken</p>
            </div>
          </div>
          
          <div className="summary-card">
            <div className="summary-icon">⭐</div>
            <div className="summary-content">
              <h3>{summary.average_score !== null ? summary.average_score.toFixed(1) : 'N/A'}%</h3>
              <p>Average Score</p>
            </div>
          </div>
          
          <div className="summary-card">
            <div className="summary-icon">🏆</div>
            <div className="summary-content">
              <h3>{summary.highest_score}%</h3>
              <p>Highest Score</p>
            </div>
          </div>
          
          <div className="summary-card">
            <div className="summary-icon">📈</div>
            <div className="summary-content">
              <h3>{summary.total_questions_answered}</h3>
              <p>Questions Answered</p>
            </div>
          </div>
        </div>
      )}

      <div className="tests-list">
        {tests.length === 0 ? (
          <div className="empty-state">
            <p>📝 No tests taken yet. Start by taking a quiz!</p>
            <button onClick={() => navigate('/')} className="go-home-btn">
              Go to Dashboard
            </button>
          </div>
        ) : (
          tests.map(test => (
            <div key={test.uqt_id} className="test-item">
              <div className="test-item-header">
                <div>
                  <h3>{test.quiz_name}</h3>
                  <p className="test-date">{formatDate(test.completed_time)}</p>
                </div>
                <div className={`test-score ${test.result >= 70 ? 'pass' : 'fail'}`}>
                  {test.result}%
                </div>
              </div>
              
              <div className="test-item-body">
                <div className="test-stats">
                  <span>✅ {test.total_correct} correct</span>
                  <span>❌ {test.total_questions - test.total_correct} incorrect</span>
                  <span>📝 {test.total_questions} total</span>
                </div>
                
                <button 
                  onClick={() => handleViewResult(test)}
                  className="view-details-btn"
                >
                  View Details →
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default MyTests;

