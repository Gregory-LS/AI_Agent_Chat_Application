import React from 'react';

export const EmptyState: React.FC = () => {
  return (
    <div className="empty-state">
      <div className="empty-state-icon">💬</div>
      <h2>Start a conversation</h2>
      <p>Type a message below to begin chatting with the AI assistant.</p>
    </div>
  );
};
