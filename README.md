# Frontend App

This directory contains the static frontend code.

## Modules

### `app.js`

Core utilities for state management and rendering.

- **`createState(initialValue)`** — Creates a reactive state container with methods `get()`, `set(newValue)`, and `subscribe(callback)`. The `set` method notifies all subscribers unless the new value is reference-equal to the current one.
- **`render(elementId, template)`** — Sets `innerHTML` of the element with the given id to the template string. Throws if the element is not found.

## Tests

Tests are in `tests/test_app.js`. They use a minimal assertion framework and can be run in Node (with ES module support) or in a browser with a module script tag.

Example usage:

```javascript
import { createState } from './app.js';

const counter = createState(0);
counter.subscribe(val => console.log('Counter:', val));
counter.set(1); // logs: Counter: 1
```
