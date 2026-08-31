import React from 'react';

interface StopButtonProps {
  onClick: () => void;
}

export const StopButton: React.FC<StopButtonProps> = ({ onClick }) => {
  return (
    <button className="stop-button" onClick={onClick} title="Stop generation">
      <span className="stop-icon">⏹</span> Stop
    </button>
  );
};
