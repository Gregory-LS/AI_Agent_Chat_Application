# Skills Drawer Panel

A React component that provides a drawer/panel for managing skills with full CRUD (Create, Read, Update, Delete) functionality.

## Features

- Toggle open/close the skills panel
- Add a new skill
- Edit an existing skill
- Delete a skill
- Keyboard support (Enter to add/save)
- Empty state display

## Installation

Clone the repository and install dependencies:

```bash
npm install
```

## Usage

Import the component into your React application:

```jsx
import SkillsDrawer from './components/SkillsDrawer';

function App() {
  return (
    <div>
      <SkillsDrawer />
    </div>
  );
}
```

## Running Tests

Tests are written with Jest and React Testing Library. Run them with:

```bash
npm test
```

## Files

- `src/components/SkillsDrawer.js` - Main component
- `src/components/SkillsDrawer.css` - Styles for the drawer
- `tests/test_SkillsDrawer.js` - Unit tests