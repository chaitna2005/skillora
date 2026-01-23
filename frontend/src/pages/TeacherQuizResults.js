import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { exportQuizResultsCSV } from '../services/api';
import '../styles/TeacherQuizResults.css';

const TeacherQuizResults = () => {
  const { quizId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [results, setResults] = useState([]);
  const [quizInfo, setQuizInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadResults();
  }, [quizId, user]);

  const loadResults = async () => {
    try {
      setLoading(true);
      setError('');
      
      // Verify teacher role
      if (user?.role !== 'TEACHER') {
        setError('Only teachers can view quiz results');
        setLoading(false);
        return;
      }

      const userId = user?.user_id || user?.id;
      if (!userId) {
        throw new Error('User ID is missing');
      }

      // Fetch all assignment results for this teacher
      const response = await fetch(`http://localhost:8000/quiz/assign/results/${userId}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch results');
      }

      const allResults = await response.json();
      
      console.log('[TeacherResults] All results from API:', allResults);
      
      // Filter results for this specific quiz
      const quizResults = allResults.filter(r => r.quiz_id === parseInt(quizId));
      
      console.log(`[TeacherResults] Filtered results for quiz ${quizId}:`, quizResults);
      console.log('[TeacherResults] First result sample:', quizResults[0]);
      
      if (quizResults.length > 0) {
        setQuizInfo({
          quiz_name: quizResults[0].quiz_name,
          total_questions: quizResults[0].total_questions
        });
      }
      
      setResults(quizResults);
      
    } catch (err) {
      console.error('Error loading results:', err);
      setError(err.message || 'Failed to load quiz results');
    } finally {
      setLoading(false);
    }
  };

  const handleExportCSV = async () => {
    try {
      const userId = user?.user_id || user?.id;
      const blob = await exportQuizResultsCSV(userId, parseInt(quizId));
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `quiz_${quizId}_results.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Export failed:', error);
      alert('Failed to export results: ' + (error.response?.data?.detail || error.message));
    }
  };

  const getScorePercentage = (correct, total) => {
    if (!total || total === 0) return 0;
    return Math.round((correct / total) * 100);
  };

  const getPerformanceClass = (percentage) => {
    if (percentage >= 80) return 'excellent';
    if (percentage >= 60) return 'good';
    if (percentage >= 40) return 'average';
    return 'needs-improvement';
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Not attempted';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="teacher-results-container">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading results...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="teacher-results-container">
        <div className="error-state">
          <p className="error-message">⚠️ {error}</p>
          <button onClick={() => navigate('/')} className="back-btn">
            ← Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="teacher-results-container">
      <div className="results-header">
        <div className="header-top">
          <button onClick={() => navigate('/')} className="back-btn">
            ← Back to Dashboard
          </button>
          <button onClick={handleExportCSV} className="export-btn">
            📥 Export CSV
          </button>
        </div>
        
        <h1>Quiz Results</h1>
        {quizInfo && (
          <div className="quiz-info">
            <h2>{quizInfo.quiz_name}</h2>
            <p className="quiz-meta">
              {quizInfo.total_questions} questions • {results.filter(r => r.attempt_status === 'COMPLETED').length} submissions
            </p>
          </div>
        )}
      </div>

      {results.length === 0 ? (
        <div className="empty-state">
          <p>📋 No students have attempted this quiz yet.</p>
        </div>
      ) : (
        <div className="results-table-wrapper">
          <table className="results-table">
            <thead>
              <tr>
                <th>Student Name</th>
                <th>Status</th>
                <th>Score</th>
                <th>Percentage</th>
                <th>Performance</th>
                <th>Completed</th>
              </tr>
            </thead>
            <tbody>
              {results.map((result, index) => {
                console.log(`[TeacherResults] Rendering row ${index}:`, {
                  student: result.student_name,
                  status: result.attempt_status,
                  total_correct: result.total_correct,
                  total_questions: result.total_questions,
                  completed_time: result.completed_time
                });
                
                const percentage = getScorePercentage(result.total_correct, result.total_questions);
                const performanceClass = getPerformanceClass(percentage);
                const isCompleted = result.attempt_status === 'COMPLETED';
                const isNotAttempted = result.attempt_status === 'NOT_ATTEMPTED';

                return (
                  <tr key={result.uqt_id || `result-${index}`} className={isNotAttempted ? 'not-attempted' : ''}>
                    <td className="student-name">
                      <strong>{result.student_name}</strong>
                    </td>
                    <td>
                      <span className={`status-badge ${isCompleted ? 'completed' : 'pending'}`}>
                        {isCompleted ? 'Completed' : isNotAttempted ? 'Not Attempted' : 'In Progress'}
                      </span>
                    </td>
                    <td className="score-cell">
                      {isCompleted ? `${result.total_correct || 0} / ${result.total_questions}` : '-'}
                    </td>
                    <td className="percentage-cell">
                      {isCompleted ? `${percentage}%` : '-'}
                    </td>
                    <td>
                      {isCompleted ? (
                        <span className={`performance-badge ${performanceClass}`}>
                          {percentage >= 80 ? 'Excellent' : 
                           percentage >= 60 ? 'Good' : 
                           percentage >= 40 ? 'Average' : 
                           'Needs Improvement'}
                        </span>
                      ) : (
                        '-'
                      )}
                    </td>
                    <td className="date-cell">
                      {formatDate(result.completed_time)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default TeacherQuizResults;
