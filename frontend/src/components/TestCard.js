import React from 'react';
import { useNavigate } from 'react-router-dom';

function TestCard({ test, type = 'completed' }) {
  const navigate = useNavigate();

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getResultColor = (result) => {
    switch (result) {
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

  const handleClick = () => {
    if (type === 'completed') {
      navigate(`/test-result/${test.uqt_id}`);
    } else if (type === 'pending') {
      navigate(`/take-test/${test.quiz_id}?uqt_id=${test.uqt_id}`);
    }
  };

  return (
    <div className="test-card" onClick={handleClick}>
      <div className="test-card-header">
        <h4>{test.quiz_name}</h4>
        {test.result && (
          <span
            className="result-badge"
            style={{ backgroundColor: getResultColor(test.result) }}
          >
            {test.result.replace('_', ' ')}
          </span>
        )}
      </div>
      <div className="test-card-body">
        {type === 'completed' ? (
          <>
            <p className="test-score">
              Score: {test.total_correct}/{test.total_no_questions || test.total_questions} (
              {Math.round((test.total_correct / (test.total_no_questions || test.total_questions)) * 100)}%)
            </p>
            <p className="test-date">Completed: {formatDate(test.completed_time)}</p>
          </>
        ) : (
          <p className="test-date">Started: {formatDate(test.start_time)}</p>
        )}
      </div>
      <div className="test-card-footer">
        <button className="btn-secondary">
          {type === 'completed' ? 'View Results' : 'Resume Test'}
        </button>
      </div>
    </div>
  );
}

export default TestCard;

