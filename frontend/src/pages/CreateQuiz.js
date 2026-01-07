import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { createQuiz, getExamplePrompts, trackPromptUsage } from '../services/api';
import '../styles/CreateQuiz.css';

const CreateQuiz = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    prompt: '',
    total_no_questions: 5,
    difficulty_level: 'MEDIUM'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [prompts, setPrompts] = useState([]);

  useEffect(() => {
    const fetchPrompts = async () => {
      if (!user?.user_id) return;
      
      try {
        const fetchedPrompts = await getExamplePrompts(user.user_id);
        setPrompts(fetchedPrompts || []);
      } catch (err) {
        // Silently fail - no prompts will be shown
        setPrompts([]);
      }
    };
    fetchPrompts();
  }, [user]);

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

  const handlePromptClick = async (promptText, promptId = null) => {
    setFormData({ ...formData, prompt: promptText });
    if (promptId) {
      try {
        await trackPromptUsage(promptId);
      } catch (err) {
        // Silently fail - prompt is still set
      }
    }
  };

  return (
    <div className="create-quiz-container">
      <div className="create-quiz-card">
        <div className="page-header">
          <h1>🤖 Create Your AI-Powered Quiz</h1>
          <p>Let our intelligent AI craft a personalized quiz tailored to your needs</p>
        </div>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit} className="create-quiz-form">
          <div className="form-group">
            <label htmlFor="prompt">
              Quiz Prompt <span className="required">*</span>
            </label>
            <textarea
              id="prompt"
              name="prompt"
              value={formData.prompt}
              onChange={handleChange}
              placeholder="Tell us what you'd like to learn or test. Be specific for the best results! For example: 'Create a quiz about JavaScript async/await concepts with practical coding scenarios'"
              rows="5"
              required
            />
            <p className="helper-text">💡 Tip: More detailed prompts help our AI generate higher-quality, more relevant questions for you.</p>
            {prompts.length > 0 && (
              <div className="examples">
                <p className="examples-title">✨ Try these example prompts:</p>
                <ul>
                  {prompts.map((prompt) => (
                    <li
                      key={prompt.prompt_id}
                      onClick={() => handlePromptClick(prompt.prompt_text, prompt.prompt_id)}
                      className="example-item"
                    >
                      {prompt.prompt_text}
                    </li>
                  ))}
                </ul>
              </div>
            )}
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
                  AI is Generating Your Quiz...
                </>
              ) : (
                <>
                  🚀 Generate Quiz with AI
                </>
              )}
            </button>
          </div>
        </form>

        {loading && (
          <div className="loading-info">
            <p>✨ Our AI is crafting your personalized quiz... This may take a moment.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default CreateQuiz;

