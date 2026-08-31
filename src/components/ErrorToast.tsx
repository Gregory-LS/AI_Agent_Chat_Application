import React from 'react';

interface ErrorToastProps {
  message: string;
  type: 'error' | 'info';
  onDismiss: () => void;
}

export const ErrorToast: React.FC<ErrorToastProps> = ({ message, type, onDismiss }) => {
  return (
    <div className={`toast toast-${type}`}>
      <span className="toast-message">{message}</span>
      <button className="toast-dismiss" onClick={onDismiss} aria-label="Dismiss">
        &times;
      </button>
    </div>
  );
};
