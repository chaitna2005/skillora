import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { loginUser } from '../services/api';
import '../styles/Auth.css';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await loginUser(username, password);
      
      // Check if login was successful
      if (!response.success) {
        setError(response.message || 'Invalid username or password');
        setLoading(false);
        return;
      }
      
      // Store user data
      login(response.user);
      navigate('/');
    } catch (err) {
      // Handle different error formats
      let errorMessage = 'Invalid username or password';
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        // If detail is a string, use it directly
        if (typeof detail === 'string') {
          errorMessage = detail;
        } 
        // If detail is an array (validation errors), extract messages
        else if (Array.isArray(detail)) {
          errorMessage = detail.map(e => e.msg || e).join(', ');
        }
        // If detail is an object, try to get message
        else if (typeof detail === 'object') {
          errorMessage = detail.msg || detail.message || JSON.stringify(detail);
        }
      }
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h1>📚 TestMyKnowledge</h1>
          <h2>Welcome Back!</h2>
          <p>Login to continue your learning journey</p>
        </div>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter your username"
              required
              autoFocus
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
            />
          </div>

          <button type="submit" className="auth-button" disabled={loading}>
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            Don't have an account? <Link to="/register">Register here</Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;

