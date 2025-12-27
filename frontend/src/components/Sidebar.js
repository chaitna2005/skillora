import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

function Sidebar({ user, onLogout }) {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    { path: '/home', label: 'Home', icon: '🏠' },
    { path: '/create-quiz', label: 'Create Quiz', icon: '➕' },
  ];

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h2>TestMyKnowledge</h2>
        <div className="user-info">
          <p>{user.first_name} {user.last_name}</p>
          <span className="user-role">{user.role}</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        {menuItems.map((item) => (
          <button
            key={item.path}
            className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
            onClick={() => navigate(item.path)}
          >
            <span className="nav-icon">{item.icon}</span>
            {item.label}
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <button className="logout-btn" onClick={onLogout}>
          🚪 Logout
        </button>
      </div>
    </div>
  );
}

export default Sidebar;

