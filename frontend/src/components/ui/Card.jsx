import React from 'react';

/**
 * Reusable Card Component with Tailwind CSS
 * 
 * @param {string} variant - Card style: 'default', 'gradient', 'hover'
 * @param {string} padding - Padding size: 'none', 'sm', 'md', 'lg'
 * @param {boolean} shadow - Enable shadow
 * @param {string} className - Additional custom classes
 * @param {ReactNode} children - Card content
 * @param {function} onClick - Optional click handler (makes card interactive)
 */
const Card = ({ 
  variant = 'default', 
  padding = 'md', 
  shadow = true,
  className = '', 
  children,
  onClick,
  ...props 
}) => {
  // Base styles for all cards
  const baseStyles = 'bg-white rounded-2xl border border-gray-200 transition-all duration-200 ease-in-out';

  // Variant styles
  const variantStyles = {
    default: shadow ? 'shadow-md' : '',
    gradient: 'bg-gradient-card shadow-md',
    hover: shadow ? 'shadow-md hover:shadow-lg hover:-translate-y-1 cursor-pointer' : 'hover:-translate-y-1 cursor-pointer',
  };

  // Padding styles
  const paddingStyles = {
    none: '',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  };

  // Make card clickable if onClick is provided
  const interactiveStyles = onClick ? 'cursor-pointer' : '';

  return (
    <div
      onClick={onClick}
      className={`${baseStyles} ${variantStyles[variant]} ${paddingStyles[padding]} ${interactiveStyles} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

// Card Header Component
export const CardHeader = ({ children, className = '' }) => (
  <div className={`mb-4 ${className}`}>
    {children}
  </div>
);

// Card Title Component
export const CardTitle = ({ children, className = '' }) => (
  <h3 className={`text-xl font-bold text-gray-900 ${className}`}>
    {children}
  </h3>
);

// Card Content Component
export const CardContent = ({ children, className = '' }) => (
  <div className={className}>
    {children}
  </div>
);

// Card Footer Component
export const CardFooter = ({ children, className = '' }) => (
  <div className={`mt-4 pt-4 border-t border-gray-200 ${className}`}>
    {children}
  </div>
);

export default Card;
