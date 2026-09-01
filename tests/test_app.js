const assert = require('assert');
const { createStore, render } = require('../static/app');

describe('createStore', function() {
  it('should create a store with initial state', function() {
    const store = createStore({ count: 0 });
    assert.deepStrictEqual(store.getState(), { count: 0 });
  });

  it('should update state with setState', function() {
    const store = createStore({ count: 0 });
    store.setState({ count: 1 });
    assert.deepStrictEqual(store.getState(), { count: 1 });
  });

  it('should merge state with setState', function() {
    const store = createStore({ a: 1, b: 2 });
    store.setState({ b: 3 });
    assert.deepStrictEqual(store.getState(), { a: 1, b: 3 });
  });

  it('should notify subscribers on state change', function() {
    const store = createStore({ count: 0 });
    let notified = false;
    store.subscribe((newState) => {
      notified = true;
      assert.strictEqual(newState.count, 1);
    });
    store.setState({ count: 1 });
    assert.ok(notified);
  });

  it('should not notify after unsubscribe', function() {
    const store = createStore({ count: 0 });
    let callCount = 0;
    const unsubscribe = store.subscribe(() => { callCount++; });
    unsubscribe();
    store.setState({ count: 1 });
    assert.strictEqual(callCount, 0);
  });
});

describe('render', function() {
  it('should render initial state and update on change', function() {
    const store = createStore({ count: 0 });
    const root = { innerHTML: '' };
    const renderFn = (state) => `<p>${state.count}</p>`;
    const unsubscribe = render(store, root, renderFn);
    assert.strictEqual(root.innerHTML, '<p>0</p>');
    store.setState({ count: 5 });
    assert.strictEqual(root.innerHTML, '<p>5</p>');
    unsubscribe();
  });

  it('should return unsubscribe function', function() {
    const store = createStore();
    const root = { innerHTML: '' };
    const unsub = render(store, root, () => '');
    assert.strictEqual(typeof unsub, 'function');
  });
});
