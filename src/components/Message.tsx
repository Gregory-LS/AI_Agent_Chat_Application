import React, { useState } from 'react';
import MessageActions from './MessageActions';

interface MessageProps {
  id: string;
  content: string;
  role: 'user' | 'assistant';
}

const Message: React.FC<MessageProps> = ({ id, content, role }) => {
  const [showActions, setShowActions] = useState(false);

  return (
    <div
      className={`message message-${role}`}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      <div className="message-content">{content}</div>
      {showActions && (
        <MessageActions
          messageId={id}
          content={content}
          onClose={() => setShowActions(false)}
        />
      )}
    </div>
  );
};

export default Message;
