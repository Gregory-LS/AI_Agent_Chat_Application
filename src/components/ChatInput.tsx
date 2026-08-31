import React, { useState, useCallback } from 'react';

interface ChatInputProps {
  onSend: (content: string) => void;
  onRegenerate: () => void;
  isLoading: boolean;
  hasMessages: boolean;
  onClear: () => void;
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSend, onRegenerate, isLoading, hasMessages, onClear }) => {
  const [input, setInput] = useState('');

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSend(input);
      setInput('');
    }
  }, [input, isLoading, onSend]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  }, [handleSubmit]);

  return (
    <div className="chat-input-container">
      <form onSubmit={handleSubmit} className="chat-input-form">
        <textarea
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your message..."
          disabled={isLoading}
          rows={1}
        />
        <button type="submit" className="send-button" disabled={!input.trim() || isLoading}>
          Send
        </button>
      </form>
      <div className="chat-actions">
        {hasMessages && !isLoading && (
          <>
            <button className="regenerate-button" onClick={onRegenerate}>
              Regenerate
            </button>
            <button className="clear-button" onClick={onClear}>
              Clear
            </button>
          </>
        )}
      </div>
    </div>
  );
};
