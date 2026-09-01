import React, { useState } from 'react';

const Sidebar = ({ conversations, onSelect, onCreateNew, currentUserId }) => {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredConversations = conversations.filter((conversation) =>
    conversation.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h2>Conversations</h2>
        <button className="new-conversation-btn" onClick={onCreateNew}>
          + New
        </button>
      </div>
      <div className="search-bar">
        <input
          type="text"
          placeholder="Search conversations..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>
      <ul className="conversation-list">
        {filteredConversations.map((conversation) => (
          <li
            key={conversation.id}
            className={"conversation-item"}
            onClick={() => onSelect(conversation.id)}
          >
            <div className="conversation-name">{conversation.name}</div>
            <div className="conversation-meta">
              <span className="last-message">
                {conversation.lastMessage
                  ? conversation.lastMessage.substring(0, 30) + '...'
                  : 'No messages yet'}
              </span>
              <span className="timestamp">
                {conversation.updatedAt
                  ? new Date(conversation.updatedAt).toLocaleDateString()
                  : ''}
              </span>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Sidebar;