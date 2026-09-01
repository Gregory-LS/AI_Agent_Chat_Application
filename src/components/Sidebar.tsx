import React, { useState, useMemo, useCallback } from 'react';

interface Conversation {
  id: string;
  title: string;
  participants: string[];
  lastMessage: string;
  timestamp: number;
}

interface SidebarProps {
  conversations: Conversation[];
  onSelectConversation: (id: string) => void;
  selectedConversationId?: string;
}

const Sidebar: React.FC<SidebarProps> = ({
  conversations,
  onSelectConversation,
  selectedConversationId,
}) => {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredConversations = useMemo(() => {
    if (!searchQuery.trim()) {
      return conversations;
    }
    const query = searchQuery.toLowerCase();
    return conversations.filter(
      (conv) =>
        conv.title.toLowerCase().includes(query) ||
        conv.participants.some((p) => p.toLowerCase().includes(query))
    );
  }, [conversations, searchQuery]);

  const handleSearchChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setSearchQuery(e.target.value);
    },
    []
  );

  const handleClearSearch = useCallback(() => {
    setSearchQuery('');
  }, []);

  return (
    <aside className="sidebar">
      <div className="sidebar-search">
        <input
          type="text"
          placeholder="Search conversations..."
          value={searchQuery}
          onChange={handleSearchChange}
          aria-label="Search conversations"
          className="search-input"
        />
        {searchQuery && (
          <button
            onClick={handleClearSearch}
            className="search-clear-button"
            aria-label="Clear search"
          >
            &times;
          </button>
        )}
      </div>
      <ul className="conversation-list">
        {filteredConversations.length === 0 ? (
          <li className="no-results">No conversations found</li>
        ) : (
          filteredConversations.map((conv) => (
            <li
              key={conv.id}
              className={`conversation-item ${
                conv.id === selectedConversationId ? 'selected' : ''
              }`}
              onClick={() => onSelectConversation(conv.id)}
            >
              <div className="conversation-title">{conv.title}</div>
              <div className="conversation-participants">
                {conv.participants.join(', ')}
              </div>
              <div className="conversation-last-message">{conv.lastMessage}</div>
            </li>
          ))
        )}
      </ul>
    </aside>
  );
};

export default Sidebar;
