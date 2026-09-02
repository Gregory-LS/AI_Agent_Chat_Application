# Model Picker UI

A reusable React component for selecting a machine-learning model. It provides a searchable dropdown with keyboard navigation, async model loading, custom model lists, and accessible ARIA attributes.

## Features

- Search and filter models by id, name, or description
- Keyboard navigation: ArrowUp/ArrowDown, Home/End, Enter to select, Escape to close
- Async loading with `Loading…` and retryable `Error` states
- Support for static model lists or custom model fetchers
- Disabled state and custom placeholder
- Accessible ARIA combobox/listbox pattern

## Installation

```bash
npm install
npm test
```

## Usage

### Basic usage with default API

```tsx
import { ModelPicker } from './src';
import { useState } from 'react';

function App() {
  const [modelId, setModelId] = useState('gpt-4o');

  return <ModelPicker value={modelId} onChange={setModelId} />;
}
```

The default implementation fetches a JSON array from `/api/models`.

### Static model list

```tsx
const models = [
  { id: 'a', name: 'Model A', description: 'First model' },
  { id: 'b', name: 'Model B' },
];

<ModelPicker models={models} onChange={setModelId} />
```

### Custom fetch function

```tsx
<ModelPicker fetchModels={fetchFromMyService} onChange={setModelId} />
```

## Props

| Prop          | Type                              | Description                                     |
| ------------- | --------------------------------- | ----------------------------------------------- |
| `value`       | `string`                          | Selected model id.                              |
| `onChange`    | `(modelId: string) => void`       | Required callback when a model is selected.     |
| `models`      | `Model[]`                         | Optional static list of models.                 |
| `fetchModels` | `() => Promise<Model[]>`          | Optional custom model fetcher.                  |
| `disabled`    | `boolean`                         | Disables the picker.                            |
| `placeholder` | `string`                          | Placeholder text when nothing is selected.      |
| `aria-label`  | `string`                          | Accessible label for the trigger button.        |
| `className`   | `string`                          | Additional CSS class for the root container.    |

## Model type

```ts
interface Model {
  id: string;
  name: string;
  description?: string;
}
```

## Development

Run the Jest test suite:

```bash
npm test
```

Type-check the source:

```bash
npx tsc --noEmit
```