# Conversation Sidebar

A React component for displaying a list of conversations.

## Features

- View list of conversations
- Search/filter conversations by name
- Click to select a conversation
- Create new conversation
- Shows last message preview and timestamp

## Usage

```jsx
import Sidebar from './components/Sidebar';

<Sidebar
  conversations={conversations}
  onSelect={(id) => console.log('Selected:', id)}
  onCreateNew={() => console.log('New conversation')}
/>
```

## Props

| Prop | Type | Description |
|------|------|-------------|
| conversations | Array | Array of conversation objects: { id, name, lastMessage?, updatedAt? } |
| onSelect | Function | Called when a conversation is clicked, receives the conversation id |
| onCreateNew | Function | Called when the "+ New" button is clicked |
| currentUserId | (optional) | The current user's id (for future use) |

## Development

Install dependencies:

```bash
npm install
```

Run tests:

```bash
npm test
```

## Files

- `src/components/Sidebar.jsx` - React component
- `src/components/Sidebar.css` - Styles
- `tests/test_Sidebar.jsx` - Unit tests