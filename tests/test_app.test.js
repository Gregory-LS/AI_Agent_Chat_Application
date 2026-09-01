import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { createStore, render } from '../static/app.js';

describe('createStore', () => {
  it('should initialize with given state', () => {
    const store = createStore({ count: 0 });
    expect(store.getState()).toEqual({ count: 0 });
  });

  it('should return a copy of state from getState', () => {
    const initialState = { items: [1, 2, 3] };
    const store = createStore(initialState);
    const state = store.getState();
    state.items.push(4);
    expect(store.getState()).toEqual({ items: [1, 2, 3] });
  });

  it('should update state with setState', () => {
    const store = createStore({ name: 'Alice', age: 30 });
    store.setState({ age: 31 });
    expect(store.getState()).toEqual({ name: 'Alice', age: 31 });
  });

  it('should throw if setState argument is not an object', () => {
    const store = createStore({});
    expect(() => store.setState(null)).toThrow('setState expects an object');
    expect(() => store.setState('string')).toThrow('setState expects an object');
    expect(() => store.setState(123)).toThrow('setState expects an object');
    expect(() => store.setState(undefined)).toThrow('setState expects an object');
  });

  it('should notify subscribers on state change', () => {
    const store = createStore({ count: 0 });
    const subscriber = vi.fn();
    store.subscribe(subscriber);
    store.setState({ count: 1 });
    expect(subscriber).toHaveBeenCalledTimes(1);
    expect(subscriber).toHaveBeenCalledWith({ count: 1 });
  });

  it('should not break on subscriber error', () => {
    const store = createStore({});
    const errorSub = vi.fn(() => { throw new Error('oops'); });
    const goodSub = vi.fn();
    store.subscribe(errorSub);
    store.subscribe(goodSub);
    expect(() => store.setState({ x: 1 })).not.toThrow();
    expect(goodSub).toHaveBeenCalledWith({ x: 1 });
  });

  it('should unsubscribe correctly', () => {
    const store = createStore({});
    const subscriber = vi.fn();
    const unsubscribe = store.subscribe(subscriber);
    unsubscribe();
    store.setState({ a: 1 });
    expect(subscriber).not.toHaveBeenCalled();
  });

  it('should throw if subscribe argument is not a function', () => {
    const store = createStore({});
    expect(() => store.subscribe(null)).toThrow('Subscriber must be a function');
    expect(() => store.subscribe('func')).toThrow('Subscriber must be a function');
  });

  it('should support multiple subscribers', () => {
    const store = createStore({});
    const sub1 = vi.fn();
    const sub2 = vi.fn();
    store.subscribe(sub1);
    store.subscribe(sub2);
    store.setState({ val: 42 });
    expect(sub1).toHaveBeenCalledWith({ val: 42 });
    expect(sub2).toHaveBeenCalledWith({ val: 42 });
  });
});

describe('render', () => {
  beforeEach(() => {
    document.body.innerHTML = '<div id="root"></div><div class="content"></div>';
  });

  afterEach(() => {
    document.body.innerHTML = '';
  });

  it('should set innerHTML of matching element', () => {
    render('#root', '<p>Hello</p>');
    expect(document.querySelector('#root').innerHTML).toBe('<p>Hello</p>');
  });

  it('should update elements with class selector', () => {
    render('.content', '<span>World</span>');
    expect(document.querySelector('.content').innerHTML).toBe('<span>World</span>');
  });

  it('should warn and silently return if element not found', () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    render('#nonexistent', 'anything');
    expect(warnSpy).toHaveBeenCalled();
    warnSpy.mockRestore();
  });
});
