import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import '../styles/Sidebar.css';

const Sidebar = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  
  // Sidebar collapsed by default (Gmail-style: icon-only)
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(true);
  
  // Track if we're on desktop (for hover behavior)
  const [isDesktop, setIsDesktop] = useState(window.innerWidth >= 1025);

  // Update body class when sidebar collapse state changes
  useEffect(() => {
    if (isSidebarCollapsed) {
      document.body.classList.add('sidebar-collapsed');
    } else {
      document.body.classList.remove('sidebar-collapsed');
    }
    
    // Cleanup on unmount
    return () => {
      document.body.classList.remove('sidebar-collapsed');
    };
  }, [isSidebarCollapsed]);

  // Track screen size for responsive behavior
  useEffect(() => {
    const handleResize = () => {
      const desktop = window.innerWidth >= 1025;
      setIsDesktop(desktop);
      
      // On mobile/tablet, always keep sidebar collapsed (drawer mode)
      if (!desktop) {
        setIsSidebarCollapsed(true);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  // Gmail-style hover behavior: only on desktop
  const handleMouseEnter = () => {
    if (isDesktop) {
      setIsSidebarCollapsed(false);
    }
  };

  const handleMouseLeave = () => {
    if (isDesktop) {
      setIsSidebarCollapsed(true);
    }
  };

  // Close mobile menu helper
  const closeMobileMenu = () => {
    setIsMobileMenuOpen(false);
  };

  if (!isAuthenticated) {
    return null;
  }

  const isActive = (path) => {
    return location.pathname === path;
  };

  return (
    <>
      {/* Mobile menu toggle button */}
      <button 
        className="mobile-menu-toggle"
        onClick={toggleMobileMenu}
        aria-label="Toggle menu"
      >
        <span className={`hamburger ${isMobileMenuOpen ? 'open' : ''}`}>
          <span></span>
          <span></span>
          <span></span>
        </span>
      </button>

      {/* Overlay for mobile */}
      {isMobileMenuOpen && (
        <div 
          className="sidebar-overlay"
          onClick={toggleMobileMenu}
        />
      )}

      {/* Sidebar with Gmail-style hover behavior */}
      <aside 
        className={`sidebar ${isMobileMenuOpen ? 'open' : ''} ${isSidebarCollapsed ? 'collapsed' : ''}`}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
      >
        <div className="sidebar-header">
          <Link to="/" className="sidebar-logo" onClick={closeMobileMenu}>
            <span className="logo-icon">📚</span>
            <span className="logo-text">TestMyKnowledge</span>
          </Link>
        </div>

        <nav className="sidebar-nav">
          <Link 
            to="/" 
            className={`sidebar-link ${isActive('/') ? 'active' : ''}`}
            onClick={closeMobileMenu}
          >
            <span className="link-icon">🏠</span>
            <span className="link-text">Home</span>
          </Link>
          
          <Link 
            to="/create-quiz" 
            className={`sidebar-link ${isActive('/create-quiz') ? 'active' : ''}`}
            onClick={closeMobileMenu}
          >
            <span className="link-icon">✨</span>
            <span className="link-text">Create Quiz</span>
          </Link>
          
          <Link 
            to="/my-tests" 
            className={`sidebar-link ${isActive('/my-tests') ? 'active' : ''}`}
            onClick={closeMobileMenu}
          >
            <span className="link-icon">📝</span>
            <span className="link-text">My Tests</span>
          </Link>
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-user">
            <div className="user-info">
              <span className="user-name">
                {user?.first_name} {user?.last_name}
              </span>
              <span className="user-role">{user?.role}</span>
            </div>
            <button onClick={handleLogout} className="logout-btn">
              <span className="logout-icon">🚪</span>
              <span className="logout-text">Logout</span>
            </button>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;

