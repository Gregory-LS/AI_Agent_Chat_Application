# Chat Application

## Components

### ConversationSidebar

A React component that displays a list of conversations. It allows users to:
- View all conversations (fetched from `/api/conversations`)
- Select a conversation (highlights it and calls `onSelectConversation(id)`)
- Create a new conversation by entering a title and clicking the "+" button or pressing Enter
- Delete a conversation (with confirmation dialog)

#### Props
- `onSelectConversation` (function): Called with the conversation ID when a conversation is selected.

#### Usage

```jsx
import ConversationSidebar from './components/ConversationSidebar';

function App() {
  const handleSelect = (id) => {
    console.log('Selected conversation:', id);
  };
  return <ConversationSidebar onSelectConversation={handleSelect} />;
}
```

#### API Endpoints Expected
- `GET /api/conversations` – returns array of `{ id, title }`
- `POST /api/conversations` – accepts `{ title }`, returns new conversation object
- `DELETE /api/conversations/:id` – deletes conversation

#### Styling

The component uses class names:
- `.conversation-sidebar` – container
- `.sidebar-header` – header with title and input
- `.conversation-list` – unordered list
- `.active` – applied to selected list item
- `.delete-btn` – delete button

Add your own CSS to style these elements.

## Testing

Tests are located in `src/components/ConversationSidebar.test.js`. Run with:

```bash
npm test
```

Tests cover:
- Rendering conversations from API
- Active state on click
- Creating a new conversation
- Deleting with confirmation
- Cancelling deletion
