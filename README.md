# Keyboard Shortcuts

A small, dependency-free utility for adding keyboard shortcuts to web pages.

## Features

- Configure shortcuts with `Modifier+Key` strings
- Supports `Ctrl`, `Meta`/`Cmd`, `Alt`, `Shift`
- Ignores shortcuts while typing in form fields by default
- Enable/disable at runtime
- No dependencies

## Usage

Include the file:

```html
<script src='keyboard_shortcuts.js'></script>
```

Or in a CommonJS environment:

```js
const KeyboardShortcuts = require('./keyboard_shortcuts');
```

Create a new instance with your shortcuts:

```js
const shortcuts = new KeyboardShortcuts({
  'Ctrl+K': () => openSearch(),
  'Ctrl+Shift+N': () => createNewNote(),
  'Alt+/': () => showHelp(),
});
```

You can also register shortcuts later:

```js
shortcuts.register('Ctrl+Z', () => undo());
shortcuts.unregister('Ctrl+Z');
```

Temporarily disable all shortcuts while a modal is open:

```js
modal.addEventListener('open', () => shortcuts.disable());
modal.addEventListener('close', () => shortcuts.enable());
```

Remove all listeners when done:

```js
shortcuts.destroy();
```

## Options

The constructor accepts a second argument:

```js
new KeyboardShortcuts(shortcuts, { ignoreInputs: false });
```

- `ignoreInputs` (default `true`): When `true`, shortcuts will not fire while
  focus is inside an `<input>`, `<textarea>`, `<select>`, `<button>`, or a
  `contenteditable` element.
