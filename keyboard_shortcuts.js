/**
 * KeyboardShortcuts - a tiny, dependency-free manager for keyboard shortcuts.
 *
 * Usage:
 *   const shortcuts = new KeyboardShortcuts({
 *     'Ctrl+K': () => console.log('search pressed'),
 *     'Ctrl+Shift+N': () => console.log('new window'),
 *   });
 *   shortcuts.destroy();
 */
(function (global) {
  'use strict';

  const MODIFIER_ALIASES = {
    CTRL: 'ctrl',
    CONTROL: 'ctrl',
    CMD: 'meta',
    COMMAND: 'meta',
    META: 'meta',
    ALT: 'alt',
    OPTION: 'alt',
    SHIFT: 'shift'
  };

  const KEY_ALIASES = {
    ' ': 'SPACE',
    SPACEBAR: 'SPACE',
    ESC: 'ESCAPE',
    RETURN: 'ENTER',
    UP: 'ARROWUP',
    DOWN: 'ARROWDOWN',
    LEFT: 'ARROWLEFT',
    RIGHT: 'ARROWRIGHT',
    DEL: 'DELETE'
  };

  class KeyboardShortcuts {
    constructor(shortcuts = {}, options = {}) {
      this.shortcuts = new Map();
      this.enabled = true;
      this.ignoreInputs = options.ignoreInputs !== false;

      for (const combo of Object.keys(shortcuts)) {
        this.register(combo, shortcuts[combo]);
      }

      this._handler = this._handler.bind(this);
      document.addEventListener('keydown', this._handler);
    }

    register(combo, callback) {
      if (typeof callback !== 'function') {
        throw new TypeError('Shortcut callback must be a function.');
      }
      const normalized = this._normalize(combo);
      this.shortcuts.set(combo, { normalized, callback });
    }

    unregister(combo) {
      this.shortcuts.delete(combo);
    }

    enable() {
      this.enabled = true;
    }

    disable() {
      this.enabled = false;
    }

    destroy() {
      document.removeEventListener('keydown', this._handler);
    }

    _normalize(combo) {
      const parts = combo.split('+').map((s) => s.trim()).filter(Boolean);
      const descriptor = { ctrl: false, meta: false, alt: false, shift: false, key: null };

      for (const part of parts) {
        const upper = part.toUpperCase();
        const modifier = MODIFIER_ALIASES[upper];
        if (modifier) {
          descriptor[modifier] = true;
        } else {
          if (descriptor.key !== null) {
            throw new Error(`Shortcut '${combo}' contains more than one non-modifier key.`);
          }
          descriptor.key = KEY_ALIASES[upper] || upper;
        }
      }

      if (!descriptor.key) {
        throw new Error(`Shortcut '${combo}' must include a non-modifier key.`);
      }
      return descriptor;
    }

    _getEventDescriptor(event) {
      let key = event.key;
      if (key === ' ') key = 'SPACE';
      else key = key.toUpperCase();
      if (KEY_ALIASES[key]) key = KEY_ALIASES[key];

      return {
        ctrl: event.ctrlKey,
        meta: event.metaKey,
        alt: event.altKey,
        shift: event.shiftKey,
        key
      };
    }

    _isTypingTarget(event) {
      if (!this.ignoreInputs) return false;
      const target = event.target;
      if (target instanceof HTMLElement) {
        if (/^(INPUT|TEXTAREA|SELECT|BUTTON)$/.test(target.tagName)) return true;
        if (target.isContentEditable) return true;
      }
      return false;
    }

    _handler(event) {
      if (!this.enabled) return;
      if (event.defaultPrevented) return;
      if (this._isTypingTarget(event)) return;

      const actual = this._getEventDescriptor(event);

      for (const { normalized, callback } of this.shortcuts.values()) {
        if (actual.key === normalized.key &&
            actual.ctrl === normalized.ctrl &&
            actual.meta === normalized.meta &&
            actual.alt === normalized.alt &&
            actual.shift === normalized.shift) {
          event.preventDefault();
          callback(event);
          return;
        }
      }
    }
  }

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = KeyboardShortcuts;
  } else {
    global.KeyboardShortcuts = KeyboardShortcuts;
  }
})(typeof window !== 'undefined' ? window : this);