import React from 'react';

/**
 * Reusable Button Component with Tailwind CSS
 * 
 * @param {string} variant - Button style: 'primary', 'secondary', 'outline', 'danger', 'success', 'ghost'
 * @param {string} size - Button size: 'sm', 'md', 'lg'
 * @param {boolean} disabled - Disabled state
 * @param {string} className - Additional custom classes
 * @param {ReactNode} children - Button content
 * @param {function} onClick - Click handler
 */
const Button = ({ 
  variant = 'primary', 
  size = 'md', 
  disabled = false, 
  className = '', 
  children, 
  onClick,
  type = 'button',
  ...props 
}) => {
  // Base styles for all buttons
  const baseStyles = 'inline-flex items-center justify-center font-medium rounded-lg transition-all duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-60 disabled:cursor-not-allowed';

  // Variant styles
  const variantStyles = {
    primary: 'bg-primary text-white hover:bg-primary-hover focus:ring-primary shadow-md hover:shadow-lg',
    secondary: 'bg-secondary text-white hover:bg-secondary-hover focus:ring-secondary shadow-md hover:shadow-lg',
    danger: 'bg-danger text-white hover:bg-danger-hover focus:ring-danger shadow-md hover:shadow-lg',
    success: 'bg-success text-white hover:bg-emerald-600 focus:ring-success shadow-md hover:shadow-lg',
    outline: 'border-2 border-gray-300 text-gray-700 hover:bg-gray-50 hover:border-gray-400 focus:ring-gray-400',
    ghost: 'text-gray-700 hover:bg-gray-100 focus:ring-gray-400',
    icon: 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 hover:shadow-md focus:ring-gray-400',
  };

  // Size styles
  const sizeStyles = {
    sm: 'px-3 py-1.5 text-sm min-h-[36px]',
    md: 'px-4 py-2 text-base min-h-[44px]',
    lg: 'px-6 py-3 text-lg min-h-[48px]',
  };

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};

export default Button;
