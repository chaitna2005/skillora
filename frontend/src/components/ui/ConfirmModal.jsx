import React, { useEffect } from 'react';
import '../../styles/ConfirmModal.css';

const ConfirmModal = ({ open, title, message, onConfirm, onCancel }) => {
  // Close modal on ESC key press
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && open) {
        onCancel();
      }
    };

    if (open) {
      document.addEventListener('keydown', handleEscape);
      // Prevent body scroll when modal is open
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [open, onCancel]);

  if (!open) return null;

  return (
    <div className="confirm-modal-overlay" onClick={onCancel}>
      <div className="confirm-modal-content" onClick={(e) => e.stopPropagation()}>
        {title && <h3 className="confirm-modal-title">{title}</h3>}
        <p className="confirm-modal-message">{message}</p>
        <div className="confirm-modal-actions">
          <button 
            className="confirm-modal-btn confirm-modal-cancel" 
            onClick={onCancel}
          >
            Cancel
          </button>
          <button 
            className="confirm-modal-btn confirm-modal-ok" 
            onClick={onConfirm}
          >
            OK
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmModal;
