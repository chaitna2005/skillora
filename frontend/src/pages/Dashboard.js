import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getUserQuizzes, getAssignedQuizzes, getPendingTests, getCompletedTests } from '../services/api';
import '../styles/Dashboard.css';

const Dashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [myQuizzes, setMyQuizzes] = useState([]);
  const [assignedQuizzes, setAssignedQuizzes] = useState([]);
  const [pendingTests, setPendingTests] = useState([]);
  const [completedTests, setCompletedTests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('myQuizzes');

  useEffect(() => {
    loadData();
  }, [user]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [quizzes, assigned, pending, completed] = await Promise.all([
        getUserQuizzes(user.user_id),
        getAssignedQuizzes(user.user_id),
        getPendingTests(user.user_id),
        getCompletedTests(user.user_id)
      ]);
      
      setMyQuizzes(quizzes);
      setAssignedQuizzes(assigned);
      setPendingTests(pending);
      setCompletedTests(completed);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTakeTest = (quizId, assignmentId = null) => {
    navigate(`/take-test/${quizId}${assignmentId ? `?assignment=${assignmentId}` : ''}`);
  };

  const handleViewResult = (uqtId) => {
    navigate(`/results/${uqtId}`);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const QuizCard = ({ quiz, onTakeTest, showTakeButton = true }) => (
    <div className="quiz-card">
      <div className="quiz-card-header">
        <h3>{quiz.quiz_name}</h3>
        <span className={`difficulty-badge ${quiz.difficulty_level.toLowerCase()}`}>
          {quiz.difficulty_level}
        </span>
      </div>
      <p className="quiz-prompt">{quiz.prompt}</p>
      <div className="quiz-card-footer">
        <div className="quiz-info">
          <span>📝 {quiz.total_no_questions} questions</span>
          <span>📅 {formatDate(quiz.created_date)}</span>
        </div>
        {showTakeButton && (
          <button onClick={onTakeTest} className="take-test-btn">
            Take Test
          </button>
        )}
      </div>
    </div>
  );

  const TestCard = ({ test, onViewResult, isPending }) => (
    <div className="test-card">
      <div className="test-card-header">
        <h3>{test.quiz_name}</h3>
        {!isPending && (
          <span className={`score-badge ${test.result >= 70 ? 'pass' : 'fail'}`}>
            {test.result}%
          </span>
        )}
      </div>
      <div className="test-card-body">
        {isPending ? (
          <>
            <p className="test-status pending">⏳ Pending</p>
            {test.due_date && (
              <p className="due-date">Due: {formatDate(test.due_date)}</p>
            )}
          </>
        ) : (
          <>
            <p className="test-score">Score: {test.total_correct}/{test.total_questions}</p>
            <p className="test-date">Completed: {formatDate(test.completed_time)}</p>
          </>
        )}
      </div>
      <button onClick={onViewResult} className="view-btn">
        {isPending ? 'Take Test' : 'View Results'}
      </button>
    </div>
  );

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading your dashboard...</p>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
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

        <div className="tab-content">
          {activeTab === 'myQuizzes' && (
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
                  />
                ))
              )}
            </div>
          )}

          {activeTab === 'assigned' && (
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
                  />
                ))
              )}
            </div>
          )}

          {activeTab === 'pending' && (
            <div className="test-grid">
              {pendingTests.length === 0 ? (
                <div className="empty-state">
                  <p>⏳ No pending tests.</p>
                </div>
              ) : (
                pendingTests.map(test => (
                  <TestCard
                    key={test.quiz_id}
                    test={test}
                    isPending={true}
                    onViewResult={() => handleTakeTest(test.quiz_id, test.quiz_assignment_id)}
                  />
                ))
              )}
            </div>
          )}

          {activeTab === 'completed' && (
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
                    onViewResult={() => handleViewResult(test.uqt_id)}
                  />
                ))
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

