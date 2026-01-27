import React from 'react';
import './Modal.css';

const ResumeTestModal = ({ open, onResume, onRestart, onCancel, questionIndex, totalQuestions }) => {
  if (!open) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-container">
        <div className="modal-header">
          <h2>📋 Resume Test?</h2>
        </div>
        <div className="modal-body">
          <p className="modal-message">
            You have an unfinished test attempt at <strong>question {questionIndex + 1} of {totalQuestions}</strong>.
          </p>
          <p className="modal-message">
            Would you like to resume where you left off or start over?
          </p>
        </div>
        <div className="modal-actions">
          <button
            onClick={onCancel}
            className="modal-button modal-button-cancel"
          >
            Cancel
          </button>
          <button
            onClick={onRestart}
            className="modal-button modal-button-secondary"
          >
            🔄 Start Over
          </button>
          <button
            onClick={onResume}
            className="modal-button modal-button-primary"
          >
            ▶️ Resume Test
          </button>
        </div>
      </div>
    </div>
  );
};

export default ResumeTestModal;
