# Skills Drawer Component

A reusable React component that provides a drawer panel for managing skills with full CRUD (Create, Read, Update, Delete) operations.

## Features

- **Open/Close Drawer**: Click "Manage Skills" button to open drawer, "Close" button or overlay click to close.
- **List Skills**: Fetches and displays all skills on drawer open.
- **Add Skill**: Form to input name, description, and level (beginner/intermediate/advanced).
- **Edit Skill**: Click "Edit" on a skill to pre-fill the form and update the skill.
- **Delete Skill**: Click "Delete" to remove a skill after confirmation (immediate in current implementation).
- **Error Handling**: Displays error messages for failed operations.
- **Loading State**: Shows loading indicator while API calls are in progress.

## Usage

```tsx
import SkillsDrawer from './components/SkillsDrawer/SkillsDrawer';

function App() {
  return (
    <div>
      <SkillsDrawer />
    </div>
  );
}
```

## API Service

The component relies on an API service (`src/services/skillsService.ts`) that exports `skillsService` with methods: `getSkills`, `createSkill`, `updateSkill`, `deleteSkill`. The current implementation uses a mock in-memory store. Replace with real HTTP calls.

## Testing

Run tests with:

```bash
npm test -- --testPathPattern=SkillsDrawer
```

Tests cover:
- Opening drawer and fetching skills
- Error handling on fetch failure
- Creating a skill
- Editing a skill
- Deleting a skill
- Cancelling edit mode

## Dependencies

- React 16+ (hooks)
- TypeScript (optional but recommended)
- For testing: @testing-library/react, @testing-library/jest-dom

## File Structure

```
src/
  components/
    SkillsDrawer/
      SkillsDrawer.tsx
      SkillsDrawer.css
      SkillsDrawer.test.tsx
  services/
    skillsService.ts
```