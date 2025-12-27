import React, { useState, useEffect } from 'react';
import Sidebar from '../components/Sidebar';
import QuizCard from '../components/QuizCard';
import TestCard from '../components/TestCard';
import { getUserQuizzes, getAssignedQuizzes, getTestSummary, getPendingTests, getCompletedTests } from '../api/api';

function Home({ user, onLogout }) {
  const [activeTab, setActiveTab] = useState('overview');
  const [quizzes, setQuizzes] = useState([]);
  const [assignedQuizzes, setAssignedQuizzes] = useState([]);
  const [pendingTests, setPendingTests] = useState([]);
  const [completedTests, setCompletedTests] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [user.user_id]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [quizzesData, assignedData, summaryData, pendingData, completedData] = await Promise.all([
        getUserQuizzes(user.user_id),
        getAssignedQuizzes(user.user_id),
        getTestSummary(user.user_id),
        getPendingTests(user.user_id),
        getCompletedTests(user.user_id),
      ]);

      setQuizzes(quizzesData);
      setAssignedQuizzes(assignedData);
      setSummary(summaryData);
      setPendingTests(pendingData);
      setCompletedTests(completedData);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const renderOverview = () => (
    <div className="overview-section">
      <h2>Welcome back, {user.first_name}!</h2>
      
      <div className="stats-grid">
        <div className="stat-card">
          <h3>{summary?.total_tests_taken || 0}</h3>
          <p>Total Tests</p>
        </div>
        <div className="stat-card">
          <h3>{summary?.total_tests_completed || 0}</h3>
          <p>Completed</p>
        </div>
        <div className="stat-card">
          <h3>{summary?.total_tests_pending || 0}</h3>
          <p>Pending</p>
        </div>
        <div className="stat-card">
          <h3>{summary?.average_score ? Math.round(summary.average_score) + '%' : 'N/A'}</h3>
          <p>Average Score</p>
        </div>
      </div>

      {pendingTests.length > 0 && (
        <div className="section">
          <h3>Pending Tests</h3>
          <div className="tests-grid">
            {pendingTests.map((test) => (
              <TestCard key={test.uqt_id} test={test} type="pending" />
            ))}
          </div>
        </div>
      )}

      {assignedQuizzes.length > 0 && (
        <div className="section">
          <h3>Assigned Quizzes</h3>
          <div className="assigned-quizzes">
            {assignedQuizzes.map((quiz) => (
              <QuizCard key={quiz.quiz_id} quiz={quiz} />
            ))}
          </div>
        </div>
      )}

      {summary?.recent_tests && summary.recent_tests.length > 0 && (
        <div className="section">
          <h3>Recent Tests</h3>
          <div className="tests-grid">
            {summary.recent_tests.map((test) => (
              <TestCard 
                key={test.uqt_id} 
                test={test} 
                type={test.completed_time ? 'completed' : 'pending'} 
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );

  const renderMyQuizzes = () => (
    <div className="quizzes-section">
      <h2>My Quizzes</h2>
      {quizzes.length === 0 ? (
        <p>No quizzes created yet. Create your first quiz!</p>
      ) : (
        <div className="quizzes-grid">
          {quizzes.map((quiz) => (
            <QuizCard key={quiz.quiz_id} quiz={quiz} />
          ))}
        </div>
      )}
    </div>
  );

  const renderPendingTests = () => (
    <div className="tests-section">
      <h2>Pending Tests</h2>
      {pendingTests.length === 0 ? (
        <p>No pending tests. All caught up!</p>
      ) : (
        <div className="tests-grid">
          {pendingTests.map((test) => (
            <TestCard key={test.uqt_id} test={test} type="pending" />
          ))}
        </div>
      )}
    </div>
  );

  const renderCompletedTests = () => (
    <div className="tests-section">
      <h2>Completed Tests</h2>
      {completedTests.length === 0 ? (
        <p>No completed tests yet.</p>
      ) : (
        <div className="tests-grid">
          {completedTests.map((test) => (
            <TestCard key={test.uqt_id} test={test} type="completed" />
          ))}
        </div>
      )}
    </div>
  );

  return (
    <div className="app-layout">
      <Sidebar user={user} onLogout={onLogout} />
      
      <div className="main-content">
        <div className="tabs">
          <button
            className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            Overview
          </button>
          <button
            className={`tab ${activeTab === 'quizzes' ? 'active' : ''}`}
            onClick={() => setActiveTab('quizzes')}
          >
            My Quizzes
          </button>
          <button
            className={`tab ${activeTab === 'pending' ? 'active' : ''}`}
            onClick={() => setActiveTab('pending')}
          >
            Pending
          </button>
          <button
            className={`tab ${activeTab === 'completed' ? 'active' : ''}`}
            onClick={() => setActiveTab('completed')}
          >
            Completed
          </button>
        </div>

        <div className="content-area">
          {loading ? (
            <div className="loading">Loading...</div>
          ) : (
            <>
              {activeTab === 'overview' && renderOverview()}
              {activeTab === 'quizzes' && renderMyQuizzes()}
              {activeTab === 'pending' && renderPendingTests()}
              {activeTab === 'completed' && renderCompletedTests()}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default Home;

