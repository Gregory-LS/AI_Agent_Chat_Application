/**
 * app.js - Minimal state management and rendering utilities.
 *
 * Provides:
 *   - createState(initialValue): reactive state container with get, set, and subscribe
 *   - render(elementId, template): renders a template string into a DOM element
 */

/**
 * Creates a reactive state container.
 *
 * @param {*} initialValue - The initial state value.
 * @returns {{ get: function, set: function, subscribe: function }} The state API.
 */
export function createState(initialValue) {
  let value = initialValue;
  const subscribers = new Set();

  return {
    /**
     * Returns the current state value.
     * @returns {*} Current value.
     */
    get() {
      return value;
    },
    /**
     * Updates the state to newValue and notifies all subscribers.
     * If the new value is identical to the current one (reference equality),
     * no update is performed.
     * @param {*} newValue - The new state value.
     */
    set(newValue) {
      if (value !== newValue) {
        value = newValue;
        subscribers.forEach((callback) => {
          try {
            callback(value);
          } catch (e) {
            console.error('State subscriber error:', e);
          }
        });
      }
    },
    /**
     * Subscribes a callback to state changes. The callback receives the new value.
     * @param {function} callback - Function to call on state change.
     * @returns {function} Unsubscribe function.
     */
    subscribe(callback) {
      subscribers.add(callback);
      return () => {
        subscribers.delete(callback);
      };
    },
  };
}

/**
 * Renders a template string into the innerHTML of the element with the given id.
 * Throws if the element is not found.
 *
 * @param {string} elementId - The id of the target DOM element.
 * @param {string} template - The HTML template string to render.
 * @throws {Error} If element with given id does not exist.
 */
export function render(elementId, template) {
  const element = document.getElementById(elementId);
  if (!element) {
    throw new Error(`Element with id "${elementId}" not found.`);
  }
  element.innerHTML = template;
}
