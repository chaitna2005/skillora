import React from 'react';

/**
 * Reusable Modal Component with Tailwind CSS
 * 
 * @param {boolean} isOpen - Modal open state
 * @param {function} onClose - Close modal handler
 * @param {string} title - Modal title
 * @param {string} size - Modal size: 'sm', 'md', 'lg', 'xl'
 * @param {boolean} closeOnOverlayClick - Close when clicking overlay (default: true)
 * @param {ReactNode} children - Modal content
 * @param {string} className - Additional custom classes
 */
const Modal = ({ 
  isOpen, 
  onClose, 
  title,
  size = 'md',
  closeOnOverlayClick = true,
  children,
  className = '',
  ...props 
}) => {
  if (!isOpen) return null;

  const sizeStyles = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
    full: 'max-w-[95vw]',
  };

  const handleOverlayClick = (e) => {
    if (closeOnOverlayClick && e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4 overflow-y-auto"
      onClick={handleOverlayClick}
      {...props}
    >
      <div
        className={`
          bg-white rounded-2xl shadow-soft-xl 
          w-full ${sizeStyles[size]} 
          ${className}
          animate-fadeIn
        `}
      >
        {/* Modal Header */}
        {title && (
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
            <h2 className="text-2xl font-bold text-gray-900">{title}</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors duration-200 text-2xl leading-none focus:outline-none"
              aria-label="Close modal"
            >
              ×
            </button>
          </div>
        )}

        {/* Modal Content */}
        <div className="px-6 py-4">
          {children}
        </div>
      </div>
    </div>
  );
};

// Modal Footer Component
export const ModalFooter = ({ children, className = '' }) => (
  <div className={`flex items-center justify-end gap-3 mt-6 pt-4 border-t border-gray-200 ${className}`}>
    {children}
  </div>
);

// Confirmation Modal Component
export const ConfirmModal = ({ 
  isOpen, 
  onClose, 
  onConfirm,
  title = 'Confirm Action',
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  variant = 'danger',
}) => {
  return (
    <Modal isOpen={isOpen} onClose={onClose} size="sm">
      <div className="text-center">
        <div className="text-5xl mb-4">
          {variant === 'danger' ? '⚠️' : 'ℹ️'}
        </div>
        <h3 className="text-xl font-bold text-gray-900 mb-2">{title}</h3>
        {message && <p className="text-gray-600 mb-6">{message}</p>}
      </div>
      
      <ModalFooter className="justify-center border-0">
        <button
          onClick={onClose}
          className="px-6 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg font-medium transition-colors duration-200"
        >
          {cancelText}
        </button>
        <button
          onClick={() => {
            onConfirm();
            onClose();
          }}
          className={`
            px-6 py-2 text-white rounded-lg font-medium transition-colors duration-200
            ${variant === 'danger' 
              ? 'bg-danger hover:bg-danger-hover' 
              : 'bg-primary hover:bg-primary-hover'
            }
          `}
        >
          {confirmText}
        </button>
      </ModalFooter>
    </Modal>
  );
};

export default Modal;
