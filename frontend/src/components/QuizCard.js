import React from 'react';
import { useNavigate } from 'react-router-dom';

function QuizCard({ quiz }) {
  const navigate = useNavigate();

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const getDifficultyColor = (level) => {
    switch (level) {
      case 'EASY':
        return '#4caf50';
      case 'MEDIUM':
        return '#ff9800';
      case 'HARD':
        return '#f44336';
      default:
        return '#666';
    }
  };

  return (
    <div className="quiz-card" onClick={() => navigate(`/quiz/${quiz.quiz_id}`)}>
      <div className="quiz-card-header">
        <h3>{quiz.quiz_name}</h3>
        <span
          className="difficulty-badge"
          style={{ backgroundColor: getDifficultyColor(quiz.difficulty_level) }}
        >
          {quiz.difficulty_level}
        </span>
      </div>
      <p className="quiz-prompt">{quiz.prompt}</p>
      <div className="quiz-card-footer">
        <span>📝 {quiz.total_no_questions} questions</span>
        <span>📅 {formatDate(quiz.created_date)}</span>
      </div>
    </div>
  );
}

export default QuizCard;

