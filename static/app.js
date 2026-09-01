/**
 * Simple state management and rendering utility.
 * @module app
 */

/**
 * Creates a store with a given initial state.
 * @param {Object} initialState - The initial state object.
 * @returns {Object} Store with methods: getState, setState, subscribe.
 */
function createStore(initialState = {}) {
  let state = { ...initialState };
  const listeners = [];

  /**
   * Returns the current state.
   * @returns {Object}
   */
  function getState() {
    return state;
  }

  /**
   * Updates the state by merging the provided partial state.
   * Notifies all subscribed listeners after the update.
   * @param {Object} partialState - Object with properties to merge.
   */
  function setState(partialState) {
    state = { ...state, ...partialState };
    listeners.forEach(listener => listener(state));
  }

  /**
   * Subscribes a listener function that is called whenever the state changes.
   * @param {Function} listener - Callback receiving the new state.
   * @returns {Function} Unsubscribe function.
   */
  function subscribe(listener) {
    listeners.push(listener);
    return () => {
      const index = listeners.indexOf(listener);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    };
  }

  return {
    getState,
    setState,
    subscribe
  };
}

/**
 * Renders the view based on the store's state and keeps it updated.
 * @param {Object} store - The store object (from createStore).
 * @param {HTMLElement} root - The DOM element to render into.
 * @param {Function} renderFn - Function that receives state and returns HTML string.
 * @returns {Function} Unsubscribe function.
 */
function render(store, root, renderFn) {
  function update() {
    root.innerHTML = renderFn(store.getState());
  }
  update();
  return store.subscribe(update);
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { createStore, render };
}
