import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getQuiz, startTest, submitTest } from '../services/api';
import '../styles/TakeTest.css';

const TakeTest = () => {
  const { quizId } = useParams();
  const [searchParams] = useSearchParams();
  const assignmentId = searchParams.get('assignment');
  const { user } = useAuth();
  const navigate = useNavigate();

  const [quiz, setQuiz] = useState(null);
  const [uqtId, setUqtId] = useState(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadQuiz();
  }, [quizId]);

  const loadQuiz = async () => {
    try {
      setLoading(true);
      const quizData = await getQuiz(quizId);
      setQuiz(quizData);
      
      // Start the test
      const testData = await startTest(user.user_id, quizId, assignmentId);
      setUqtId(testData.uqt_id);
      
      // Initialize answers object
      const initialAnswers = {};
      quizData.questions.forEach(q => {
        initialAnswers[q.question_id] = [];
      });
      setAnswers(initialAnswers);
    } catch (err) {
      setError('Failed to load quiz. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerChange = (questionId, optionId, isMultiple) => {
    if (isMultiple) {
      // For CHECKLIST questions (multiple answers)
      setAnswers(prev => {
        const currentAnswers = prev[questionId] || [];
        if (currentAnswers.includes(optionId)) {
          return {
            ...prev,
            [questionId]: currentAnswers.filter(id => id !== optionId)
          };
        } else {
          return {
            ...prev,
            [questionId]: [...currentAnswers, optionId]
          };
        }
      });
    } else {
      // For RADIO questions (single answer)
      setAnswers(prev => ({
        ...prev,
        [questionId]: [optionId]
      }));
    }
  };

  const handleSubmit = async () => {
    // Check if all questions are answered
    const unansweredQuestions = quiz.questions.filter(
      q => !answers[q.question_id] || answers[q.question_id].length === 0
    );

    if (unansweredQuestions.length > 0) {
      const confirm = window.confirm(
        `You have ${unansweredQuestions.length} unanswered question(s). Do you want to submit anyway?`
      );
      if (!confirm) return;
    }

    try {
      setSubmitting(true);
      
      // Format answers for API
      const formattedAnswers = [];
      Object.keys(answers).forEach(questionId => {
        answers[questionId].forEach(optionId => {
          formattedAnswers.push({
            question_id: parseInt(questionId),
            question_option_id: optionId
          });
        });
      });

      const submitData = {
        uqt_id: uqtId,
        answers: formattedAnswers
      };

      const result = await submitTest(submitData);
      navigate(`/results/${uqtId}`);
    } catch (err) {
      setError('Failed to submit test. Please try again.');
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  const goToQuestion = (index) => {
    setCurrentQuestionIndex(index);
  };

  const nextQuestion = () => {
    if (currentQuestionIndex < quiz.questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    }
  };

  const previousQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading quiz...</p>
      </div>
    );
  }

  if (error || !quiz) {
    return (
      <div className="error-container">
        <p>{error || 'Quiz not found'}</p>
        <button onClick={() => navigate('/')}>Go Back</button>
      </div>
    );
  }

  const currentQuestion = quiz.questions[currentQuestionIndex];
  const isMultiple = currentQuestion.question_type === 'CHECKLIST';
  const currentAnswers = answers[currentQuestion.question_id] || [];

  return (
    <div className="take-test-container">
      <div className="test-header">
        <div className="test-info">
          <h1>{quiz.quiz_name}</h1>
          <p className="test-meta">
            <span>{quiz.questions.length} Questions</span>
            <span className={`difficulty ${quiz.difficulty_level.toLowerCase()}`}>
              {quiz.difficulty_level}
            </span>
          </p>
        </div>
      </div>

      <div className="test-progress">
        <div className="progress-bar">
          <div 
            className="progress-fill" 
            style={{ width: `${((currentQuestionIndex + 1) / quiz.questions.length) * 100}%` }}
          />
        </div>
        <p className="progress-text">
          Question {currentQuestionIndex + 1} of {quiz.questions.length}
        </p>
      </div>

      <div className="question-indicators">
        {quiz.questions.map((q, index) => (
          <button
            key={q.question_id}
            className={`indicator ${index === currentQuestionIndex ? 'active' : ''} ${
              answers[q.question_id] && answers[q.question_id].length > 0 ? 'answered' : ''
            }`}
            onClick={() => goToQuestion(index)}
          >
            {index + 1}
          </button>
        ))}
      </div>

      <div className="question-card">
        <div className="question-header">
          <h2>Question {currentQuestionIndex + 1}</h2>
          <span className="question-type">
            {isMultiple ? '☑️ Multiple Choice' : '⭕ Single Choice'}
          </span>
        </div>
        
        <p className="question-text">{currentQuestion.question_text}</p>

        <div className="options-container">
          {currentQuestion.options.map(option => (
            <label
              key={option.question_option_id}
              className={`option-label ${
                currentAnswers.includes(option.question_option_id) ? 'selected' : ''
              }`}
            >
              <input
                type={isMultiple ? 'checkbox' : 'radio'}
                name={`question-${currentQuestion.question_id}`}
                value={option.question_option_id}
                checked={currentAnswers.includes(option.question_option_id)}
                onChange={() => handleAnswerChange(
                  currentQuestion.question_id,
                  option.question_option_id,
                  isMultiple
                )}
              />
              <span className="option-text">{option.option_text}</span>
            </label>
          ))}
        </div>
      </div>

      <div className="navigation-buttons">
        <button
          onClick={previousQuestion}
          disabled={currentQuestionIndex === 0}
          className="nav-btn prev-btn"
        >
          ← Previous
        </button>

        {currentQuestionIndex === quiz.questions.length - 1 ? (
          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="submit-test-btn"
          >
            {submitting ? 'Submitting...' : '✓ Submit Test'}
          </button>
        ) : (
          <button
            onClick={nextQuestion}
            className="nav-btn next-btn"
          >
            Next →
          </button>
        )}
      </div>
    </div>
  );
};

export default TakeTest;

