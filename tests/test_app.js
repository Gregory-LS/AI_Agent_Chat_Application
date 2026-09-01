import { createStore, render } from '../static/app.js';

/**
 * Tests for createStore
 */
describe('createStore', () => {
  test('getState returns initial state', () => {
    const store = createStore({ count: 0 });
    expect(store.getState()).toEqual({ count: 0 });
  });

  test('setState updates state', () => {
    const store = createStore({ count: 0 });
    store.setState({ count: 1 });
    expect(store.getState()).toEqual({ count: 1 });
  });

  test('setState merges partial state', () => {
    const store = createStore({ a: 1, b: 2 });
    store.setState({ b: 3 });
    expect(store.getState()).toEqual({ a: 1, b: 3 });
  });

  test('subscribe listener is called on setState', () => {
    const store = createStore({ count: 0 });
    const listener = jest.fn();
    store.subscribe(listener);
    store.setState({ count: 1 });
    expect(listener).toHaveBeenCalledWith({ count: 1 });
  });

  test('subscribe returns an unsubscribe function', () => {
    const store = createStore({ count: 0 });
    const listener = jest.fn();
    const unsubscribe = store.subscribe(listener);
    unsubscribe();
    store.setState({ count: 1 });
    expect(listener).not.toHaveBeenCalled();
  });

  test('multiple listeners are called', () => {
    const store = createStore({ count: 0 });
    const listener1 = jest.fn();
    const listener2 = jest.fn();
    store.subscribe(listener1);
    store.subscribe(listener2);
    store.setState({ count: 1 });
    expect(listener1).toHaveBeenCalled();
    expect(listener2).toHaveBeenCalled();
  });

  test('listeners receive the new state', () => {
    const store = createStore({ val: 'hello' });
    const listener = jest.fn();
    store.subscribe(listener);
    store.setState({ val: 'world' });
    expect(listener).toHaveBeenCalledWith({ val: 'world' });
  });
});

/**
 * Tests for render function
 */
describe('render', () => {
  let root;

  beforeEach(() => {
    root = document.createElement('div');
  });

  test('throws if root is not an HTMLElement', () => {
    expect(() => render(() => '', null)).toThrow();
    expect(() => render(() => '', 'not-element')).toThrow();
  });

  test('returns an update function', () => {
    const update = render(() => '<p>test</p>', root);
    expect(typeof update).toBe('function');
  });

  test('update sets innerHTML of root', () => {
    const update = render((state) => `<p>${state.text}</p>`, root);
    update({ text: 'hello' });
    expect(root.innerHTML).toBe('<p>hello</p>');
  });

  test('update can be called multiple times', () => {
    const update = render((state) => `<p>${state.count}</p>`, root);
    update({ count: 1 });
    expect(root.innerHTML).toBe('<p>1</p>');
    update({ count: 2 });
    expect(root.innerHTML).toBe('<p>2</p>');
  });
});
