import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getAssignmentInfo, claimAssignment } from '../services/api';
import '../styles/Dashboard.css';

const ClaimAssignment = () => {
  const { token } = useParams();
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [assignmentInfo, setAssignmentInfo] = useState(null);
  const [claiming, setClaiming] = useState(false);
  const [claimedAssignment, setClaimedAssignment] = useState(null);

  useEffect(() => {
    loadAssignmentInfo();
  }, [token]);

  const loadAssignmentInfo = async () => {
    try {
      setLoading(true);
      const info = await getAssignmentInfo(token);
      setAssignmentInfo(info);
      if (!info.valid) {
        setError(info.message || 'Invalid or expired assignment link');
      }
    } catch (err) {
      setError('Failed to load assignment information.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated && user && assignmentInfo && assignmentInfo.valid && !claimedAssignment) {
      if (user.role === 'STUDENT') {
        handleClaim();
      }
    }
  }, [isAuthenticated, user, assignmentInfo]);

  const handleClaim = async () => {
    if (!user || !token || !assignmentInfo?.valid) return;

    setClaiming(true);
    setError('');

    try {
      const userId = user.user_id || user.id || user.userId;
      const result = await claimAssignment(token, userId);
      if (result.success) {
        setClaimedAssignment(result.assignment);
      } else {
        setError(result.message || 'Failed to claim assignment.');
      }
    } catch (err) {
      setError(err.response?.data?.message || err.response?.data?.detail || 'Failed to claim assignment.');
    } finally {
      setClaiming(false);
    }
  };

  const handleStartQuiz = () => {
    if (claimedAssignment && assignmentInfo) {
      navigate(`/take-test/${assignmentInfo.quiz_id}?assignment=${claimedAssignment.quiz_assignment_id}`);
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading assignment...</p>
      </div>
    );
  }

  if (!assignmentInfo || !assignmentInfo.valid) {
    return (
      <div className="create-quiz-container">
        <div className="create-quiz-card">
          <h2>Assignment Link Invalid</h2>
          <p style={{ color: 'red' }}>{error || 'This assignment link is invalid or has expired.'}</p>
          <button onClick={() => navigate('/')} style={{ marginTop: '20px', padding: '10px 20px' }}>
            Go to Dashboard
          </button>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="create-quiz-container">
        <div className="create-quiz-card">
          <h2>Assignment: {assignmentInfo.quiz_name}</h2>
          <p>📝 {assignmentInfo.total_questions} questions</p>
          <p>📊 Difficulty: {assignmentInfo.difficulty_level}</p>
          <p style={{ marginTop: '20px', fontWeight: 'bold' }}>Please log in or sign up to access this assignment.</p>
          <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
            <button 
              onClick={() => navigate('/login', { state: { from: `/assign/${token}` } })} 
              style={{ padding: '10px 20px', backgroundColor: '#6C63FF', color: 'white', border: 'none', borderRadius: '5px', cursor: 'pointer' }}
            >
              Log In
            </button>
            <button 
              onClick={() => navigate('/register', { state: { from: `/assign/${token}` } })} 
              style={{ padding: '10px 20px', backgroundColor: '#4caf50', color: 'white', border: 'none', borderRadius: '5px', cursor: 'pointer' }}
            >
              Sign Up
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (user.role === 'TEACHER') {
    return (
      <div className="create-quiz-container">
        <div className="create-quiz-card">
          <h2>Assignment: {assignmentInfo.quiz_name}</h2>
          <p>📝 {assignmentInfo.total_questions} questions</p>
          <p>📊 Difficulty: {assignmentInfo.difficulty_level}</p>
          <p style={{ marginTop: '20px', padding: '15px', backgroundColor: '#fff3cd', borderRadius: '8px', border: '1px solid #ffc107' }}>
            This assignment is for students. Teachers can view results in the dashboard.
          </p>
          <button 
            onClick={() => navigate('/')} 
            style={{ marginTop: '20px', padding: '10px 20px', backgroundColor: '#6C63FF', color: 'white', border: 'none', borderRadius: '5px', cursor: 'pointer' }}
          >
            Go to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="create-quiz-container">
      <div className="create-quiz-card">
        {claiming ? (
          <div>
            <div className="spinner"></div>
            <p>Claiming assignment...</p>
          </div>
        ) : error ? (
          <div>
            <h2>Assignment: {assignmentInfo.quiz_name}</h2>
            <p style={{ color: 'red', marginTop: '20px' }}>{error}</p>
            <button onClick={() => navigate('/')} style={{ marginTop: '20px', padding: '10px 20px' }}>
              Go to Dashboard
            </button>
          </div>
        ) : claimedAssignment ? (
          <div>
            <h2>Assignment: {assignmentInfo.quiz_name}</h2>
            <p>📝 {assignmentInfo.total_questions} questions</p>
            <p>📊 Difficulty: {assignmentInfo.difficulty_level}</p>
            <p style={{ marginTop: '20px', color: '#4caf50', fontWeight: 'bold' }}>
              Assignment claimed successfully!
            </p>
            <button 
              onClick={handleStartQuiz}
              style={{ marginTop: '20px', padding: '12px 24px', backgroundColor: '#6C63FF', color: 'white', border: 'none', borderRadius: '5px', cursor: 'pointer', fontSize: '16px', fontWeight: '600' }}
            >
              Start Quiz
            </button>
          </div>
        ) : (
          <div>
            <h2>Assignment: {assignmentInfo.quiz_name}</h2>
            <p>📝 {assignmentInfo.total_questions} questions</p>
            <p>📊 Difficulty: {assignmentInfo.difficulty_level}</p>
            <p style={{ marginTop: '20px' }}>Preparing assignment...</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ClaimAssignment;

