import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getQuiz, startTest, submitTest as submitTestAPI, getTestAnswers, saveAnswer, getHint } from '../services/api';
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
  const [hints, setHints] = useState({}); // Store hints per question_id
  const [loadingHint, setLoadingHint] = useState({}); // Track loading state per question
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [submitError, setSubmitError] = useState('');
  const [isPaletteOpen, setIsPaletteOpen] = useState(false);
  const [showSubmitModal, setShowSubmitModal] = useState(false);
  const [unansweredCount, setUnansweredCount] = useState(0);

  // Format difficulty label for display (short form)
  const formatDifficultyLabel = (difficulty) => {
    if (!difficulty) return 'Med';
    const normalized = difficulty.charAt(0).toUpperCase() + difficulty.slice(1).toLowerCase();
    return normalized === 'Medium' ? 'Med' : normalized;
  };

  useEffect(() => {
    // Reset state when quizId changes (e.g., when retaking)
    setQuiz(null);
    setUqtId(null);
    setCurrentQuestionIndex(0);
    setAnswers({});
    setHints({});
    setLoadingHint({});
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
      
      // CRITICAL: Start or resume the test first to get uqt_id
      // Backend ALWAYS checks for existing pending test (completed_time IS NULL) before creating new one
      // This prevents duplicate attempts from being created
      // If existing pending test found: Returns existing uqt_id
      // If NO existing pending test: Creates ONE new attempt and returns uqt_id
      const testData = await startTest(user.user_id, quizId, assignmentId);
      
      // CRITICAL: Store uqt_id immediately - this is the SINGLE attempt ID for this test session
      if (!testData || !testData.uqt_id) {
        throw new Error('Failed to start test: uqt_id not returned');
      }
      
      console.log(`[DEBUG] Test started/resumed: uqt_id=${testData.uqt_id}`);
      setUqtId(testData.uqt_id);
      
      // CRITICAL: Persist uqt_id to localStorage for reliability
      // Store both with quizId key (for recovery) and simple key (for submit)
      localStorage.setItem(`uqt_id_${quizId}`, testData.uqt_id.toString());
      localStorage.setItem("uqt_id", testData.uqt_id.toString());
      
      // Fetch quiz with shuffling for test integrity
      // Use uqt_id as seed for deterministic shuffling (consistent order per attempt)
      const quizData = await getQuiz(quizId, true, testData.uqt_id);
      setQuiz(quizData);
      
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

  const handleGetHint = async (questionId, questionText, options) => {
    // If hint already exists, don't fetch again
    if (hints[questionId]) {
      return;
    }

    try {
      setLoadingHint(prev => ({ ...prev, [questionId]: true }));
      
      const optionTexts = options.map(opt => opt.option_text);
      const hintData = await getHint(questionId, questionText, optionTexts);
      
      setHints(prev => ({
        ...prev,
        [questionId]: hintData.hint
      }));
    } catch (err) {
      console.error('Failed to get hint:', err);
      // Set a fallback hint if API fails
      setHints(prev => ({
        ...prev,
        [questionId]: 'Think carefully about the key concepts related to this question. Consider what you know about the topic and how it applies here.'
      }));
    } finally {
      setLoadingHint(prev => ({ ...prev, [questionId]: false }));
    }
  };

  const handleSubmit = async () => {
    // Check if all questions are answered
    const unansweredQuestions = quiz.questions.filter(
      q => !answers[q.question_id] || answers[q.question_id].length === 0
    );

    if (unansweredQuestions.length > 0) {
      // Show custom modal instead of browser confirm
      setUnansweredCount(unansweredQuestions.length);
      setShowSubmitModal(true);
      return;
    }

    // Proceed with submission
    await submitTest();
  };

  const submitTest = async () => {
    // Clear any previous submit errors
    setSubmitError('');
    setSubmitting(true);

    // Create AbortController for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 second timeout

    try {
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

      // CRITICAL: Use the SAME uqt_id that was set when test started
      // This ensures we're submitting to the correct attempt (not a duplicate)
      // Fallback to localStorage if state was lost
      let finalUqtId = uqtId;
      
      // Try simple key first, then quiz-specific key
      if (!finalUqtId) {
        const storedUqtId = localStorage.getItem("uqt_id");
        if (storedUqtId) {
          finalUqtId = parseInt(storedUqtId);
          console.log(`[DEBUG] Recovered uqt_id from localStorage (simple key): ${finalUqtId}`);
          setUqtId(finalUqtId);
        }
      }
      
      if (!finalUqtId && quiz) {
        const storedUqtId = localStorage.getItem(`uqt_id_${quiz.quiz_id}`);
        if (storedUqtId) {
          finalUqtId = parseInt(storedUqtId);
          console.log(`[DEBUG] Recovered uqt_id from localStorage (quiz key): ${finalUqtId}`);
          setUqtId(finalUqtId);
        }
      }
      
      // CRITICAL: Validate uqt_id exists before submission
      if (!finalUqtId || isNaN(finalUqtId)) {
        console.error('[ERROR] uqt_id is missing or invalid:', { uqtId, finalUqtId, quizId: quiz?.quiz_id });
        throw new Error('Test session ID is missing. Please start the test again.');
      }
      
      console.log(`[DEBUG] Using uqt_id for submission: ${finalUqtId}`);
      
      // MANDATORY: Include user_id and quiz_id for reliable submission
      const submitData = {
        uqt_id: finalUqtId,  // Optional - backend will use user_id + quiz_id if unreliable
        user_id: user.user_id,  // Required
        quiz_id: quiz.quiz_id,  // Required
        answers: formattedAnswers
      };

      console.log(`[DEBUG] Submitting test with uqt_id=${finalUqtId}, answers count=${formattedAnswers.length}`);
      
      // CRITICAL: Verify uqt_id is in submitData
      if (!submitData.uqt_id || submitData.uqt_id !== finalUqtId) {
        console.error('[ERROR] uqt_id mismatch in submitData:', { 
          submitDataUqtId: submitData.uqt_id, 
          finalUqtId 
        });
        throw new Error('Session ID mismatch. Please try again.');
      }
      
      // Call the renamed API function
      const result = await submitTestAPI(submitData);
      
      // Clear timeout on success
      clearTimeout(timeoutId);
      
      // CRITICAL: Navigate to results using the SAME uqt_id
      // Clear localStorage after successful submission
      localStorage.removeItem("uqt_id");
      if (quiz) {
        localStorage.removeItem(`uqt_id_${quiz.quiz_id}`);
      }
      
      console.log(`[DEBUG] Test submitted successfully, navigating to results`);
      console.log(`[DEBUG] Result data:`, { 
        uqt_id: result.uqt_id, 
        completed_time: result.completed_time,
        total_correct: result.total_correct,
        quiz_id: result.quiz_id
      });
      
      // CRITICAL: Navigate to results using quiz_id (backend will fetch latest completed attempt)
      navigate(`/results/${quiz.quiz_id}`);
    } catch (err) {
      clearTimeout(timeoutId);
      
      console.error('[ERROR] Failed to submit test:', err);
      
      // Handle different error types
      if (err.name === 'AbortError') {
        setSubmitError('Request timed out. Please check your connection and try again.');
      } else if (err.message) {
        setSubmitError(err.message);
      } else {
        setSubmitError('Failed to submit test. Please try again.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const goToQuestion = (index) => {
    setCurrentQuestionIndex(index);
  };

  const handleConfirmSubmit = async () => {
    setShowSubmitModal(false);
    await submitTest();
  };

  const handleCancelSubmit = () => {
    setShowSubmitModal(false);
  };

  // Handle ESC key press to close modal
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && showSubmitModal) {
        setShowSubmitModal(false);
      }
    };

    if (showSubmitModal) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [showSubmitModal]);

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
      {/* Submit Error Toast */}
      {submitError && (
        <div className="error-toast">
          <span>{submitError}</span>
          <button onClick={() => setSubmitError('')} className="error-toast-close">
            ✕
          </button>
        </div>
      )}

      <div className="test-header">
        <div className="test-info">
          <h1>{quiz.quiz_name}</h1>
          <p className="test-meta">
            <span>{quiz.questions.length} Questions</span>
            <span className={`difficulty ${quiz.difficulty_level.toLowerCase()}`}>
              {formatDifficultyLabel(quiz.difficulty_level)}
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
        <div className="palette-header">
          <span className="palette-title">Question Navigator</span>
          <button 
            className="palette-toggle"
            onClick={() => setIsPaletteOpen(!isPaletteOpen)}
            aria-label={isPaletteOpen ? "Collapse palette" : "Expand palette"}
          >
            {isPaletteOpen ? '▲' : '▼'}
          </button>
        </div>
        {isPaletteOpen && (
          <div className="palette-content">
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
        )}
      </div>

      <div className="question-card">
        <div className="question-header">
          <h2>Question {currentQuestionIndex + 1}</h2>
          <span className="question-type">
            {isMultiple ? '☑️ Multiple Choice' : '⭕ Single Choice'}
          </span>
        </div>
        
        <p className="question-text">{currentQuestion.question_text}</p>

        <div style={{ marginBottom: '15px', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            onClick={() => handleGetHint(
              currentQuestion.question_id,
              currentQuestion.question_text,
              currentQuestion.options
            )}
            disabled={loadingHint[currentQuestion.question_id] || !!hints[currentQuestion.question_id]}
            style={{
              padding: '8px 16px',
              backgroundColor: hints[currentQuestion.question_id] ? '#e0e0e0' : '#6C63FF',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: loadingHint[currentQuestion.question_id] || hints[currentQuestion.question_id] ? 'not-allowed' : 'pointer',
              fontSize: '14px',
              fontWeight: '500',
              opacity: loadingHint[currentQuestion.question_id] || hints[currentQuestion.question_id] ? 0.7 : 1,
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            {loadingHint[currentQuestion.question_id] ? (
              <>⏳ Loading...</>
            ) : hints[currentQuestion.question_id] ? (
              <>💡 Hint Used</>
            ) : (
              <>💡 Hint</>
            )}
          </button>
          {hints[currentQuestion.question_id] && (
            <span style={{ fontSize: '12px', color: '#6B7280', fontStyle: 'italic' }}>
              Hint displayed below
            </span>
          )}
        </div>

        {hints[currentQuestion.question_id] && (
          <div style={{
            marginBottom: '20px',
            padding: '12px 16px',
            backgroundColor: '#F6F8FF',
            border: '1px solid #E0E5FF',
            borderRadius: '8px',
            borderLeft: '4px solid #A78BFA'
          }}>
            <div style={{ fontSize: '12px', color: '#6B7280', fontWeight: '600', marginBottom: '6px' }}>
              💡 Hint:
            </div>
            <p style={{ margin: 0, fontSize: '14px', color: '#1F2937', lineHeight: '1.6' }}>
              {hints[currentQuestion.question_id]}
            </p>
          </div>
        )}

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

      {/* Submit Confirmation Modal */}
      {showSubmitModal && (
        <div className="modal-overlay" onClick={handleCancelSubmit}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <p style={{ fontSize: '15px', color: '#475569', margin: '0 0 24px 0', lineHeight: '1.5' }}>
              You have {unansweredCount} unanswered question(s). Do you want to submit anyway?
            </p>
            <div className="modal-actions">
              <button className="btn-cancel" onClick={handleCancelSubmit}>
                Go Back
              </button>
              <button className="btn-delete" onClick={handleConfirmSubmit}>
                Submit Anyway
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TakeTest;

