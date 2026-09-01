# State Management and Rendering Utility

This module provides a simple state management store (`createStore`) and a DOM rendering helper (`render`).

## Functions

### `createStore(initialState)`

Creates a store with the given initial state. Returns an object with:

- `getState()` – returns the current state object.
- `setState(partialState)` – merges `partialState` into the current state and notifies all subscribers.
- `subscribe(listener)` – adds a listener that is called with the new state after every update. Returns an unsubscribe function.

### `render(store, root, renderFn)`

Renders the view initially and on every state change. 

- `store` – a store created by `createStore`.
- `root` – a DOM element (or mock with `innerHTML`).
- `renderFn` – function that receives the current state and returns an HTML string.

Returns an unsubscribe function to stop updating the view.

## Usage Example

```javascript
const { createStore, render } = require('./static/app');

const store = createStore({ count: 0 });
const root = document.getElementById('app');
render(store, root, (state) => `<h1>Count: ${state.count}</h1>`);

store.setState({ count: 1 });
// DOM updates automatically
```

## Running Tests

```bash
node --experimental-vm-modules tests/test_app.js
```

(If using CommonJS, simply `node tests/test_app.js`)
