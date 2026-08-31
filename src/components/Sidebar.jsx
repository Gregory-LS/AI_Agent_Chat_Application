import React, { useState } from 'react';
import SearchInput from './SearchInput';
import ConversationList from './ConversationList';

const Sidebar = ({ conversations, onConversationClick }) => {
  const [searchTerm, setSearchTerm] = useState('');

  const handleSearch = (term) => {
    setSearchTerm(term);
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h2>Conversations</h2>
      </div>
      <SearchInput onSearch={handleSearch} />
      <ConversationList
        conversations={conversations}
        searchTerm={searchTerm}
        onConversationClick={onConversationClick}
      />
    </aside>
  );
};

export default Sidebar;
