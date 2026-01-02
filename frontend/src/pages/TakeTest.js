import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getQuiz, startTest, submitTest, getTestAnswers, saveAnswer } from '../services/api';
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
    // Reset state when quizId changes (e.g., when retaking)
    setQuiz(null);
    setUqtId(null);
    setCurrentQuestionIndex(0);
    setAnswers({});
    setError('');
    setSubmitting(false);
    loadQuiz();
  }, [quizId]);

  // Auto-save answers when they change (with debounce)
  useEffect(() => {
    if (!uqtId || !quiz || Object.keys(answers).length === 0) {
      return;
    }

    // Debounce: save answers 1 second after user stops changing them
    const timeoutId = setTimeout(() => {
      // Save current question's answer automatically
      const currentQuestion = quiz.questions[currentQuestionIndex];
      if (currentQuestion) {
        const currentAnswers = answers[currentQuestion.question_id] || [];
        if (currentAnswers.length > 0) {
          saveAnswer(uqtId, currentQuestion.question_id, currentAnswers.map(id => parseInt(id)))
            .catch(err => {
              // Silently fail - answers will be saved on navigation or submit
              console.error('Auto-save failed:', err);
            });
        }
      }
    }, 1000); // 1 second debounce

    return () => clearTimeout(timeoutId);
  }, [answers, uqtId, quiz, currentQuestionIndex]);

  // Save answers when component unmounts (user navigates away)
  useEffect(() => {
    return () => {
      // Cleanup: save current answer when component unmounts
      if (uqtId && quiz && !submitting) {
        const currentQuestion = quiz.questions[currentQuestionIndex];
        if (currentQuestion) {
          const currentAnswers = answers[currentQuestion.question_id] || [];
          if (currentAnswers.length > 0) {
            // Use sendBeacon for reliability during navigation
            const answerData = JSON.stringify({
              question_id: currentQuestion.question_id,
              question_option_ids: currentAnswers.map(id => parseInt(id))
            });
            
            // Try to save synchronously using fetch with keepalive
            fetch(`/api/test/save-answer/${uqtId}`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: answerData,
              keepalive: true
            }).catch(() => {
              // Ignore errors - answers are already saved on navigation
            });
          }
        }
      }
    };
  }, [uqtId, quiz, answers, currentQuestionIndex, submitting]);

  const loadQuiz = async () => {
    try {
      setLoading(true);
      setError('');
      const quizData = await getQuiz(quizId);
      setQuiz(quizData);
      
      // Start or resume the test
      // CRITICAL: Backend behavior:
      // - If assignmentId exists (Pending Tests): Resumes existing test if available
      // - If assignmentId is NULL (My Quizzes): ALWAYS creates new test, never resumes
      const testData = await startTest(user.user_id, quizId, assignmentId);
      setUqtId(testData.uqt_id);
      
      // Initialize answers object
      const initialAnswers = {};
      quizData.questions.forEach(q => {
        initialAnswers[q.question_id] = [];
      });
      
      // CRITICAL: Load existing answers ONLY when coming from Pending Tests (assignmentId exists)
      // My Quizzes (assignmentId is NULL) must NEVER load existing answers - always start fresh
      // This enforces strict separation: My Quizzes = START, Pending Tests = CONTINUE
      if (assignmentId) {
        // Coming from Pending Tests - check if test is IN_PROGRESS and load saved answers
        const testStatus = testData.status || (testData.start_time && !testData.completed_time ? 'IN_PROGRESS' : 'NOT_STARTED');
        
        if (testStatus === 'IN_PROGRESS') {
          try {
            const existingAnswers = await getTestAnswers(testData.uqt_id);
            if (existingAnswers && existingAnswers.answers) {
              // Merge existing answers into initial answers
              Object.keys(existingAnswers.answers).forEach(questionId => {
                const questionIdInt = parseInt(questionId);
                if (existingAnswers.answers[questionId] && existingAnswers.answers[questionId].length > 0) {
                  initialAnswers[questionIdInt] = existingAnswers.answers[questionId].map(id => parseInt(id));
                }
              });
            }
          } catch (err) {
            // If no existing answers, that's fine - start fresh
          }
        }
      }
      // If assignmentId is NULL (My Quizzes), always start with empty answers - no continuation
      
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
      
      // Save current question's answer before submitting (if on a question with answers)
      if (uqtId && quiz) {
        const currentQuestion = quiz.questions[currentQuestionIndex];
        const currentAnswers = answers[currentQuestion.question_id] || [];
        
        if (currentAnswers.length > 0) {
          try {
            await saveAnswer(uqtId, currentQuestion.question_id, currentAnswers.map(id => parseInt(id)));
          } catch (err) {
            console.error('Failed to save current answer before submit:', err);
            // Continue with submission even if save fails
          }
        }
      }
      
      // Format answers for API - group by question_id with question_option_ids array
      const formattedAnswers = [];
      Object.keys(answers).forEach(questionId => {
        if (answers[questionId] && answers[questionId].length > 0) {
          formattedAnswers.push({
            question_id: parseInt(questionId),
            question_option_ids: answers[questionId].map(id => parseInt(id))
          });
        }
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

  const nextQuestion = async () => {
    // Save current question's answer before moving to next
    if (uqtId && quiz) {
      const currentQuestion = quiz.questions[currentQuestionIndex];
      const currentAnswers = answers[currentQuestion.question_id] || [];
      
      if (currentAnswers.length > 0) {
        try {
          await saveAnswer(uqtId, currentQuestion.question_id, currentAnswers.map(id => parseInt(id)));
          console.log(`Saved answer for question ${currentQuestion.question_id}`);
        } catch (err) {
          console.error('Failed to save answer:', err);
          // Don't block navigation if save fails - user can still continue
        }
      }
    }
    
    // Move to next question
    if (currentQuestionIndex < quiz.questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    }
  };

  const previousQuestion = async () => {
    // Save current question's answer before moving to previous
    if (uqtId && quiz) {
      const currentQuestion = quiz.questions[currentQuestionIndex];
      const currentAnswers = answers[currentQuestion.question_id] || [];
      
      if (currentAnswers.length > 0) {
        try {
          await saveAnswer(uqtId, currentQuestion.question_id, currentAnswers.map(id => parseInt(id)));
        } catch (err) {
          // Don't block navigation if save fails
        }
      }
    }
    
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
          {currentQuestion.options.map((option, index) => (
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
              <span className="option-number">{index + 1}.</span>
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

