import React, { useState, useCallback, useRef, useEffect } from 'react';
import { useChat } from '../hooks/useChat';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { LoadingState } from './LoadingState';
import { EmptyState } from './EmptyState';
import { ErrorToast } from './ErrorToast';
import { ConfirmDialog } from './ConfirmDialog';
import { StopButton } from './StopButton';
import '../styles/chat.css';

interface ChatWindowProps {
  initialMessages?: Array<{ role: string; content: string }>;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({ initialMessages = [] }) => {
  const {
    messages,
    isLoading,
    error,
    sendMessage,
    regenerate,
    stopGeneration,
    clearMessages,
    isStreaming
  } = useChat(initialMessages);

  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'error' | 'info' } | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  useEffect(() => {
    if (error) {
      setToast({ message: error, type: 'error' });
      const timer = setTimeout(() => setToast(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  const handleClear = useCallback(() => {
    setShowClearConfirm(true);
  }, []);

  const confirmClear = useCallback(() => {
    clearMessages();
    setShowClearConfirm(false);
    setToast({ message: 'Conversation cleared', type: 'info' });
  }, [clearMessages]);

  const cancelClear = useCallback(() => {
    setShowClearConfirm(false);
  }, []);

  return (
    <div className="chat-window">
      {toast && (
        <ErrorToast
          message={toast.message}
          type={toast.type}
          onDismiss={() => setToast(null)}
        />
      )}
      {showClearConfirm && (
        <ConfirmDialog
          title="Clear conversation?"
          message="This will delete all messages in this conversation. This action cannot be undone."
          onConfirm={confirmClear}
          onCancel={cancelClear}
        />
      )}
      <div className="chat-messages">
        {messages.length === 0 && !isLoading ? (
          <EmptyState />
        ) : (
          <>
            {messages.map((msg, idx) => (
              <div key={idx} className={`message-row ${msg.role}`}>
                <ChatMessage message={msg} />
              </div>
            ))}
            {isLoading && <LoadingState />}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>
      <div className="chat-input-area">
        {isLoading && <StopButton onClick={stopGeneration} />}
        <ChatInput
          onSend={sendMessage}
          onRegenerate={regenerate}
          isLoading={isLoading}
          hasMessages={messages.length > 0}
          onClear={handleClear}
        />
      </div>
    </div>
  );
};
