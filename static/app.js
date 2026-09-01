// Store - simple state management and rendering helper
// This module provides a reactive state store and a minimal rendering utility.

/**
 * Creates a new Store with the given initial state.
 * Subscribers are notified on every state update.
 *
 * @param {Object} initialState - the initial state object
 * @returns {Object} store API
 */
export function createStore(initialState = {}) {
  let state = { ...initialState };
  const subscribers = new Set();

  /**
   * Returns the current state (shallow copy).
   * @returns {Object}
   */
  function getState() {
    return { ...state };
  }

  /**
   * Merges the given partial state into the current state
   * and notifies all subscribers.
   *
   * @param {Object} partial - partial state to merge
   */
  function setState(partial) {
    if (typeof partial !== 'object' || partial === null) {
      throw new Error('setState expects an object');
    }
    state = { ...state, ...partial };
    subscribers.forEach((subscriber) => {
      try {
        subscriber(getState());
      } catch (e) {
        console.error('Subscriber error:', e);
      }
    });
  }

  /**
   * Registers a subscriber to be called on state changes.
   * Returns an unsubscribe function.
   *
   * @param {Function} subscriber - receives the new state
   * @returns {Function} unsubscribe
   */
  function subscribe(subscriber) {
    if (typeof subscriber !== 'function') {
      throw new Error('Subscriber must be a function');
    }
    subscribers.add(subscriber);
    return () => {
      subscribers.delete(subscriber);
    };
  }

  return { getState, setState, subscribe };
}

/**
 * Updates the innerHTML of a DOM element with the given value.
 * Simple rendering helper to decouple view updates.
 *
 * @param {string} selector - CSS selector
 * @param {string} html - HTML string to set
 */
export function render(selector, html) {
  const element = document.querySelector(selector);
  if (!element) {
    console.warn(`render: element not found for selector "${selector}"`);
    return;
  }
  element.innerHTML = html;
}
