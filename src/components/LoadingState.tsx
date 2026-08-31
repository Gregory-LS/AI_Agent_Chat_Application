import React from 'react';

export const LoadingState: React.FC = () => {
  return (
    <div className="loading-state">
      <div className="spinner"></div>
      <p>Generating response...</p>
    </div>
  );
};
