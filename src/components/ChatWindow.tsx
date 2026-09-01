import React from 'react';
import Message from './Message';
import { useMessageStore } from '../store/messageStore';

const ChatWindow: React.FC = () => {
  const messages = useMessageStore((state) => state.messages);

  return (
    <div className="chat-window">
      {messages.map((msg) => (
        <Message key={msg.id} id={msg.id} content={msg.content} role={msg.role} />
      ))}
    </div>
  );
};

export default ChatWindow;
