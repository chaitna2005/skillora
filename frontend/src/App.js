import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Sidebar from './components/Sidebar';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import CreateQuiz from './pages/CreateQuiz';
import TakeTest from './pages/TakeTest';
import Results from './pages/Results';
import MyTests from './pages/MyTests';
import ViewQuiz from './pages/ViewQuiz';
import ClaimAssignment from './pages/ClaimAssignment';
import './App.css';

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <div className="w-12 h-12 border-4 border-gray-200 border-t-primary rounded-full animate-spin"></div>
      </div>
    );
  }
  
  return isAuthenticated ? children : <Navigate to="/login" />;
};

// Public Route Component (redirect to dashboard if already logged in)
const PublicRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
      </div>
    );
  }
  
  return !isAuthenticated ? children : <Navigate to="/" />;
};

function AppContent() {
  return (
    <Router>
      <div className="min-h-screen flex flex-row w-full overflow-x-hidden">
        <Sidebar />
        <div className="flex-1 ml-0 lg:ml-[280px] p-3 sm:p-4 md:p-6 lg:p-[30px] pt-[70px] lg:pt-[30px] min-h-screen bg-gradient-main bg-fixed w-full lg:w-[calc(100%-280px)] overflow-x-hidden transition-all duration-300 ease-in-out [body.sidebar-collapsed_&]:lg:ml-[60px] [body.sidebar-collapsed_&]:lg:w-[calc(100%-60px)]">
          <Routes>
            {/* Public Routes */}
            <Route path="/login" element={
              <PublicRoute>
                <Login />
              </PublicRoute>
            } />
            <Route path="/register" element={
              <PublicRoute>
                <Register />
              </PublicRoute>
            } />

            {/* Protected Routes */}
            <Route path="/" element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } />
            <Route path="/create-quiz" element={
              <ProtectedRoute>
                <CreateQuiz />
              </ProtectedRoute>
            } />
            <Route path="/view-quiz/:quizId" element={
              <ProtectedRoute>
                <ViewQuiz />
              </ProtectedRoute>
            } />
            <Route path="/take-test/:quizId" element={
              <ProtectedRoute>
                <TakeTest />
              </ProtectedRoute>
            } />
            <Route path="/results/:quizId" element={
              <ProtectedRoute>
                <Results />
              </ProtectedRoute>
            } />
            <Route path="/my-tests" element={
              <ProtectedRoute>
                <MyTests />
              </ProtectedRoute>
            } />
            <Route path="/assign/:token" element={
              <ProtectedRoute>
                <ClaimAssignment />
              </ProtectedRoute>
            } />

            {/* Redirect any unknown routes */}
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
