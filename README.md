# Model Picker Component

A reusable React component for selecting an AI model from a dropdown list.

## Installation

Copy the `src/components/ModelPicker.tsx` and `src/components/ModelPicker.module.css` into your project.

## Usage

```tsx
import { ModelPicker } from './components';

const models = ['GPT-3', 'GPT-4', 'BERT', 'T5'];
const [selected, setSelected] = useState<string>('');

<ModelPicker
  models={models}
  selectedModel={selected}
  onSelect={setSelected}
  disabled={false}
  placeholder="Pick a model"
/>
```

## Props

| Prop          | Type       | Default           | Description                          |
|---------------|------------|-------------------|--------------------------------------|
| `models`      | `string[]` | (required)        | Array of model names to display      |
| `selectedModel` | `string`   | -               | Currently selected model             |
| `onSelect`    | `(model: string) => void` | (required) | Callback when a model is selected |
| `disabled`    | `boolean`  | `false`           | Disables the select                  |
| `placeholder` | `string`   | `'Select a model'` | Placeholder text for unselected state |

## Testing

Run tests with:

```bash
npm test -- --testPathPattern=ModelPicker
```

Covered behaviors:
- Rendering all options
- Displaying the selected value
- Triggering the `onSelect` callback with the chosen model
- Not triggering on placeholder selection
- Disabled state
- Custom placeholder
- Empty models list
