# Sidebar Search Feature

This project now includes a search input in the sidebar to filter conversations by title or participant names.

## Usage

- Type in the search box at the top of the sidebar.
- The list of conversations will be filtered in real time.
- Click the × button to clear the search.

## Component

`Sidebar` component accepts:
- `conversations`: array of conversation objects with `id`, `title`, `participants`, `lastMessage`, `timestamp`.
- `onSelectConversation`: callback when a conversation is clicked.
- `selectedConversationId` (optional): ID of the currently selected conversation.

## Testing

Run tests with:

```bash
npm test
```

Tests cover:
- Rendering all conversations
- Filtering by title
- Filtering by participant name
- No results state
- Clear search functionality
- Conversation selection
- Highlighted selected conversation
