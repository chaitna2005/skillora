import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import { createQuiz } from '../api/api';

function CreateQuiz({ user, onLogout }) {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    prompt: '',
    difficulty_level: 'MEDIUM',
    total_no_questions: 10,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const quiz = await createQuiz(user.user_id, formData);
      alert('Quiz created successfully!');
      navigate(`/quiz/${quiz.quiz_id}`);
    } catch (err) {
      setError(err.message || 'Failed to create quiz. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-layout">
      <Sidebar user={user} onLogout={onLogout} />
      
      <div className="main-content">
        <div className="create-quiz-container">
          <h1>Create New Quiz</h1>
          <p className="subtitle">AI will generate questions based on your prompt</p>

          {error && <div className="error-message">{error}</div>}

          <form onSubmit={handleSubmit} className="quiz-form">
            <div className="form-group">
              <label>What do you want to be tested on?</label>
              <textarea
                name="prompt"
                value={formData.prompt}
                onChange={handleChange}
                required
                rows="5"
                placeholder="Example: I completed 10th grade social studies about World War II. Test my knowledge with questions about the major events, leaders, and outcomes."
              />
              <small>Be specific about the topic and what you want to learn.</small>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Difficulty Level</label>
                <select
                  name="difficulty_level"
                  value={formData.difficulty_level}
                  onChange={handleChange}
                >
                  <option value="EASY">Easy</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="HARD">Hard</option>
                </select>
              </div>

              <div className="form-group">
                <label>Number of Questions</label>
                <input
                  type="number"
                  name="total_no_questions"
                  value={formData.total_no_questions}
                  onChange={handleChange}
                  min="5"
                  max="50"
                  required
                />
              </div>
            </div>

            <div className="form-actions">
              <button
                type="button"
                className="btn-secondary"
                onClick={() => navigate('/home')}
                disabled={loading}
              >
                Cancel
              </button>
              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? 'Creating Quiz...' : 'Create Quiz'}
              </button>
            </div>
          </form>

          <div className="prompt-examples">
            <h3>Example Prompts:</h3>
            <ul>
              <li>"Test me on Indian rivers and the states they flow through"</li>
              <li>"I am an engineering student. I learned about LLM concepts. Test my knowledge"</li>
              <li>"Give me infix to postfix conversion problems for 5th grade level"</li>
              <li>"Test my knowledge on states and capitals of India"</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default CreateQuiz;

