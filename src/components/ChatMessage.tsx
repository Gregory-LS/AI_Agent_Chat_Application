import { useState } from 'react';
import { User, Bot } from 'lucide-react';
import RegenerateButton from './RegenerateButton';
import StopButton from './StopButton';
import TransitionWrapper from './TransitionWrapper';

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  isStreaming?: boolean;
  onRegenerate?: () => void;
  onStop?: () => void;
}

export default function ChatMessage({ role, content, isStreaming = false, onRegenerate, onStop }: ChatMessageProps) {
  const [visible, setVisible] = useState(true);
  const isUser = role === 'user';

  return (
    <TransitionWrapper show={visible} type="slide-up">
      <div className={`flex gap-3 p-4 ${isUser ? 'flex-row-reverse' : ''}`}>
        <div
          className={`w-8 h-8 rounded-full flex items-center justify-center ${
            isUser ? 'bg-blue-500' : 'bg-gray-300'
          }`}
        >
          {isUser ? <User className="w-5 h-5 text-white" /> : <Bot className="w-5 h-5 text-gray-600" />}
        </div>
        <div
          className={`flex-1 p-3 rounded-lg ${
            isUser
              ? 'bg-blue-100 text-blue-900'
              : 'bg-gray-100 text-gray-900'
          }`}
        >
          <p className="whitespace-pre-wrap">{content}</p>
          {isStreaming && (
            <span className="inline-block w-2 h-4 bg-gray-400 animate-pulse ml-1" />
          )}
          {!isUser && !isStreaming && (
            <div className="flex gap-2 mt-2">
              {onRegenerate && <RegenerateButton onClick={onRegenerate} />}
              {onStop && <StopButton onClick={onStop} />}
            </div>
          )}
        </div>
      </div>
    </TransitionWrapper>
  );
}
