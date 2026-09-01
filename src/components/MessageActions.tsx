import React, { useState } from 'react';
import { useMessageStore } from '../store/messageStore';

interface MessageActionsProps {
  messageId: string;
  content: string;
  onClose: () => void;
}

const MessageActions: React.FC<MessageActionsProps> = ({ messageId, content, onClose }) => {
  const { deleteMessage, editMessage, messages } = useMessageStore();
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState(content);

  const handleCopy = () => {
    navigator.clipboard.writeText(content).catch(console.error);
    onClose();
  };

  const handleCopyMarkdown = () => {
    // Assume content is plain text; for markdown we could convert, but here we just copy as is.
    navigator.clipboard.writeText(content).catch(console.error);
    onClose();
  };

  const handleDelete = () => {
    deleteMessage(messageId);
    onClose();
  };

  const handleEdit = () => {
    setIsEditing(true);
  };

  const handleSaveEdit = () => {
    editMessage(messageId, editText);
    setIsEditing(false);
    onClose();
  };

  const handleCancelEdit = () => {
    setEditText(content);
    setIsEditing(false);
  };

  if (isEditing) {
    return (
      <div className="message-actions-editing">
        <textarea
          value={editText}
          onChange={(e) => setEditText(e.target.value)}
          rows={3}
        />
        <button onClick={handleSaveEdit}>Save</button>
        <button onClick={handleCancelEdit}>Cancel</button>
      </div>
    );
  }

  return (
    <div className="message-actions">
      <button onClick={handleCopy}>Copy</button>
      <button onClick={handleCopyMarkdown}>Copy Markdown</button>
      <button onClick={handleDelete}>Delete</button>
      <button onClick={handleEdit}>Edit</button>
    </div>
  );
};

export default MessageActions;
