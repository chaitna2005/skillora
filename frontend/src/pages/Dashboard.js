import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  getUserQuizzes, 
  getAssignedQuizzes, 
  getPendingTests, 
  getCompletedTests, 
  deletePendingTest, 
  deleteQuiz,
  deleteAllPendingTests,
  deleteAllCompletedTests,
  deleteAllUserQuizzes,
  deleteAllAssignedQuizzes,
  bulkDeletePendingTests,
  bulkDeleteCompletedTests,
  bulkDeleteQuizzes,
  bulkDeleteAssignedQuizzes,
  createShareLink,
  getAssignmentResults,
  getQuizAnalytics,
  getQuestionDifficulty,
  exportQuizResultsCSV,
  getUserStats
} from '../services/api';
import '../styles/Dashboard.css';

const Dashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [myQuizzes, setMyQuizzes] = useState([]);
  const [assignedQuizzes, setAssignedQuizzes] = useState([]);
  const [pendingTests, setPendingTests] = useState([]);
  const [completedTests, setCompletedTests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('myQuizzes');
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [confirmAction, setConfirmAction] = useState(null);
  const [successMessage, setSuccessMessage] = useState('');
  
  // Selection state for each section
  const [selectedQuizzes, setSelectedQuizzes] = useState(new Set());
  const [selectedAssigned, setSelectedAssigned] = useState(new Set());
  const [selectedPending, setSelectedPending] = useState(new Set());
  const [selectedCompleted, setSelectedCompleted] = useState(new Set());
  const [shareLink, setShareLink] = useState(null);
  const [assignmentResults, setAssignmentResults] = useState([]);
  const [showResults, setShowResults] = useState(false);
  const [quizAnalytics, setQuizAnalytics] = useState([]);
  const [questionDifficulty, setQuestionDifficulty] = useState([]);
  const [selectedQuizForDifficulty, setSelectedQuizForDifficulty] = useState(null);
  const [showDifficultyModal, setShowDifficultyModal] = useState(false);
  const [userStats, setUserStats] = useState(null);
  const [newBadgeNotification, setNewBadgeNotification] = useState(null);
  
  // Helper to get user ID (handles different field names)
  const getUserId = () => {
    if (!user) return null;
    return user.user_id || user.id || user.userId || null;
  };

  // Clear selections when tab changes
  useEffect(() => {
    setSelectedQuizzes(new Set());
    setSelectedAssigned(new Set());
    setSelectedPending(new Set());
    setSelectedCompleted(new Set());
  }, [activeTab]);

  useEffect(() => {
    if (user) {
      loadData();
    }
  }, [user, location.pathname]);

  // Refresh data when window regains focus (user returns from test page)
  useEffect(() => {
    const handleFocus = () => {
      if (user) {
        loadData();
      }
    };

    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, [user]);

  // Refresh data when component becomes visible (user navigates back)
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden && user) {
        loadData();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [user]);

  const loadData = async () => {
    const userId = getUserId();
    
    if (!user || !userId) {
      console.error('[DASHBOARD] User or user_id is missing:', {
        user: user,
        user_id: user?.user_id,
        id: user?.id,
        userId: user?.userId,
        resolvedUserId: userId
      });
      setLoading(false);
      return;
    }
    
    try {
      setLoading(true);
      
      const [quizzes, assigned, pending, completed, stats] = await Promise.all([
        getUserQuizzes(userId).catch(() => []),
        getAssignedQuizzes(userId).catch(() => []),
        getPendingTests(userId).catch(() => []),
        getCompletedTests(userId).catch(() => []),
        getUserStats(userId).catch(() => null)
      ]);
      
      // Ensure we have arrays (handle null/undefined responses)
      const quizzesArray = Array.isArray(quizzes) ? quizzes : [];
      const assignedArray = Array.isArray(assigned) ? assigned : [];
      const pendingArray = Array.isArray(pending) ? pending : [];
      const completedArray = Array.isArray(completed) ? completed : [];
      
      // NO FILTERING - Set pending tests directly as received from API
      // Includes both NOT_STARTED and IN_PROGRESS tests
      setMyQuizzes(quizzesArray);
      setAssignedQuizzes(assignedArray);
      setPendingTests(pendingArray);
      setCompletedTests(completedArray);
      
      // Update stats and check for new badges
      if (stats) {
        const previousBadges = userStats?.unlocked_badges || [];
        const newBadges = stats.unlocked_badges || [];
        const newlyUnlocked = newBadges.filter(badge => !previousBadges.includes(badge));
        
        // Show notification for newly unlocked badges (only if we had previous stats)
        if (newlyUnlocked.length > 0 && userStats !== null) {
          setNewBadgeNotification(newlyUnlocked);
          setTimeout(() => setNewBadgeNotification(null), 5000); // Auto-hide after 5 seconds
        }
        
        setUserStats(stats);
      }
    } catch (error) {
      setMyQuizzes([]);
      setAssignedQuizzes([]);
      setPendingTests([]);
      setCompletedTests([]);
    } finally {
      setLoading(false);
    }
  };

  const handleTakeTest = (quizId, assignmentId = null) => {
    navigate(`/take-test/${quizId}${assignmentId ? `?assignment=${assignmentId}` : ''}`);
  };

  const handleViewQuiz = (quizId) => {
    navigate(`/view-quiz/${quizId}`);
  };

  const handleViewResult = (test) => {
    // CRITICAL: Navigate using quiz_id (backend will fetch latest completed attempt)
    // test can be either uqtId (number) or test object with quiz_id
    const quizId = typeof test === 'object' ? test.quiz_id : completedTests.find(t => t.uqt_id === test)?.quiz_id;
    if (quizId) {
      navigate(`/results/${quizId}`);
    } else {
      console.error('[ERROR] quiz_id not found for test:', test);
      alert('Quiz ID not found. Cannot view results.');
    }
  };

  const handleDeleteQuiz = async (quizId, e) => {
    e.stopPropagation();
    const userId = getUserId();
    if (!userId) {
      alert('User ID not found. Please log in again.');
      return;
    }
    if (window.confirm('Are you sure you want to delete this quiz?')) {
      try {
        await deleteQuiz(userId, quizId);
        setMyQuizzes(myQuizzes.filter(q => q.quiz_id !== quizId));
      } catch (error) {
        alert('Failed to delete quiz. Please try again.');
        console.error(error);
      }
    }
  };

  const handleDeletePendingTest = async (uqtId, e) => {
    e.stopPropagation();
    const userId = getUserId();
    if (!userId) {
      alert('User ID not found. Please log in again.');
      return;
    }
    if (window.confirm('Are you sure you want to delete this pending test?')) {
      try {
        await deletePendingTest(userId, uqtId);
        setPendingTests(pendingTests.filter(t => t.uqt_id !== uqtId));
      } catch (error) {
        alert('Failed to delete pending test. Please try again.');
        console.error(error);
      }
    }
  };

  const handleDeleteAll = (section) => {
    setConfirmAction(section);
    setShowConfirmModal(true);
  };

  const confirmDeleteAll = async () => {
    const userId = getUserId();
    if (!userId) {
      alert('User ID not found. Please log in again.');
      return;
    }
    
    try {
      let result;
      let refreshFunction;
      
      switch (confirmAction) {
        case 'pending':
          result = await deleteAllPendingTests(userId);
          refreshFunction = () => loadData();
          break;
        case 'completed':
          result = await deleteAllCompletedTests(userId);
          refreshFunction = () => loadData();
          break;
        case 'myQuizzes':
          result = await deleteAllUserQuizzes(userId);
          refreshFunction = () => loadData();
          break;
        case 'assigned':
          result = await deleteAllAssignedQuizzes(userId);
          refreshFunction = () => loadData();
          break;
        default:
          return;
      }
      
      setSuccessMessage(result.message || `Successfully deleted ${result.deleted_count || 0} item(s)`);
      setShowConfirmModal(false);
      setConfirmAction(null);
      
      // Refresh data
      await refreshFunction();
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (error) {
      alert('Failed to delete items. Please try again.');
      console.error(error);
      setShowConfirmModal(false);
      setConfirmAction(null);
    }
  };

  const cancelDeleteAll = () => {
    setShowConfirmModal(false);
    setConfirmAction(null);
  };

  // Selection handlers
  const handleSelectItem = (section, id) => {
    const setters = {
      'myQuizzes': setSelectedQuizzes,
      'assigned': setSelectedAssigned,
      'pending': setSelectedPending,
      'completed': setSelectedCompleted
    };
    
    const selections = {
      'myQuizzes': selectedQuizzes,
      'assigned': selectedAssigned,
      'pending': selectedPending,
      'completed': selectedCompleted
    };
    
    const setter = setters[section];
    const current = selections[section];
    const newSelection = new Set(current);
    
    if (newSelection.has(id)) {
      newSelection.delete(id);
    } else {
      newSelection.add(id);
    }
    
    setter(newSelection);
  };

  const handleSelectAll = (section) => {
    const items = {
      'myQuizzes': myQuizzes.map(q => q.quiz_id),
      'assigned': assignedQuizzes.map(q => q.quiz_assignment_id),
      'pending': pendingTests.map(t => t.uqt_id),
      'completed': completedTests.map(t => t.uqt_id)
    };
    
    const setters = {
      'myQuizzes': setSelectedQuizzes,
      'assigned': setSelectedAssigned,
      'pending': setSelectedPending,
      'completed': setSelectedCompleted
    };
    
    const selections = {
      'myQuizzes': selectedQuizzes,
      'assigned': selectedAssigned,
      'pending': selectedPending,
      'completed': selectedCompleted
    };
    
    const itemIds = items[section];
    const current = selections[section];
    const setter = setters[section];
    
    // If all are selected, deselect all; otherwise select all
    if (itemIds.length > 0 && itemIds.every(id => current.has(id))) {
      setter(new Set());
    } else {
      setter(new Set(itemIds));
    }
  };

  const handleDeleteSelected = (section) => {
    setConfirmAction({ type: 'selected', section });
    setShowConfirmModal(true);
  };

  const confirmDeleteSelected = async () => {
    if (!confirmAction || confirmAction.type !== 'selected') return;
    
    const userId = getUserId();
    if (!userId) {
      alert('User ID not found. Please log in again.');
      return;
    }
    
    const section = confirmAction.section;
    const selections = {
      'myQuizzes': Array.from(selectedQuizzes),
      'assigned': Array.from(selectedAssigned),
      'pending': Array.from(selectedPending),
      'completed': Array.from(selectedCompleted)
    };
    
    const ids = selections[section];
    
    if (!ids || ids.length === 0) {
      setShowConfirmModal(false);
      setConfirmAction(null);
      return;
    }
    
    try {
      let result;
      const refreshFunction = () => loadData();
      
      switch (section) {
        case 'pending':
          result = await bulkDeletePendingTests(userId, ids);
          break;
        case 'completed':
          result = await bulkDeleteCompletedTests(userId, ids);
          break;
        case 'myQuizzes':
          result = await bulkDeleteQuizzes(userId, ids);
          break;
        case 'assigned':
          result = await bulkDeleteAssignedQuizzes(userId, ids);
          break;
        default:
          return;
      }
      
      setSuccessMessage(result.message || `Successfully deleted ${result.deleted_count || 0} item(s)`);
      setShowConfirmModal(false);
      setConfirmAction(null);
      
      // Clear selections
      const setters = {
        'myQuizzes': setSelectedQuizzes,
        'assigned': setSelectedAssigned,
        'pending': setSelectedPending,
        'completed': setSelectedCompleted
      };
      setters[section](new Set());
      
      // Refresh data
      await refreshFunction();
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (error) {
      alert('Failed to delete selected items. Please try again.');
      console.error(error);
      setShowConfirmModal(false);
      setConfirmAction(null);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const handleShareQuiz = async (quizId) => {
    try {
      const userId = getUserId();
      const result = await createShareLink(quizId, userId);
      setShareLink(result.share_url);
      navigator.clipboard.writeText(result.share_url);
      alert('Share link copied to clipboard!');
    } catch (error) {
      alert('Failed to create share link. Please try again.');
      console.error(error);
    }
  };

  const handleViewResults = async () => {
    try {
      const userId = getUserId();
      const results = await getAssignmentResults(userId);
      const analytics = await getQuizAnalytics(userId);
      setAssignmentResults(results);
      setQuizAnalytics(analytics);
      setShowResults(true);
    } catch (error) {
      alert('Failed to load assignment results.');
      console.error(error);
    }
  };

  const handleViewQuestionDifficulty = async (quizId) => {
    try {
      const userId = getUserId();
      if (!userId) {
        alert('User not logged in.');
        return;
      }
      const difficulty = await getQuestionDifficulty(quizId, userId);
      if (Array.isArray(difficulty)) {
        setQuestionDifficulty(difficulty);
        setSelectedQuizForDifficulty(myQuizzes.find(q => q.quiz_id === quizId));
        setShowDifficultyModal(true);
      } else {
        console.error('Invalid response format:', difficulty);
        alert('Invalid response from server. Please try again.');
      }
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to load question difficulty analysis.';
      console.error('Error loading question difficulty:', error);
      alert(errorMessage);
    }
  };

  const handleCloseDifficultyModal = () => {
    setShowDifficultyModal(false);
    setQuestionDifficulty([]);
    setSelectedQuizForDifficulty(null);
  };

  const handleExportCSV = async (quizId = null) => {
    try {
      const userId = getUserId();
      if (!userId) {
        alert('User not logged in.');
        return;
      }
      
      const blob = await exportQuizResultsCSV(userId, quizId);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = quizId ? `quiz_results_${quizId}.csv` : `all_quiz_results_${userId}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to export quiz results.';
      console.error('Error exporting CSV:', error);
      alert(errorMessage);
    }
  };

  const QuizCard = ({ quiz, onTakeTest, onViewQuiz, onDelete, onShare, showTakeButton = true, isSelected = false, onSelect = null, section = 'myQuizzes', onViewDifficulty = null, onExportCSV = null }) => {
    const handleCheckboxClick = (e) => {
      e.stopPropagation();
      if (onSelect) {
        const id = section === 'assigned' ? quiz.quiz_assignment_id : quiz.quiz_id;
        onSelect(section, id);
      }
    };
    
    return (
      <div className="quiz-card" style={{ position: 'relative' }}>
        {onSelect && (
          <input
            type="checkbox"
            checked={isSelected}
            onChange={handleCheckboxClick}
            onClick={handleCheckboxClick}
            style={{
              position: 'absolute',
              left: '12px',
              top: '12px',
              width: '20px',
              height: '20px',
              cursor: 'pointer',
              zIndex: 10
            }}
          />
        )}
        <div className="quiz-card-header" style={{ paddingLeft: onSelect ? '40px' : '0' }}>
          <h3>{quiz.quiz_name}</h3>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <span className={`difficulty-badge ${quiz.difficulty_level.toLowerCase()}`}>
              {quiz.difficulty_level}
            </span>
            {onShare && user?.role === 'TEACHER' && (
              <button 
                onClick={(e) => { e.stopPropagation(); onShare(quiz.quiz_id); }} 
                className="share-btn"
                title="Share / Assign Quiz"
                style={{ 
                  background: 'none', 
                  border: 'none', 
                  cursor: 'pointer', 
                  fontSize: '18px',
                  padding: '4px 8px'
                }}
              >
                🔗
              </button>
            )}
            {onDelete && (
              <button 
                onClick={(e) => onDelete(quiz.quiz_id, e)} 
                className="delete-btn"
                title="Delete quiz"
                style={{ 
                  background: 'none', 
                  border: 'none', 
                  cursor: 'pointer', 
                  fontSize: '18px',
                  padding: '4px 8px'
                }}
              >
                🗑️
              </button>
            )}
          </div>
        </div>
        <div className="quiz-card-footer">
          <div className="quiz-info">
            <span>📝 {quiz.total_no_questions} questions</span>
            <span>📅 {formatDate(quiz.created_date)}</span>
          </div>
          <div className="quiz-actions" style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            {onViewQuiz && (
              <button onClick={() => onViewQuiz(quiz.quiz_id)} className="view-quiz-btn" style={{
                padding: '8px 16px',
                backgroundColor: '#6c757d',
                color: 'white',
                border: 'none',
                borderRadius: '5px',
                cursor: 'pointer',
                fontSize: '14px'
              }}>
                View Quiz
              </button>
            )}
            {onViewDifficulty && user?.role === 'TEACHER' && (
              <button onClick={() => onViewDifficulty(quiz.quiz_id)} className="view-difficulty-btn" style={{
                padding: '8px 16px',
                backgroundColor: '#ff9800',
                color: 'white',
                border: 'none',
                borderRadius: '5px',
                cursor: 'pointer',
                fontSize: '14px'
              }}>
                📊 Difficulty
              </button>
            )}
            {onExportCSV && user?.role === 'TEACHER' && (
              <button onClick={() => onExportCSV(quiz.quiz_id)} className="export-csv-btn" style={{
                padding: '8px 16px',
                backgroundColor: '#4caf50',
                color: 'white',
                border: 'none',
                borderRadius: '5px',
                cursor: 'pointer',
                fontSize: '14px'
              }}>
                📥 Export CSV
              </button>
            )}
            {onShare && user?.role === 'TEACHER' && (
              <button onClick={(e) => { e.stopPropagation(); onShare(quiz.quiz_id); }} className="assign-share-btn" style={{
                padding: '8px 16px',
                backgroundColor: '#6C63FF',
                color: 'white',
                border: 'none',
                borderRadius: '5px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '500'
              }}>
                Assign / Share
              </button>
            )}
            {showTakeButton && (
              <button onClick={onTakeTest} className="take-test-btn">
                Take Test
              </button>
            )}
          </div>
        </div>
      </div>
    );
  };

  const TestCard = ({ test, onViewResult, onDelete, isPending, isSelected = false, onSelect = null, section = 'pending' }) => {
    const handleCheckboxClick = (e) => {
      e.stopPropagation();
      if (onSelect) {
        onSelect(section, test.uqt_id);
      }
    };
    
    return (
    <div className="test-card" style={{ position: 'relative' }}>
      {onSelect && (
        <input
          type="checkbox"
          checked={isSelected}
          onChange={handleCheckboxClick}
          onClick={handleCheckboxClick}
          style={{
            position: 'absolute',
            left: '12px',
            top: '12px',
            width: '20px',
            height: '20px',
            cursor: 'pointer',
            zIndex: 10
          }}
        />
      )}
      <div className="test-card-header" style={{ paddingLeft: onSelect ? '40px' : '0' }}>
        <h3>{test.quiz_name}</h3>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          {!isPending && (
            <span className={`score-badge ${test.result >= 70 ? 'pass' : 'fail'}`}>
              {test.result}%
            </span>
          )}
          {isPending && onDelete && (
            <button 
              onClick={(e) => onDelete(test.uqt_id, e)} 
              className="delete-btn"
              title="Delete pending test"
              style={{ 
                background: 'none', 
                border: 'none', 
                cursor: 'pointer', 
                fontSize: '18px',
                padding: '4px 8px'
              }}
            >
              🗑️
            </button>
          )}
        </div>
      </div>
      <div className="test-card-body">
        {isPending ? (
          <>
            <p className="test-status pending">
              {test.status === 'NOT_STARTED' && '🟡 Not Started'}
              {test.status === 'IN_PROGRESS' && '🔵 In Progress'}
              {test.status === 'COMPLETED' && '🟢 Completed'}
              {!test.status && '⏳ Pending'}
            </p>
            {test.due_date && (
              <p className="due-date">Due: {formatDate(test.due_date)}</p>
            )}
          </>
        ) : (
          <>
            <p className="test-status completed">
              {test.status === 'COMPLETED' ? '🟢 Completed' : '✅ Completed'}
            </p>
            <p className="test-score">Score: {test.total_correct}/{test.total_questions}</p>
            <p className="test-date">Completed: {formatDate(test.completed_time)}</p>
          </>
        )}
      </div>
      <button onClick={onViewResult} className="view-btn">
        {isPending ? (test.status === 'IN_PROGRESS' ? 'Continue Test' : 'Take Test') : 'View Results'}
      </button>
    </div>
    );
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading your dashboard...</p>
      </div>
    );
  }

  // Confirmation Modal Component
  const ConfirmModal = () => {
    if (!showConfirmModal) return null;
    
    const isSelectedDelete = confirmAction && confirmAction.type === 'selected';
    const section = isSelectedDelete ? confirmAction.section : confirmAction;
    
    const getSectionName = () => {
      switch (section) {
        case 'pending': return 'Pending Tests';
        case 'completed': return 'Completed Tests';
        case 'myQuizzes': return 'My Quizzes';
        case 'assigned': return 'Assigned Quizzes';
        default: return 'items';
      }
    };
    
    const getSelectedCount = () => {
      if (!isSelectedDelete) return 0;
      const selections = {
        'myQuizzes': selectedQuizzes.size,
        'assigned': selectedAssigned.size,
        'pending': selectedPending.size,
        'completed': selectedCompleted.size
      };
      return selections[section] || 0;
    };
    
    const handleConfirm = () => {
      if (isSelectedDelete) {
        confirmDeleteSelected();
      } else {
        confirmDeleteAll();
      }
    };
    
    return (
      <div className="modal-overlay" onClick={cancelDeleteAll}>
        <div className="modal-content" onClick={(e) => e.stopPropagation()}>
          <h2>{isSelectedDelete ? 'Confirm Delete Selected' : 'Confirm Delete All'}</h2>
          <p>
            {isSelectedDelete 
              ? `Are you sure you want to delete ${getSelectedCount()} selected ${getSectionName().toLowerCase()}? This action cannot be undone.`
              : `Are you sure you want to delete all ${getSectionName()}? This action cannot be undone.`
            }
          </p>
          <div className="modal-actions">
            <button className="btn-cancel" onClick={cancelDeleteAll}>
              Cancel
            </button>
            <button className="btn-delete" onClick={handleConfirm}>
              {isSelectedDelete ? 'Delete Selected' : 'Delete All'}
            </button>
          </div>
        </div>
      </div>
    );
  };

  // Badge name mapping
  const badgeNames = {
    'first_quiz': 'First Quiz Completed',
    'five_quizzes': '5 Quizzes Completed',
    'ten_quizzes': '10 Quizzes Completed'
  };

  return (
    <div className="dashboard-container">
      {/* Badge Notification Toast */}
      {newBadgeNotification && newBadgeNotification.length > 0 && (
        <div style={{
          position: 'fixed',
          top: '20px',
          right: '20px',
          zIndex: 9999,
          backgroundColor: '#4CAF50',
          color: 'white',
          padding: '16px 24px',
          borderRadius: '8px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
          animation: 'slideIn 0.3s ease-out'
        }}>
          <div style={{ fontSize: '18px', fontWeight: '600', marginBottom: '8px' }}>
            🎉 New Badge Unlocked!
          </div>
          {newBadgeNotification.map((badgeId, idx) => (
            <div key={idx} style={{ fontSize: '14px', marginTop: '4px' }}>
              {badgeNames[badgeId] || badgeId}
            </div>
          ))}
        </div>
      )}

      {/* Stats Display */}
      {userStats && (
        <div style={{
          marginBottom: '20px',
          padding: '16px',
          backgroundColor: '#F6F8FF',
          border: '1px solid #E0E5FF',
          borderRadius: '8px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {userStats.current_streak > 0 && (
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontSize: '18px',
                fontWeight: '600',
                color: '#1F2937'
              }}>
                <span>🔥</span>
                <span>{userStats.current_streak}-day streak</span>
              </div>
            )}
            {userStats.current_streak === 0 && (
              <div style={{ fontSize: '14px', color: '#6B7280' }}>
                Start your streak today!
              </div>
            )}
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
            <div style={{ fontSize: '14px', color: '#6B7280' }}>
              <span style={{ fontWeight: '600', color: '#1F2937' }}>{userStats.quiz_completion_count}</span> quizzes completed
            </div>
            
            {userStats.unlocked_badges && userStats.unlocked_badges.length > 0 && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                <span style={{ fontSize: '14px', color: '#6B7280' }}>Badges:</span>
                {userStats.unlocked_badges.map((badgeId, idx) => (
                  <span
                    key={idx}
                    style={{
                      backgroundColor: '#6C63FF',
                      color: 'white',
                      padding: '4px 12px',
                      borderRadius: '12px',
                      fontSize: '12px',
                      fontWeight: '500'
                    }}
                    title={badgeNames[badgeId] || badgeId}
                  >
                    {badgeNames[badgeId] || badgeId}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
      {successMessage && (
        <div className="success-message" style={{
          position: 'fixed',
          top: '20px',
          right: '20px',
          background: '#4CAF50',
          color: 'white',
          padding: '12px 24px',
          borderRadius: '8px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
          zIndex: 1000
        }}>
          {successMessage}
        </div>
      )}
      
      <ConfirmModal />
      
      <div className="dashboard-header">
        <h1>Welcome back, {user.first_name}! 👋</h1>
        <p className="subtitle">Your learning dashboard</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">📚</div>
          <div className="stat-content">
            <h3>{myQuizzes.length}</h3>
            <p>My Quizzes</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">📋</div>
          <div className="stat-content">
            <h3>{assignedQuizzes.length}</h3>
            <p>Assigned Quizzes</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">⏳</div>
          <div className="stat-content">
            <h3>{pendingTests.length}</h3>
            <p>Pending Tests</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">✅</div>
          <div className="stat-content">
            <h3>{completedTests.length}</h3>
            <p>Completed</p>
          </div>
        </div>
      </div>

      <div className="tabs-container">
        <div className="tabs">
          <button
            className={`tab ${activeTab === 'myQuizzes' ? 'active' : ''}`}
            onClick={() => setActiveTab('myQuizzes')}
          >
            My Quizzes ({myQuizzes.length})
          </button>
          <button
            className={`tab ${activeTab === 'assigned' ? 'active' : ''}`}
            onClick={() => setActiveTab('assigned')}
          >
            Assigned to Me ({assignedQuizzes.length})
          </button>
          <button
            className={`tab ${activeTab === 'pending' ? 'active' : ''}`}
            onClick={() => setActiveTab('pending')}
          >
            Pending Tests ({pendingTests.length})
          </button>
          <button
            className={`tab ${activeTab === 'completed' ? 'active' : ''}`}
            onClick={() => setActiveTab('completed')}
          >
            Completed ({completedTests.length})
          </button>
        </div>

        {shareLink && (
          <div style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#e8f5e9', borderRadius: '8px', border: '1px solid #4caf50' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
              <div style={{ flex: 1, minWidth: '200px' }}>
                <strong>Share Link Created:</strong>
                <p style={{ margin: '5px 0', wordBreak: 'break-all', color: '#2e7d32' }}>{shareLink}</p>
              </div>
              <div style={{ display: 'flex', gap: '10px' }}>
                <button 
                  onClick={() => {
                    navigator.clipboard.writeText(shareLink);
                    alert('Link copied to clipboard!');
                  }}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: '#4caf50',
                    color: 'white',
                    border: 'none',
                    borderRadius: '5px',
                    cursor: 'pointer',
                    fontSize: '14px'
                  }}
                >
                  Copy
                </button>
                <button 
                  onClick={() => setShareLink(null)}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: '#f44336',
                    color: 'white',
                    border: 'none',
                    borderRadius: '5px',
                    cursor: 'pointer',
                    fontSize: '14px'
                  }}
                >
                  ✕
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="tab-content">
          {activeTab === 'myQuizzes' && (
            <div>
              {myQuizzes.length > 0 && (
                <div style={{ marginBottom: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <input
                      type="checkbox"
                      checked={myQuizzes.length > 0 && myQuizzes.every(q => selectedQuizzes.has(q.quiz_id))}
                      onChange={() => handleSelectAll('myQuizzes')}
                      style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                    />
                    <span style={{ fontSize: '14px', color: '#666' }}>Select All</span>
                  </div>
                  <div style={{ display: 'flex', gap: '10px' }}>
                    {selectedQuizzes.size > 0 && (
                      <button 
                        onClick={() => handleDeleteSelected('myQuizzes')}
                        className="delete-selected-btn"
                        style={{
                          background: '#ff9800',
                          color: 'white',
                          border: 'none',
                          padding: '10px 20px',
                          borderRadius: '6px',
                          cursor: 'pointer',
                          fontSize: '14px',
                          fontWeight: '500'
                        }}
                      >
                        🗑️ Delete Selected ({selectedQuizzes.size})
                      </button>
                    )}
                    <button 
                      onClick={() => handleDeleteAll('myQuizzes')}
                      className="delete-all-btn"
                      style={{
                        background: '#f44336',
                        color: 'white',
                        border: 'none',
                        padding: '10px 20px',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontSize: '14px',
                        fontWeight: '500'
                      }}
                    >
                      🗑️ Delete All
                    </button>
                  </div>
                </div>
              )}
              <div className="quiz-grid">
                {myQuizzes.length === 0 ? (
                  <div className="empty-state">
                    <p>📚 No quizzes yet. Create your first quiz!</p>
                    <button onClick={() => navigate('/create-quiz')} className="create-quiz-btn">
                      Create Quiz
                    </button>
                  </div>
                ) : (
                  myQuizzes.map(quiz => (
                    <QuizCard
                      key={quiz.quiz_id}
                      quiz={quiz}
                      onTakeTest={() => handleTakeTest(quiz.quiz_id)}
                      onViewQuiz={handleViewQuiz}
                      onDelete={handleDeleteQuiz}
                      onShare={handleShareQuiz}
                      onViewDifficulty={handleViewQuestionDifficulty}
                      onExportCSV={handleExportCSV}
                      isSelected={selectedQuizzes.has(quiz.quiz_id)}
                      onSelect={handleSelectItem}
                      section="myQuizzes"
                      showTakeButton={true}
                    />
                  ))
                )}
              </div>
            </div>
          )}

          {activeTab === 'assigned' && (
            <div>
              {user?.role === 'TEACHER' && (
                <div style={{ marginBottom: '20px', display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: '10px' }}>
                  <button onClick={() => handleExportCSV()} style={{
                    padding: '10px 20px',
                    backgroundColor: '#4caf50',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '14px',
                    fontWeight: '500'
                  }}>
                    📥 Export All Results (CSV)
                  </button>
                  <button onClick={handleViewResults} style={{
                    padding: '10px 20px',
                    backgroundColor: '#6C63FF',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '14px',
                    fontWeight: '500'
                  }}>
                    View Quiz Analytics
                  </button>
                </div>
              )}
              {assignedQuizzes.length > 0 && (
                <div style={{ marginBottom: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <input
                      type="checkbox"
                      checked={assignedQuizzes.length > 0 && assignedQuizzes.every(q => selectedAssigned.has(q.quiz_assignment_id))}
                      onChange={() => handleSelectAll('assigned')}
                      style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                    />
                    <span style={{ fontSize: '14px', color: '#666' }}>Select All</span>
                  </div>
                  <div style={{ display: 'flex', gap: '10px' }}>
                    {selectedAssigned.size > 0 && (
                      <button 
                        onClick={() => handleDeleteSelected('assigned')}
                        className="delete-selected-btn"
                        style={{
                          background: '#ff9800',
                          color: 'white',
                          border: 'none',
                          padding: '10px 20px',
                          borderRadius: '6px',
                          cursor: 'pointer',
                          fontSize: '14px',
                          fontWeight: '500'
                        }}
                      >
                        🗑️ Delete Selected ({selectedAssigned.size})
                      </button>
                    )}
                    <button 
                      onClick={() => handleDeleteAll('assigned')}
                      className="delete-all-btn"
                      style={{
                        background: '#f44336',
                        color: 'white',
                        border: 'none',
                        padding: '10px 20px',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontSize: '14px',
                        fontWeight: '500'
                      }}
                    >
                      🗑️ Delete All
                    </button>
                  </div>
                </div>
              )}
              <div className="quiz-grid">
                {assignedQuizzes.length === 0 ? (
                  <div className="empty-state">
                    <p>📋 No quizzes assigned to you yet.</p>
                  </div>
                ) : (
                  assignedQuizzes.map(quiz => (
                    <QuizCard
                      key={quiz.quiz_id}
                      quiz={quiz}
                      onTakeTest={() => handleTakeTest(quiz.quiz_id, quiz.quiz_assignment_id)}
                      onViewQuiz={handleViewQuiz}
                      isSelected={selectedAssigned.has(quiz.quiz_assignment_id)}
                      onSelect={handleSelectItem}
                      section="assigned"
                    />
                  ))
                )}
              </div>
            </div>
          )}

          {activeTab === 'pending' && (
            <div>
              {pendingTests.length > 0 && (
                <div style={{ marginBottom: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <input
                      type="checkbox"
                      checked={pendingTests.length > 0 && pendingTests.every(t => selectedPending.has(t.uqt_id))}
                      onChange={() => handleSelectAll('pending')}
                      style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                    />
                    <span style={{ fontSize: '14px', color: '#666' }}>Select All</span>
                  </div>
                  <div style={{ display: 'flex', gap: '10px' }}>
                    {selectedPending.size > 0 && (
                      <button 
                        onClick={() => handleDeleteSelected('pending')}
                        className="delete-selected-btn"
                        style={{
                          background: '#ff9800',
                          color: 'white',
                          border: 'none',
                          padding: '10px 20px',
                          borderRadius: '6px',
                          cursor: 'pointer',
                          fontSize: '14px',
                          fontWeight: '500'
                        }}
                      >
                        🗑️ Delete Selected ({selectedPending.size})
                      </button>
                    )}
                    <button 
                      onClick={() => handleDeleteAll('pending')}
                      className="delete-all-btn"
                      style={{
                        background: '#f44336',
                        color: 'white',
                        border: 'none',
                        padding: '10px 20px',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontSize: '14px',
                        fontWeight: '500'
                      }}
                    >
                      🗑️ Delete All
                    </button>
                  </div>
                </div>
              )}
              <div className="test-grid">
                {pendingTests.length === 0 ? (
                  <div className="empty-state">
                    <p>⏳ No pending tests.</p>
                  </div>
                ) : (
                  pendingTests.map(test => (
                    <TestCard
                      key={test.uqt_id}
                      test={test}
                      isPending={true}
                      onViewResult={() => handleTakeTest(test.quiz_id, test.quiz_assignment_id ?? null)}
                      onDelete={handleDeletePendingTest}
                      isSelected={selectedPending.has(test.uqt_id)}
                      onSelect={handleSelectItem}
                      section="pending"
                    />
                  ))
                )}
              </div>
            </div>
          )}

          {activeTab === 'completed' && (
            <div>
              {completedTests.length > 0 && (
                <div style={{ marginBottom: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <input
                      type="checkbox"
                      checked={completedTests.length > 0 && completedTests.every(t => selectedCompleted.has(t.uqt_id))}
                      onChange={() => handleSelectAll('completed')}
                      style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                    />
                    <span style={{ fontSize: '14px', color: '#666' }}>Select All</span>
                  </div>
                  <div style={{ display: 'flex', gap: '10px' }}>
                    {selectedCompleted.size > 0 && (
                      <button 
                        onClick={() => handleDeleteSelected('completed')}
                        className="delete-selected-btn"
                        style={{
                          background: '#ff9800',
                          color: 'white',
                          border: 'none',
                          padding: '10px 20px',
                          borderRadius: '6px',
                          cursor: 'pointer',
                          fontSize: '14px',
                          fontWeight: '500'
                        }}
                      >
                        🗑️ Delete Selected ({selectedCompleted.size})
                      </button>
                    )}
                    <button 
                      onClick={() => handleDeleteAll('completed')}
                      className="delete-all-btn"
                      style={{
                        background: '#f44336',
                        color: 'white',
                        border: 'none',
                        padding: '10px 20px',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontSize: '14px',
                        fontWeight: '500'
                      }}
                    >
                      🗑️ Delete All
                    </button>
                  </div>
                </div>
              )}
              <div className="test-grid">
                {completedTests.length === 0 ? (
                  <div className="empty-state">
                    <p>✅ No completed tests yet.</p>
                  </div>
                ) : (
                  completedTests.map(test => (
                    <TestCard
                      key={test.uqt_id}
                      test={test}
                      isPending={false}
                      onViewResult={() => handleViewResult(test)}
                      isSelected={selectedCompleted.has(test.uqt_id)}
                      onSelect={handleSelectItem}
                      section="completed"
                    />
                  ))
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Quiz Analytics Modal */}
      {showResults && user?.role === 'TEACHER' && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            padding: '30px',
            borderRadius: '12px',
            maxWidth: '800px',
            maxHeight: '80vh',
            overflowY: 'auto',
            width: '90%',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3 style={{ margin: 0, fontSize: '24px', color: '#1F2937' }}>Quiz Analytics Dashboard</h3>
              <button 
                onClick={() => setShowResults(false)} 
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '24px',
                  cursor: 'pointer',
                  color: '#666',
                  padding: '0',
                  width: '30px',
                  height: '30px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                ✕
              </button>
            </div>
            
            {quizAnalytics.length === 0 ? (
              <p style={{ color: '#666', textAlign: 'center', padding: '20px' }}>
                No quiz analytics available. Assign quizzes to students to see analytics.
              </p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                {quizAnalytics.map((analytics) => (
                  <div 
                    key={analytics.quiz_id}
                    style={{
                      border: '1px solid #E0E5FF',
                      borderRadius: '8px',
                      padding: '20px',
                      backgroundColor: '#F6F8FF'
                    }}
                  >
                    <h4 style={{ margin: '0 0 15px 0', fontSize: '18px', color: '#1F2937', fontWeight: '600' }}>
                      {analytics.quiz_name}
                    </h4>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '15px' }}>
                      <div>
                        <div style={{ fontSize: '12px', color: '#6B7280', marginBottom: '5px' }}>Total Students</div>
                        <div style={{ fontSize: '20px', fontWeight: '600', color: '#1F2937' }}>
                          {analytics.total_students || 0}
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: '12px', color: '#6B7280', marginBottom: '5px' }}>Attempted</div>
                        <div style={{ fontSize: '20px', fontWeight: '600', color: '#1F2937' }}>
                          {analytics.attempted || 0}
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: '12px', color: '#6B7280', marginBottom: '5px' }}>Average Score</div>
                        <div style={{ fontSize: '20px', fontWeight: '600', color: '#6C63FF' }}>
                          {analytics.attempted > 0 ? `${analytics.average_score.toFixed(1)}%` : 'N/A'}
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: '12px', color: '#6B7280', marginBottom: '5px' }}>Highest Score</div>
                        <div style={{ fontSize: '20px', fontWeight: '600', color: '#4caf50' }}>
                          {analytics.attempted > 0 ? `${analytics.highest_score.toFixed(1)}%` : 'N/A'}
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: '12px', color: '#6B7280', marginBottom: '5px' }}>Lowest Score</div>
                        <div style={{ fontSize: '20px', fontWeight: '600', color: '#f44336' }}>
                          {analytics.attempted > 0 ? `${analytics.lowest_score.toFixed(1)}%` : 'N/A'}
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: '12px', color: '#6B7280', marginBottom: '5px' }}>Total Questions</div>
                        <div style={{ fontSize: '20px', fontWeight: '600', color: '#1F2937' }}>
                          {analytics.total_questions || 0}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
            
            <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'flex-end' }}>
              <button 
                onClick={() => setShowResults(false)} 
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#6C63FF',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: '500'
                }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Question Difficulty Modal */}
      {showDifficultyModal && user?.role === 'TEACHER' && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            padding: '30px',
            borderRadius: '12px',
            maxWidth: '900px',
            maxHeight: '80vh',
            overflowY: 'auto',
            width: '90%',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3 style={{ margin: 0, fontSize: '24px', color: '#1F2937' }}>
                Question Difficulty Analysis
                {selectedQuizForDifficulty && ` - ${selectedQuizForDifficulty.quiz_name}`}
              </h3>
              <button 
                onClick={handleCloseDifficultyModal} 
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '24px',
                  cursor: 'pointer',
                  color: '#666',
                  padding: '0',
                  width: '30px',
                  height: '30px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                ✕
              </button>
            </div>
            
            {questionDifficulty.length === 0 ? (
              <p style={{ color: '#666', textAlign: 'center', padding: '20px' }}>
                No question difficulty data available. Students need to complete the quiz first.
              </p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                {questionDifficulty.map((item, index) => {
                  const getDifficultyColor = (percentage) => {
                    if (percentage >= 70) return '#f44336'; // Red
                    if (percentage >= 40) return '#ff9800'; // Yellow/Orange
                    return '#4caf50'; // Green
                  };
                  
                  const getDifficultyEmoji = (percentage) => {
                    if (percentage >= 70) return '🔴';
                    if (percentage >= 40) return '🟡';
                    return '🟢';
                  };

                  const difficultyColor = getDifficultyColor(item.incorrect_percentage);
                  const difficultyEmoji = getDifficultyEmoji(item.incorrect_percentage);

                  return (
                    <div 
                      key={item.question_id}
                      style={{
                        border: `2px solid ${difficultyColor}`,
                        borderRadius: '8px',
                        padding: '20px',
                        backgroundColor: '#F6F8FF'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontSize: '14px', color: '#6B7280', marginBottom: '5px' }}>
                            Question {index + 1}
                          </div>
                          <div style={{ fontSize: '16px', fontWeight: '600', color: '#1F2937', marginBottom: '10px' }}>
                            {item.question_text}
                          </div>
                        </div>
                        <div style={{ fontSize: '24px', marginLeft: '15px' }}>
                          {difficultyEmoji}
                        </div>
                      </div>
                      <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
                        <div>
                          <div style={{ fontSize: '12px', color: '#6B7280', marginBottom: '3px' }}>Total Attempts</div>
                          <div style={{ fontSize: '18px', fontWeight: '600', color: '#1F2937' }}>
                            {item.total_attempts || 0}
                          </div>
                        </div>
                        <div>
                          <div style={{ fontSize: '12px', color: '#6B7280', marginBottom: '3px' }}>Incorrect Percentage</div>
                          <div style={{ fontSize: '18px', fontWeight: '600', color: difficultyColor }}>
                            {item.incorrect_percentage.toFixed(1)}%
                          </div>
                        </div>
                        <div style={{ flex: 1, textAlign: 'right' }}>
                          <span style={{ 
                            fontSize: '14px', 
                            color: difficultyColor,
                            fontWeight: '500'
                          }}>
                            {item.incorrect_percentage >= 70 
                              ? '❌ Very Difficult' 
                              : item.incorrect_percentage >= 40 
                              ? '⚠️ Moderate Difficulty' 
                              : '✅ Easy'}
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
            
            <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'flex-end' }}>
              <button 
                onClick={handleCloseDifficultyModal} 
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#6C63FF',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: '500'
                }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;

