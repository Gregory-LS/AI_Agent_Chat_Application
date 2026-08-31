import React from 'react';

interface ChatMessageProps {
  message: {
    role: string;
    content: string;
  };
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  return (
    <div className={`chat-message ${message.role}`}>
      <div className="message-avatar">
        {message.role === 'user' ? '👤' : '🤖'}
      </div>
      <div className="message-content">
        {message.content}
      </div>
    </div>
  );
};
