import React from 'react';

/**
 * Reusable Badge Component with Tailwind CSS
 * 
 * @param {string} variant - Badge style: 'default', 'primary', 'success', 'warning', 'danger', 'info'
 * @param {string} difficulty - Difficulty level: 'easy', 'medium', 'hard'
 * @param {string} status - Status type: 'pending', 'completed', 'excellent', 'good', 'average', 'needs-improvement'
 * @param {string} size - Badge size: 'sm', 'md', 'lg'
 * @param {string} className - Additional custom classes
 * @param {ReactNode} children - Badge content
 */
const Badge = ({ 
  variant, 
  difficulty,
  status,
  size = 'md',
  className = '', 
  children,
  ...props 
}) => {
  // Base styles for all badges
  const baseStyles = 'inline-flex items-center justify-center font-semibold rounded-full transition-all duration-200';

  // Size styles
  const sizeStyles = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-3 py-1 text-sm',
    lg: 'px-4 py-1.5 text-base',
  };

  // Variant styles (generic)
  const variantStyles = {
    default: 'bg-gray-100 text-gray-700',
    primary: 'bg-blue-100 text-blue-700',
    success: 'bg-green-100 text-green-700',
    warning: 'bg-yellow-100 text-yellow-700',
    danger: 'bg-red-100 text-red-700',
    info: 'bg-indigo-100 text-indigo-700',
  };

  // Difficulty-specific styles
  const difficultyStyles = {
    easy: 'bg-gradient-to-r from-green-100 to-emerald-100 text-green-700 shadow-sm',
    medium: 'bg-gradient-to-r from-yellow-100 to-amber-100 text-yellow-700 shadow-sm',
    hard: 'bg-gradient-to-r from-red-100 to-rose-100 text-red-700 shadow-sm',
  };

  // Status-specific styles (for tests/feedback)
  const statusStyles = {
    pending: 'bg-gradient-to-r from-yellow-50 to-amber-50 text-amber-700 border border-amber-200',
    completed: 'bg-gradient-to-r from-green-50 to-emerald-50 text-green-700 border border-green-200',
    excellent: 'bg-gradient-to-r from-green-400 to-emerald-500 text-white shadow-lg shadow-green-200',
    good: 'bg-gradient-to-r from-blue-400 to-cyan-500 text-white shadow-lg shadow-blue-200',
    average: 'bg-gradient-to-r from-purple-400 to-violet-500 text-white shadow-lg shadow-purple-200',
    'needs-improvement': 'bg-gradient-to-r from-red-400 to-rose-500 text-white shadow-lg shadow-red-200',
  };

  // Determine which style to use
  let appliedStyle = variantStyles[variant] || variantStyles.default;
  
  if (difficulty) {
    appliedStyle = difficultyStyles[difficulty.toLowerCase()] || difficultyStyles.medium;
  }
  
  if (status) {
    appliedStyle = statusStyles[status.toLowerCase()] || statusStyles.pending;
  }

  return (
    <span
      className={`${baseStyles} ${sizeStyles[size]} ${appliedStyle} ${className}`}
      {...props}
    >
      {children}
    </span>
  );
};

export default Badge;
