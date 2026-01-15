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
  exportQuizResultsCSV
} from '../services/api';
import { 
  Button, 
  Card, 
  Badge, 
  Table, 
  TableCellBold, 
  TableCellActions,
  ControlledTabs,
  ConfirmModal
} from '../components/ui';
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
      
      const [quizzes, assigned, pending, completed] = await Promise.all([
        getUserQuizzes(userId).catch(() => []),
        getAssignedQuizzes(userId).catch(() => []),
        getPendingTests(userId).catch(() => []),
        getCompletedTests(userId).catch(() => [])
      ]);
      
      // Ensure we have arrays (handle null/undefined responses)
      const quizzesArray = Array.isArray(quizzes) ? quizzes : [];
      const assignedArray = Array.isArray(assigned) ? assigned : [];
      const pendingArray = Array.isArray(pending) ? pending : [];
      const completedArray = Array.isArray(completed) ? completed : [];
      
      // DEBUG: Log assigned quizzes data
      console.log('[DASHBOARD] Assigned Quizzes Data:', {
        count: assignedArray.length,
        data: assignedArray,
        sample: assignedArray[0]
      });
      
      // NO FILTERING - Set pending tests directly as received from API
      // Includes both NOT_STARTED and IN_PROGRESS tests
      setMyQuizzes(quizzesArray);
      setAssignedQuizzes(assignedArray);
      setPendingTests(pendingArray);
      setCompletedTests(completedArray);
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
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return 'N/A';
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getFeedbackLabel = (score, total) => {
    // Check for null/undefined/0 for total, but allow 0 for score
    if (score === null || score === undefined || total === null || total === undefined || total === 0) {
      return 'N/A';
    }
    const percentage = (score / total) * 100;
    if (percentage >= 80) return 'Excellent';
    if (percentage >= 60) return 'Good';
    if (percentage >= 40) return 'Average';
    return 'Needs Improvement';
  };

  const getFeedbackClass = (score, total) => {
    // Check for null/undefined/0 for total, but allow 0 for score
    if (score === null || score === undefined || total === null || total === undefined || total === 0) {
      return '';
    }
    const percentage = (score / total) * 100;
    if (percentage >= 80) return 'excellent';
    if (percentage >= 60) return 'good';
    if (percentage >= 40) return 'average';
    return 'needs-improvement';
  };

  const handleShareQuiz = async (quizId) => {
    try {
      const userId = getUserId();
      const result = await createShareLink(quizId, userId);
      setShareLink(result.share_url);
      navigator.clipboard.writeText(result.share_url);
      
      // Show non-blocking success message
      setSuccessMessage('✓ Share link copied to clipboard!');
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (error) {
      setSuccessMessage('✗ Failed to create share link. Please try again.');
      setTimeout(() => setSuccessMessage(''), 3000);
      console.error(error);
    }
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

  const QuizCard = ({ quiz, onTakeTest, onViewQuiz, onDelete, onShare, showTakeButton = true, isSelected = false, onSelect = null, section = 'myQuizzes', onExportCSV = null }) => {
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
          <h3>{quiz.quiz_name || 'Untitled Quiz'}</h3>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <span className={`difficulty-badge ${(quiz.difficulty_level || 'medium').toLowerCase()}`}>
              {quiz.difficulty_level || 'Medium'}
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
            <span>📝 {quiz.total_no_questions || 0} questions</span>
            <span>📅 {quiz.created_date ? formatDate(quiz.created_date) : (quiz.assign_date ? formatDate(quiz.assign_date) : 'N/A')}</span>
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
  return (
    <div className="dashboard-container">
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
        <div className="stat-card stat-card-1">
          <div className="stat-icon stat-icon-1">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
            </svg>
          </div>
          <div className="stat-content">
            <h3>{myQuizzes.length}</h3>
            <p>My Quizzes</p>
          </div>
        </div>
        <div className="stat-card stat-card-2">
          <div className="stat-icon stat-icon-2">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25zM6.75 12h.008v.008H6.75V12zm0 3h.008v.008H6.75V15zm0 3h.008v.008H6.75V18z" />
            </svg>
          </div>
          <div className="stat-content">
            <h3>{assignedQuizzes.length}</h3>
            <p>Assigned Quizzes</p>
          </div>
        </div>
        <div className="stat-card stat-card-3">
          <div className="stat-icon stat-icon-3">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div className="stat-content">
            <h3>{pendingTests.length}</h3>
            <p>Pending Tests</p>
          </div>
        </div>
        <div className="stat-card stat-card-4">
          <div className="stat-icon stat-icon-4">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
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
                    setSuccessMessage('✓ Link copied to clipboard!');
                    setTimeout(() => setSuccessMessage(''), 3000);
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
                  </div>
                </div>
              )}
              {myQuizzes.length === 0 ? (
                <div className="empty-state">
                  <p>📚 No quizzes yet. Create your first quiz!</p>
                  <button onClick={() => navigate('/create-quiz')} className="create-quiz-btn">
                    Create Quiz
                  </button>
                </div>
              ) : (
                <>
                  {/* Table view for desktop */}
                  <div className="quiz-table-container">
                    <table className="quiz-table">
                      <thead>
                        <tr>
                          <th style={{ width: '40px' }}></th>
                          <th>Quiz Name</th>
                          <th>Diff.</th>
                          <th>Qs</th>
                          <th>Created</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {myQuizzes.map(quiz => (
                          <tr key={quiz.quiz_id} className="quiz-table-row">
                            <td>
                              <input
                                type="checkbox"
                                checked={selectedQuizzes.has(quiz.quiz_id)}
                                onChange={(e) => {
                                  e.stopPropagation();
                                  handleSelectItem('myQuizzes', quiz.quiz_id);
                                }}
                                style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                              />
                            </td>
                            <td className="quiz-name-cell">
                              <strong>{quiz.quiz_name}</strong>
                            </td>
                            <td>
                              <span className={`difficulty-badge ${quiz.difficulty_level.toLowerCase()}`}>
                                {quiz.difficulty_level}
                              </span>
                            </td>
                            <td>📝 {quiz.total_no_questions}</td>
                            <td>{formatDate(quiz.created_date)}</td>
                            <td>
                              <div className="action-buttons">
                                <button 
                                  onClick={() => handleViewQuiz(quiz.quiz_id)} 
                                  className="action-btn view-btn-icon"
                                  title="View Quiz"
                                >
                                  👁️
                                </button>
                                {user?.role === 'TEACHER' && (
                                  <>
                                    <button 
                                      onClick={() => handleExportCSV(quiz.quiz_id)} 
                                      className="action-btn export-btn-icon"
                                      title="Export CSV"
                                    >
                                      📥
                                    </button>
                                    <button 
                                      onClick={() => handleShareQuiz(quiz.quiz_id)} 
                                      className="action-btn share-btn-icon"
                                      title="Assign / Share"
                                    >
                                      🔗
                                    </button>
                                  </>
                                )}
                                <button 
                                  onClick={() => handleTakeTest(quiz.quiz_id)} 
                                  className="action-btn take-test-btn-icon"
                                  title="Take Test"
                                >
                                  ▶️
                                </button>
                                <button 
                                  onClick={(e) => handleDeleteQuiz(quiz.quiz_id, e)} 
                                  className="action-btn delete-btn-icon"
                                  title="Delete"
                                >
                                  🗑️
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  
                  {/* Card view for mobile */}
                  <div className="quiz-grid">
                    {myQuizzes.map(quiz => (
                      <QuizCard
                        key={quiz.quiz_id}
                        quiz={quiz}
                        onTakeTest={() => handleTakeTest(quiz.quiz_id)}
                        onViewQuiz={handleViewQuiz}
                        onDelete={handleDeleteQuiz}
                        onShare={handleShareQuiz}
                        onExportCSV={handleExportCSV}
                        isSelected={selectedQuizzes.has(quiz.quiz_id)}
                        onSelect={handleSelectItem}
                        section="myQuizzes"
                        showTakeButton={true}
                      />
                    ))}
                  </div>
                </>
              )}
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
                  </div>
                </div>
              )}
              {assignedQuizzes.length === 0 ? (
                <div className="empty-state">
                  <p>📋 No quizzes assigned to you yet.</p>
                </div>
              ) : (
                <>
                  {/* Table view for desktop */}
                  <div className="quiz-table-container">
                    <table className="quiz-table">
                      <thead>
                        <tr>
                          <th style={{ width: '40px' }}></th>
                          <th>Quiz Name</th>
                          <th>Diff.</th>
                          <th>Qs</th>
                          <th>Assigned</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {assignedQuizzes.map((quiz, index) => {
                          console.log(`[DASHBOARD] Rendering assigned quiz ${index}:`, quiz);
                          return (
                            <tr key={quiz.quiz_assignment_id || `assigned-${quiz.quiz_id}-${index}`} className="quiz-table-row">
                              <td>
                                <input
                                  type="checkbox"
                                  checked={selectedAssigned.has(quiz.quiz_assignment_id)}
                                  onChange={(e) => {
                                    e.stopPropagation();
                                    handleSelectItem('assigned', quiz.quiz_assignment_id);
                                  }}
                                  style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                                />
                              </td>
                              <td className="quiz-name-cell">
                                <strong>{quiz.quiz_name || 'Untitled Quiz'}</strong>
                              </td>
                              <td>
                                <span className={`difficulty-badge ${(quiz.difficulty_level || 'medium').toLowerCase()}`}>
                                  {quiz.difficulty_level || 'Medium'}
                                </span>
                              </td>
                              <td>📝 {quiz.total_no_questions || quiz.total_questions || 0}</td>
                              <td>{quiz.assign_date ? formatDate(quiz.assign_date) : (quiz.created_date ? formatDate(quiz.created_date) : 'N/A')}</td>
                              <td>
                                <div className="action-buttons">
                                  <button 
                                    onClick={() => handleViewQuiz(quiz.quiz_id)} 
                                    className="action-btn view-btn-icon"
                                    title="View Quiz"
                                  >
                                    👁️
                                  </button>
                                  <button 
                                    onClick={() => handleTakeTest(quiz.quiz_id, quiz.quiz_assignment_id)} 
                                    className="action-btn"
                                    title="Take Test"
                                    style={{
                                      backgroundColor: '#4caf50',
                                      color: 'white',
                                      border: 'none'
                                    }}
                                  >
                                    ✏️
                                  </button>
                                </div>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>

                  {/* Card view for mobile/tablet */}
                  <div className="quiz-grid" style={{ display: 'none' }}>
                    {assignedQuizzes.map((quiz, index) => (
                      <QuizCard
                        key={quiz.quiz_assignment_id || `assigned-${quiz.quiz_id}-${index}`}
                        quiz={quiz}
                        onTakeTest={() => handleTakeTest(quiz.quiz_id, quiz.quiz_assignment_id)}
                        onViewQuiz={handleViewQuiz}
                        isSelected={selectedAssigned.has(quiz.quiz_assignment_id)}
                        onSelect={handleSelectItem}
                        section="assigned"
                      />
                    ))}
                  </div>
                </>
              )}
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
                  </div>
                </div>
              )}
              {pendingTests.length === 0 ? (
                <div className="empty-state">
                  <p>⏳ No pending tests.</p>
                </div>
              ) : (
                <>
                  {/* Table view for desktop */}
                  <div className="quiz-table-container">
                    <table className="quiz-table">
                      <thead>
                        <tr>
                          <th style={{ width: '40px' }}></th>
                          <th>Quiz Name</th>
                          <th>Diff.</th>
                          <th>Qs</th>
                          <th>Status</th>
                          <th>Date</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {pendingTests.map(test => (
                          <tr key={test.uqt_id} className="quiz-table-row">
                            <td>
                              <input
                                type="checkbox"
                                checked={selectedPending.has(test.uqt_id)}
                                onChange={(e) => {
                                  e.stopPropagation();
                                  handleSelectItem('pending', test.uqt_id);
                                }}
                                style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                              />
                            </td>
                            <td className="quiz-name-cell">
                              <strong>{test.quiz_name}</strong>
                            </td>
                            <td>
                              <span className={`difficulty-badge ${test.difficulty_level?.toLowerCase() || 'medium'}`}>
                                {test.difficulty_level || 'Medium'}
                              </span>
                            </td>
                            <td>📝 {test.total_questions || test.total_no_questions || 0}</td>
                            <td>
                              <span className="status-badge pending">
                                ⏳ Pending
                              </span>
                            </td>
                            <td>{formatDate(test.start_time)}</td>
                            <td>
                              <div className="action-buttons">
                                <button 
                                  onClick={() => handleTakeTest(test.quiz_id, test.quiz_assignment_id ?? null)} 
                                  className="action-btn take-test-btn-icon"
                                  title="Continue / Start Test"
                                >
                                  ▶️
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  
                  {/* Card view for mobile */}
                  <div className="test-grid">
                    {pendingTests.map(test => (
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
                    ))}
                  </div>
                </>
              )}
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
                  </div>
                </div>
              )}
              {completedTests.length === 0 ? (
                <div className="empty-state">
                  <p>✅ No completed tests yet.</p>
                </div>
              ) : (
                <>
                  {/* Table view for desktop */}
                  <div className="quiz-table-container">
                    <table className="quiz-table">
                      <thead>
                        <tr>
                          <th style={{ width: '40px' }}></th>
                          <th>Quiz Name</th>
                          <th>Diff.</th>
                          <th>Qs</th>
                          <th>Score</th>
                          <th>Feedback</th>
                          <th>Date</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {completedTests.map(test => {
                          const totalQuestions = test.total_questions || test.total_no_questions || 0;
                          // For completed tests, default to 0 if score is missing (should not happen)
                          // This ensures we NEVER show N/A for completed tests
                          const score = test.total_correct !== null && test.total_correct !== undefined 
                            ? test.total_correct 
                            : 0;
                          const feedbackLabel = getFeedbackLabel(score, totalQuestions);
                          const feedbackClass = getFeedbackClass(score, totalQuestions);
                          
                          return (
                            <tr key={test.uqt_id} className="quiz-table-row">
                              <td>
                                <input
                                  type="checkbox"
                                  checked={selectedCompleted.has(test.uqt_id)}
                                  onChange={(e) => {
                                    e.stopPropagation();
                                    handleSelectItem('completed', test.uqt_id);
                                  }}
                                  style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                                />
                              </td>
                              <td className="quiz-name-cell">
                                <strong>{test.quiz_name}</strong>
                              </td>
                              <td>
                                <span className={`difficulty-badge ${test.difficulty_level?.toLowerCase() || 'medium'}`}>
                                  {test.difficulty_level || 'Medium'}
                                </span>
                              </td>
                              <td>📝 {totalQuestions}</td>
                              <td>
                                <strong>{score}/{totalQuestions}</strong>
                              </td>
                              <td>
                                <span className={`feedback-badge ${feedbackClass}`}>
                                  {feedbackLabel}
                                </span>
                              </td>
                              <td>{formatDate(test.completed_time)}</td>
                              <td>
                                <div className="action-buttons">
                                  <button 
                                    onClick={() => handleViewResult(test)} 
                                    className="action-btn view-btn-icon"
                                    title="View Results"
                                  >
                                    📊
                                  </button>
                                </div>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                  
                  {/* Card view for mobile */}
                  <div className="test-grid">
                    {completedTests.map(test => (
                      <TestCard
                        key={test.uqt_id}
                        test={test}
                        isPending={false}
                        onViewResult={() => handleViewResult(test)}
                        isSelected={selectedCompleted.has(test.uqt_id)}
                        onSelect={handleSelectItem}
                        section="completed"
                      />
                    ))}
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </div>

    </div>
  );
};

export default Dashboard;

