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
  const baseStyles = 'inline-flex items-center justify-center font-medium rounded-full transition-all duration-200 uppercase tracking-wide';

  // Size styles
  const sizeStyles = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-3 py-1 text-xs',
    lg: 'px-4 py-1.5 text-sm',
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

  // Difficulty-specific styles - Professional premium design with dot indicators
  const difficultyStyles = {
    easy: 'bg-emerald-50 border border-emerald-200 text-slate-700 gap-1.5 before:content-[""] before:w-1.5 before:h-1.5 before:rounded-full before:bg-emerald-500 before:flex-shrink-0',
    medium: 'bg-amber-50 border border-amber-200 text-slate-700 gap-1.5 before:content-[""] before:w-1.5 before:h-1.5 before:rounded-full before:bg-amber-500 before:flex-shrink-0',
    hard: 'bg-rose-50 border border-rose-200 text-slate-700 gap-1.5 before:content-[""] before:w-1.5 before:h-1.5 before:rounded-full before:bg-rose-500 before:flex-shrink-0',
  };

  // Status-specific styles (for tests/feedback) - Professional premium design with dot indicators
  const statusStyles = {
    pending: 'bg-amber-50 border border-amber-200 text-slate-700 gap-1.5 before:content-[""] before:w-1.5 before:h-1.5 before:rounded-full before:bg-amber-500 before:flex-shrink-0',
    completed: 'bg-emerald-50 border border-emerald-200 text-slate-700 gap-1.5 before:content-[""] before:w-1.5 before:h-1.5 before:rounded-full before:bg-emerald-500 before:flex-shrink-0',
    excellent: 'bg-emerald-50 border border-emerald-200 text-slate-700 gap-1.5 before:content-[""] before:w-1.5 before:h-1.5 before:rounded-full before:bg-emerald-500 before:flex-shrink-0',
    good: 'bg-blue-50 border border-blue-200 text-slate-700 gap-1.5 before:content-[""] before:w-1.5 before:h-1.5 before:rounded-full before:bg-blue-500 before:flex-shrink-0',
    average: 'bg-amber-50 border border-amber-200 text-slate-700 gap-1.5 before:content-[""] before:w-1.5 before:h-1.5 before:rounded-full before:bg-amber-500 before:flex-shrink-0',
    'needs-improvement': 'bg-rose-50 border border-rose-200 text-slate-700 gap-1.5 before:content-[""] before:w-1.5 before:h-1.5 before:rounded-full before:bg-rose-500 before:flex-shrink-0',
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
