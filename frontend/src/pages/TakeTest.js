import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import { getQuiz, startTest, submitTest } from '../api/api';

function TakeTest({ user, onLogout }) {
  const { quizId } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const existingUqtId = searchParams.get('uqt_id');

  const [quiz, setQuiz] = useState(null);
  const [uqtId, setUqtId] = useState(existingUqtId);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadQuiz();
  }, [quizId]);

  const loadQuiz = async () => {
    setLoading(true);
    try {
      const quizData = await getQuiz(quizId);
      setQuiz(quizData);

      // If no existing test, start a new one
      if (!existingUqtId) {
        const testData = { quiz_id: parseInt(quizId) };
        const test = await startTest(user.user_id, testData);
        setUqtId(test.uqt_id);
      }
    } catch (error) {
      console.error('Error loading quiz:', error);
      alert('Failed to load quiz');
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerChange = (questionId, optionId, isChecklist) => {
    if (isChecklist) {
      // For checklist, toggle the option
      const currentAnswers = answers[questionId] || [];
      const newAnswers = currentAnswers.includes(optionId)
        ? currentAnswers.filter(id => id !== optionId)
        : [...currentAnswers, optionId];
      
      setAnswers({
        ...answers,
        [questionId]: newAnswers,
      });
    } else {
      // For radio, replace with single option
      setAnswers({
        ...answers,
        [questionId]: [optionId],
      });
    }
  };

  const handleNext = () => {
    if (currentQuestionIndex < quiz.questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    }
  };

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
    }
  };

  const handleSubmit = async () => {
    // Check if all questions are answered
    const unanswered = quiz.questions.filter(q => !answers[q.question_id] || answers[q.question_id].length === 0);
    
    if (unanswered.length > 0) {
      const confirmSubmit = window.confirm(
        `You have ${unanswered.length} unanswered question(s). Submit anyway?`
      );
      if (!confirmSubmit) return;
    }

    setSubmitting(true);
    try {
      const submissionData = {
        uqt_id: parseInt(uqtId),
        answers: quiz.questions.map(q => ({
          question_id: q.question_id,
          question_option_ids: answers[q.question_id] || [],
        })),
      };

      const result = await submitTest(submissionData);
      navigate(`/test-result/${result.uqt_id}`);
    } catch (error) {
      console.error('Error submitting test:', error);
      alert('Failed to submit test. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="app-layout">
        <Sidebar user={user} onLogout={onLogout} />
        <div className="main-content">
          <div className="loading">Loading test...</div>
        </div>
      </div>
    );
  }

  if (!quiz || !quiz.questions) {
    return (
      <div className="app-layout">
        <Sidebar user={user} onLogout={onLogout} />
        <div className="main-content">
          <div className="error-message">Test not found</div>
        </div>
      </div>
    );
  }

  const currentQuestion = quiz.questions[currentQuestionIndex];
  const isChecklist = currentQuestion.question_type === 'CHECKLIST';
  const selectedAnswers = answers[currentQuestion.question_id] || [];

  return (
    <div className="app-layout">
      <Sidebar user={user} onLogout={onLogout} />
      
      <div className="main-content">
        <div className="test-container">
          <div className="test-header">
            <h1>{quiz.quiz_name}</h1>
            <div className="progress">
              Question {currentQuestionIndex + 1} of {quiz.questions.length}
            </div>
          </div>

          <div className="question-card">
            <div className="question-header">
              <h2>Question {currentQuestionIndex + 1}</h2>
              <span className="question-type-badge">
                {isChecklist ? 'Multiple Answers' : 'Single Answer'}
              </span>
            </div>

            <p className="question-text">{currentQuestion.question_text}</p>

            <div className="options-list">
              {currentQuestion.options.map((option) => (
                <label
                  key={option.question_option_id}
                  className={`option-item ${
                    selectedAnswers.includes(option.question_option_id) ? 'selected' : ''
                  }`}
                >
                  <input
                    type={isChecklist ? 'checkbox' : 'radio'}
                    name={`question-${currentQuestion.question_id}`}
                    checked={selectedAnswers.includes(option.question_option_id)}
                    onChange={() =>
                      handleAnswerChange(
                        currentQuestion.question_id,
                        option.question_option_id,
                        isChecklist
                      )
                    }
                  />
                  <span>{option.option_text}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="test-navigation">
            <button
              className="btn-secondary"
              onClick={handlePrevious}
              disabled={currentQuestionIndex === 0}
            >
              ← Previous
            </button>

            <div className="question-indicators">
              {quiz.questions.map((_, index) => (
                <button
                  key={index}
                  className={`indicator ${
                    index === currentQuestionIndex ? 'active' : ''
                  } ${answers[quiz.questions[index].question_id]?.length > 0 ? 'answered' : ''}`}
                  onClick={() => setCurrentQuestionIndex(index)}
                >
                  {index + 1}
                </button>
              ))}
            </div>

            {currentQuestionIndex === quiz.questions.length - 1 ? (
              <button
                className="btn-primary"
                onClick={handleSubmit}
                disabled={submitting}
              >
                {submitting ? 'Submitting...' : 'Submit Test'}
              </button>
            ) : (
              <button className="btn-primary" onClick={handleNext}>
                Next →
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default TakeTest;

