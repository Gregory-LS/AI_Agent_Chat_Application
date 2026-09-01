/**
 * Unit tests for app.js using a minimal assertion framework (compatible with Node or browser).
 * Run with a test runner like Mocha or QUnit, or simply import and run in a browser.
 */

import { createState, render } from '../static/app.js';

let passed = 0;
let failed = 0;

function assert(condition, message) {
  if (condition) {
    passed++;
    console.log(`PASS: ${message}`);
  } else {
    failed++;
    console.error(`FAIL: ${message}`);
  }
}

function assertEqual(actual, expected, message) {
  if (actual === expected) {
    passed++;
    console.log(`PASS: ${message}`);
  } else {
    failed++;
    console.error(`FAIL: ${message} — expected ${expected}, got ${actual}`);
  }
}

// ---------- Tests for createState ----------

// Basic get/set
const state1 = createState(10);
assertEqual(state1.get(), 10, 'createState(10) initial value should be 10');
state1.set(20);
assertEqual(state1.get(), 20, 'After set(20), get() should be 20');

// Subscriber notification
const state2 = createState('hello');
let receivedValue = null;
const unsubscribe = state2.subscribe((val) => {
  receivedValue = val;
});
state2.set('world');
assertEqual(receivedValue, 'world', 'Subscriber should receive new value on set');

// Unsubscribe
receivedValue = null;
unsubscribe();
state2.set('foo');
assertEqual(receivedValue, null, 'After unsubscribe, subscriber should not be called');

// Multiple subscribers
const state3 = createState(0);
let count1 = 0;
let count2 = 0;
state3.subscribe(() => count1++);
state3.subscribe(() => count2++);
state3.set(1);
assertEqual(count1, 1, 'First subscriber called once after set');
assertEqual(count2, 1, 'Second subscriber called once after set');

// No update if same reference
const state4 = createState({ a: 1 });
let callCount = 0;
state4.subscribe(() => callCount++);
state4.set({ a: 1 }); // different object – should trigger
assertEqual(callCount, 1, 'Setting a new object with same content should trigger update');
callCount = 0;
state4.set(state4.get()); // same reference – should not trigger
assertEqual(callCount, 0, 'Setting the exact same reference should not trigger update');

// ---------- Tests for render ----------

// Mock document for testing
const mockElement = { innerHTML: '' };
const originalGetElementById = document.getElementById;
document.getElementById = (id) => {
  if (id === 'test-root') {
    return mockElement;
  }
  return null;
};

// Render to existing element
try {
  render('test-root', '<p>Hello</p>');
  assertEqual(mockElement.innerHTML, '<p>Hello</p>', 'render should set innerHTML correctly');
} catch (e) {
  assert(false, 'render to existing element should not throw');
}

// Render to non-existing element
try {
  render('non-existent', 'anything');
  assert(false, 'render should throw if element not found');
} catch (e) {
  assert(true, 'render throws when element not found');
}

// Restore mock
document.getElementById = originalGetElementById;

// ---------- Summary ----------
console.log(`\n${passed} passed, ${failed} failed`);
if (failed > 0) {
  process.exit(1);
}
