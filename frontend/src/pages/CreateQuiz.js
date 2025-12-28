import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { createQuiz } from '../services/api';
import '../styles/CreateQuiz.css';

const CreateQuiz = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    quiz_name: '',
    prompt: '',
    total_no_questions: 5,
    difficulty_level: 'MEDIUM'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const quiz = await createQuiz(user.user_id, formData);
      alert('Quiz created successfully! 🎉');
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create quiz. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const examplePrompts = [
    "Test me on World War II history",
    "Create questions about Python programming",
    "Quiz me on Indian geography and states",
    "Generate questions about Machine Learning basics",
    "Test my knowledge of React.js hooks"
  ];

  return (
    <div className="create-quiz-container">
      <div className="create-quiz-card">
        <div className="page-header">
          <h1>✨ Create New Quiz</h1>
          <p>Let AI generate custom questions for you</p>
        </div>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit} className="create-quiz-form">
          <div className="form-group">
            <label htmlFor="quiz_name">
              Quiz Name <span className="required">*</span>
            </label>
            <input
              type="text"
              id="quiz_name"
              name="quiz_name"
              value={formData.quiz_name}
              onChange={handleChange}
              placeholder="e.g., History Quiz, Python Basics"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="prompt">
              Quiz Prompt <span className="required">*</span>
            </label>
            <textarea
              id="prompt"
              name="prompt"
              value={formData.prompt}
              onChange={handleChange}
              placeholder="Describe what you want to be tested on..."
              rows="4"
              required
            />
            <div className="examples">
              <p className="examples-title">💡 Example prompts:</p>
              <ul>
                {examplePrompts.map((example, index) => (
                  <li
                    key={index}
                    onClick={() => setFormData({ ...formData, prompt: example })}
                    className="example-item"
                  >
                    {example}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="total_no_questions">
                Number of Questions <span className="required">*</span>
              </label>
              <select
                id="total_no_questions"
                name="total_no_questions"
                value={formData.total_no_questions}
                onChange={handleChange}
                required
              >
                <option value="5">5 Questions</option>
                <option value="10">10 Questions</option>
                <option value="15">15 Questions</option>
                <option value="20">20 Questions</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="difficulty_level">
                Difficulty Level <span className="required">*</span>
              </label>
              <select
                id="difficulty_level"
                name="difficulty_level"
                value={formData.difficulty_level}
                onChange={handleChange}
                required
              >
                <option value="EASY">Easy</option>
                <option value="MEDIUM">Medium</option>
                <option value="HARD">Hard</option>
              </select>
            </div>
          </div>

          <div className="form-actions">
            <button
              type="button"
              onClick={() => navigate('/')}
              className="cancel-btn"
              disabled={loading}
            >
              Cancel
            </button>
            <button type="submit" className="submit-btn" disabled={loading}>
              {loading ? (
                <>
                  <span className="spinner-small"></span>
                  Generating Quiz...
                </>
              ) : (
                <>
                  ✨ Create Quiz
                </>
              )}
            </button>
          </div>
        </form>

        {loading && (
          <div className="loading-info">
            <p>⏳ AI is generating your questions... This may take a moment.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default CreateQuiz;

