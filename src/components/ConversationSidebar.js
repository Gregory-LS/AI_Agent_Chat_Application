import React, { useState, useEffect } from 'react';

const ConversationSidebar = ({ onSelectConversation }) => {
  const [conversations, setConversations] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [newTitle, setNewTitle] = useState('');

  useEffect(() => {
    fetch('/api/conversations')
      .then(res => res.json())
      .then(data => setConversations(data))
      .catch(err => console.error('Failed to load conversations', err));
  }, []);

  const handleCreate = () => {
    if (!newTitle.trim()) return;
    fetch('/api/conversations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: newTitle }),
    })
      .then(res => res.json())
      .then(conv => {
        setConversations(prev => [...prev, conv]);
        setNewTitle('');
      })
      .catch(err => console.error('Failed to create conversation', err));
  };

  const handleDelete = (id) => {
    if (!window.confirm('Delete this conversation?')) return;
    fetch(`/api/conversations/${id}`, { method: 'DELETE' })
      .then(() => {
        setConversations(prev => prev.filter(c => c.id !== id));
        if (activeId === id) {
          setActiveId(null);
          if (onSelectConversation) onSelectConversation(null);
        }
      })
      .catch(err => console.error('Failed to delete conversation', err));
  };

  const handleSelect = (id) => {
    setActiveId(id);
    if (onSelectConversation) onSelectConversation(id);
  };

  return (
    <div className="conversation-sidebar">
      <div className="sidebar-header">
        <h3>Conversations</h3>
        <div className="new-conversation">
          <input
            type="text"
            placeholder="New conversation title..."
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
          />
          <button onClick={handleCreate}>+</button>
        </div>
      </div>
      <ul className="conversation-list">
        {conversations.map(conv => (
          <li
            key={conv.id}
            className={conv.id === activeId ? 'active' : ''}
            onClick={() => handleSelect(conv.id)}
          >
            <span className="conv-title">{conv.title}</span>
            <button
              className="delete-btn"
              onClick={(e) => { e.stopPropagation(); handleDelete(conv.id); }}
            >
              ×
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ConversationSidebar;
