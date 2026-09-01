/**
 * Simple state management and rendering utility.
 * Provides a createStore function for reactive state and a render function
 * to update the DOM based on a template.
 */

/**
 * Creates a store with reactive state.
 * @param {Object} initialState - The initial state object.
 * @returns {Object} Store with getState, setState, and subscribe methods.
 */
export function createStore(initialState = {}) {
  let state = { ...initialState };
  const listeners = new Set();

  /**
   * Returns the current state (shallow copy).
   * @returns {Object}
   */
  function getState() {
    return { ...state };
  }

  /**
   * Updates state by merging the given partial state.
   * Notifies all subscribed listeners.
   * @param {Object} newState - Partial state to merge.
   */
  function setState(newState) {
    state = { ...state, ...newState };
    listeners.forEach((listener) => listener(state));
  }

  /**
   * Subscribes a listener function that is called on every state change.
   * @param {Function} listener - Called with the new state.
   * @returns {Function} Unsubscribe function.
   */
  function subscribe(listener) {
    listeners.add(listener);
    return () => listeners.delete(listener);
  }

  return { getState, setState, subscribe };
}

/**
 * Renders a template function into a DOM element.
 * The template receives the current state and returns an HTML string.
 * @param {Function} template - (state) => htmlString
 * @param {HTMLElement} root - The DOM element to render into.
 * @returns {Function} A function to update the rendering with new state.
 */
export function render(template, root) {
  if (!root || !(root instanceof HTMLElement)) {
    throw new Error('render requires a valid HTMLElement as root');
  }

  /**
   * Update the DOM with the given state.
   * @param {Object} state - The state to render.
   */
  function update(state) {
    root.innerHTML = template(state);
  }

  return update;
}
