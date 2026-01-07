import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { createQuiz, getExamplePrompts, trackPromptUsage, deletePromptsBulk } from '../services/api';
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
  const [selectedPrompts, setSelectedPrompts] = useState([]);

  useEffect(() => {
    const fetchPrompts = async () => {
      if (!user?.user_id) return;
      
      try {
        const fetchedPrompts = await getExamplePrompts(user.user_id);
        
        // Safety: Deduplicate and limit to 10 prompts (newest first)
        if (fetchedPrompts && Array.isArray(fetchedPrompts)) {
          const uniquePrompts = [];
          const seenTexts = new Set();
          
          for (const prompt of fetchedPrompts) {
            if (!seenTexts.has(prompt.prompt_text)) {
              seenTexts.add(prompt.prompt_text);
              uniquePrompts.push(prompt);
            }
          }
          
          // Limit to 10
          setPrompts(uniquePrompts.slice(0, 10));
        } else {
          setPrompts([]);
        }
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

  const handleSelectPrompt = (promptId) => {
    setSelectedPrompts(prev => 
      prev.includes(promptId) 
        ? prev.filter(id => id !== promptId)
        : [...prev, promptId]
    );
  };

  const handleDeleteSelected = async () => {
    if (selectedPrompts.length === 0) return;
    
    if (!window.confirm(`Delete ${selectedPrompts.length} selected prompt(s)?`)) {
      return;
    }

    try {
      await deletePromptsBulk(selectedPrompts, user.user_id);
      // Refresh prompts
      const fetchedPrompts = await getExamplePrompts(user.user_id);
      
      // Safety: Deduplicate and limit to 10
      if (fetchedPrompts && Array.isArray(fetchedPrompts)) {
        const uniquePrompts = [];
        const seenTexts = new Set();
        
        for (const prompt of fetchedPrompts) {
          if (!seenTexts.has(prompt.prompt_text)) {
            seenTexts.add(prompt.prompt_text);
            uniquePrompts.push(prompt);
          }
        }
        
        setPrompts(uniquePrompts.slice(0, 10));
      } else {
        setPrompts([]);
      }
      
      setSelectedPrompts([]);
    } catch (err) {
      alert('Failed to delete prompts. Please try again.');
    }
  };

  const truncateText = (text, maxLength = 120) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
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
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                  <p className="examples-title" style={{ margin: 0 }}>✨ Your recent prompts (max 10):</p>
                  {selectedPrompts.length > 0 && (
                    <button
                      type="button"
                      onClick={handleDeleteSelected}
                      className="delete-prompts-btn"
                      style={{
                        padding: '6px 12px',
                        fontSize: '12px',
                        backgroundColor: '#f44336',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontWeight: '500'
                      }}
                    >
                      🗑️ Delete ({selectedPrompts.length})
                    </button>
                  )}
                </div>
                <div className="prompts-list">
                  {prompts.map((prompt) => (
                    <div
                      key={prompt.prompt_id}
                      className="prompt-item"
                      style={{
                        display: 'flex',
                        alignItems: 'flex-start',
                        gap: '8px',
                        padding: '8px',
                        borderRadius: '6px',
                        backgroundColor: selectedPrompts.includes(prompt.prompt_id) ? '#f0f0f0' : 'transparent',
                        border: '1px solid #e0e0e0',
                        marginBottom: '6px',
                        transition: 'all 0.2s'
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={selectedPrompts.includes(prompt.prompt_id)}
                        onChange={() => handleSelectPrompt(prompt.prompt_id)}
                        onClick={(e) => e.stopPropagation()}
                        style={{ 
                          marginTop: '2px',
                          cursor: 'pointer',
                          flexShrink: 0
                        }}
                      />
                      <div
                        onClick={() => handlePromptClick(prompt.prompt_text, prompt.prompt_id)}
                        style={{
                          flex: 1,
                          cursor: 'pointer',
                          fontSize: '13px',
                          lineHeight: '1.4',
                          color: '#333'
                        }}
                        title={prompt.prompt_text}
                      >
                        {truncateText(prompt.prompt_text, 120)}
                      </div>
                    </div>
                  ))}
                </div>
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

