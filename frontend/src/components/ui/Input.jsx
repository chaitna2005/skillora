import React from 'react';

/**
 * Reusable Input Component with Tailwind CSS
 * 
 * @param {string} type - Input type: 'text', 'email', 'password', 'number', 'textarea'
 * @param {string} label - Input label
 * @param {string} placeholder - Placeholder text
 * @param {string} value - Input value
 * @param {function} onChange - Change handler
 * @param {boolean} required - Required field
 * @param {boolean} disabled - Disabled state
 * @param {string} error - Error message
 * @param {string} helperText - Helper text below input
 * @param {string} className - Additional custom classes
 */
const Input = ({ 
  type = 'text',
  label,
  placeholder,
  value,
  onChange,
  required = false,
  disabled = false,
  error,
  helperText,
  className = '',
  rows = 4,
  ...props 
}) => {
  // Base input styles
  const baseStyles = 'w-full px-4 py-3 rounded-lg border-2 transition-all duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-offset-1 disabled:opacity-60 disabled:cursor-not-allowed disabled:bg-gray-50';

  // State-based styles
  const stateStyles = error
    ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
    : 'border-gray-200 focus:border-primary focus:ring-primary hover:border-gray-300';

  const inputElement = type === 'textarea' ? (
    <textarea
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      required={required}
      disabled={disabled}
      rows={rows}
      className={`${baseStyles} ${stateStyles} ${className} resize-vertical min-h-[120px]`}
      {...props}
    />
  ) : (
    <input
      type={type}
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      required={required}
      disabled={disabled}
      className={`${baseStyles} ${stateStyles} ${className}`}
      {...props}
    />
  );

  return (
    <div className="w-full">
      {label && (
        <label className="block mb-2 text-sm font-semibold text-gray-900">
          {label}
          {required && <span className="text-danger ml-1">*</span>}
        </label>
      )}
      {inputElement}
      {error && (
        <p className="mt-1.5 text-sm text-danger flex items-center gap-1">
          <span>⚠️</span>
          {error}
        </p>
      )}
      {helperText && !error && (
        <p className="mt-1.5 text-sm text-gray-500 italic">
          {helperText}
        </p>
      )}
    </div>
  );
};

// Select/Dropdown Component
export const Select = ({ 
  label,
  value,
  onChange,
  options = [],
  required = false,
  disabled = false,
  error,
  className = '',
  ...props 
}) => {
  const baseStyles = 'w-full px-4 py-3 rounded-lg border-2 transition-all duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-offset-1 disabled:opacity-60 disabled:cursor-not-allowed disabled:bg-gray-50';
  
  const stateStyles = error
    ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
    : 'border-gray-200 focus:border-primary focus:ring-primary hover:border-gray-300';

  return (
    <div className="w-full">
      {label && (
        <label className="block mb-2 text-sm font-semibold text-gray-900">
          {label}
          {required && <span className="text-danger ml-1">*</span>}
        </label>
      )}
      <select
        value={value}
        onChange={onChange}
        required={required}
        disabled={disabled}
        className={`${baseStyles} ${stateStyles} ${className}`}
        {...props}
      >
        {options.map((option, index) => (
          <option key={index} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {error && (
        <p className="mt-1.5 text-sm text-danger flex items-center gap-1">
          <span>⚠️</span>
          {error}
        </p>
      )}
    </div>
  );
};

export default Input;
