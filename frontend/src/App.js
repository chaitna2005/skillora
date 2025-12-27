import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import Home from './pages/Home';
import CreateQuiz from './pages/CreateQuiz';
import QuizDetail from './pages/QuizDetail';
import TakeTest from './pages/TakeTest';
import TestResult from './pages/TestResult';
import './styles/App.css';

function App() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    // Check if user is logged in (from localStorage)
    const savedUser = localStorage.getItem('user');
    if (savedUser) {
      setUser(JSON.parse(savedUser));
    }
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
    localStorage.setItem('user', JSON.stringify(userData));
    localStorage.setItem('token', userData.access_token);
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('user');
    localStorage.removeItem('token');
  };

  return (
    <Router>
      <Routes>
        <Route
          path="/login"
          element={!user ? <Login onLogin={handleLogin} /> : <Navigate to="/home" />}
        />
        <Route
          path="/register"
          element={!user ? <Register /> : <Navigate to="/home" />}
        />
        <Route
          path="/home"
          element={user ? <Home user={user} onLogout={handleLogout} /> : <Navigate to="/login" />}
        />
        <Route
          path="/create-quiz"
          element={user ? <CreateQuiz user={user} onLogout={handleLogout} /> : <Navigate to="/login" />}
        />
        <Route
          path="/quiz/:quizId"
          element={user ? <QuizDetail user={user} onLogout={handleLogout} /> : <Navigate to="/login" />}
        />
        <Route
          path="/take-test/:quizId"
          element={user ? <TakeTest user={user} onLogout={handleLogout} /> : <Navigate to="/login" />}
        />
        <Route
          path="/test-result/:uqtId"
          element={user ? <TestResult user={user} onLogout={handleLogout} /> : <Navigate to="/login" />}
        />
        <Route path="/" element={<Navigate to="/login" />} />
      </Routes>
    </Router>
  );
}

export default App;

