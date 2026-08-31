import React from 'react';
import PropTypes from 'prop-types';

const ConversationList = ({ conversations, searchTerm, onConversationClick }) => {
  const filtered = conversations.filter((conv) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      (conv.name && conv.name.toLowerCase().includes(term)) ||
      (conv.lastMessage && conv.lastMessage.toLowerCase().includes(term))
    );
  });

  if (filtered.length === 0) {
    return <div className="conversation-list-empty">No conversations found</div>;
  }

  return (
    <ul className="conversation-list">
      {filtered.map((conv) => (
        <li
          key={conv.id}
          className="conversation-item"
          onClick={() => onConversationClick && onConversationClick(conv)}
          role="button"
          tabIndex={0}
          onKeyPress={(e) => {
            if (e.key === 'Enter') onConversationClick && onConversationClick(conv);
          }}
        >
          <div className="conversation-name">{conv.name}</div>
          <div className="conversation-last-message">{conv.lastMessage}</div>
        </li>
      ))}
    </ul>
  );
};

ConversationList.propTypes = {
  conversations: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      name: PropTypes.string,
      lastMessage: PropTypes.string,
    })
  ).isRequired,
  searchTerm: PropTypes.string,
  onConversationClick: PropTypes.func,
};

export default ConversationList;
