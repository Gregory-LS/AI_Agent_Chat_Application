# Static App - State management and rendering module

This module provides a lightweight state management and DOM rendering utility.

## Usage

### Import

```javascript
import { createStore, render } from './static/app.js';
```

### createStore(initialState)

Creates a reactive store.

- `initialState` (Object): initial state object.
- Returns an object with:
  - `getState()` - returns a shallow copy of the current state.
  - `setState(partial)` - merges partial state and notifies subscribers.
  - `subscribe(subscriber)` - adds a subscriber function. Returns an unsubscribe function.

```javascript
const store = createStore({ count: 0 });
store.subscribe((state) => {
  console.log('State updated:', state);
});
store.setState({ count: 1 });
```

### render(selector, html)

Updates the innerHTML of a DOM element identified by selector.

- `selector` (string): CSS selector for the target element.
- `html` (string): HTML content to set.

```javascript
render('#app', '<h1>Hello World</h1>');
```

## Testing

Tests are written with [Vitest](https://vitest.dev/). To run:

```bash
npx vitest run
```

## Files

- `static/app.js` - main module
- `tests/test_app.test.js` - unit tests
