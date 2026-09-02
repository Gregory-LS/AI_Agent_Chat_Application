# Model Picker Component

A React component for selecting a model from a list fetched from an API.

## Usage

```tsx
import ModelPicker from './components/ModelPicker';

function App() {
  const handleSelect = (model) => {
    console.log('Selected model:', model);
  };

  return <ModelPicker onSelect={handleSelect} />;
}
```

## Props

- `onSelect: (model: Model) => void` – callback when a model is selected.

## Behavior

- Fetches models from `/api/models` on mount.
- Displays a loading message while fetching.
- Displays an error message if the fetch fails.
- Renders a dropdown with model names.
- Calls `onSelect` with the selected model object.

## Development

Run tests:

```bash
npm test
```

## Files

- `src/components/ModelPicker.tsx` – component implementation
- `src/components/__tests__/ModelPicker.test.tsx` – unit tests