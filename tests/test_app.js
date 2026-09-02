// ============================================================
// Unit tests for app.js — streaming fetch and state
// ============================================================

// Mock fetch and DOM for testing
let mockFetchCalls = [];
let mockEventListeners = {};

// Mock window
if (typeof window === 'undefined') {
  global.window = {
    dispatchEvent: (event) => {
      if (mockEventListeners[event.type]) {
        mockEventListeners[event.type].forEach(fn => fn(event));
      }
    },
    addEventListener: (type, fn) => {
      if (!mockEventListeners[type]) mockEventListeners[type] = [];
      mockEventListeners[type].push(fn);
    },
    removeEventListener: (type, fn) => {
      if (mockEventListeners[type]) {
        mockEventListeners[type] = mockEventListeners[type].filter(f => f !== fn);
      }
    },
  };
}

// Mock CustomEvent
if (typeof CustomEvent === 'undefined') {
  global.CustomEvent = class CustomEvent {
    constructor(type, options) {
      this.type = type;
      this.detail = options?.detail || {};
    }
  };
}

// Mock fetch
const originalFetch = global.fetch;
function mockFetch(responseBody, ok = true, status = 200) {
  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    start(controller) {
      const chunks = responseBody.split('\n').map(line => encoder.encode(line + '\n'));
      chunks.forEach(chunk => controller.enqueue(chunk));
      controller.close();
    }
  });
  global.fetch = async (url, options) => {
    mockFetchCalls.push({ url, options });
    return {
      ok,
      status,
      body: { getReader: () => stream.getReader() },
      text: async () => responseBody,
    };
  };
}

function resetMocks() {
  mockFetchCalls = [];
  mockEventListeners = {};
  global.fetch = originalFetch;
}

// Load the module (assumes app.js is in parent directory)
const { streamFetch, AppState } = require('../static/app.js');

// --- Tests ---

async function testStreamFetchSuccess() {
  console.log('Test: streamFetch success');
  const sseData = [
    'data: {"type":"chunk","content":"Hello"}',
    'data: {"type":"chunk","content":" world"}',
    'data: {"type":"usage","data":{"total_tokens":10}}',
    'data: {"type":"done"}',
  ].join('\n');
  mockFetch(sseData);

  const result = await streamFetch('test message', 'test-model', []);
  console.assert(result.content === 'Hello world', `Expected 'Hello world', got '${result.content}'`);
  console.assert(result.usage.total_tokens === 10, `Expected usage 10, got ${JSON.stringify(result.usage)}`);
  console.assert(mockFetchCalls.length === 1, 'Expected one fetch call');
  console.assert(mockFetchCalls[0].url === '/api/chat', `Expected /api/chat, got ${mockFetchCalls[0].url}`);
  console.assert(mockFetchCalls[0].options.method === 'POST', 'Expected POST method');
  const body = JSON.parse(mockFetchCalls[0].options.body);
  console.assert(body.messages.length === 1, 'Expected one message');
  console.assert(body.messages[0].role === 'user', 'Expected user role');
  console.assert(body.model === 'test-model', 'Expected test-model');
  console.log('  PASS');
}

async function testStreamFetchError() {
  console.log('Test: streamFetch error event');
  const sseData = 'data: {"type":"error","error":"Model not available"}\n';
  mockFetch(sseData);

  try {
    await streamFetch('test', 'test-model', []);
    console.assert(false, 'Expected error to be thrown');
  } catch (e) {
    console.assert(e.message === 'Model not available', `Expected 'Model not available', got '${e.message}'`);
    console.log('  PASS');
  }
}

async function testStreamFetchCancellation() {
  console.log('Test: streamFetch cancellation via AbortController');
  const controller = new AbortController();
  // Simulate a stream that never ends (to test abort)
  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    start(controller) {
      // Never close the stream
    }
  });
  global.fetch = async (url, options) => {
    mockFetchCalls.push({ url, options });
    return {
      ok: true,
      status: 200,
      body: { getReader: () => stream.getReader() },
      text: async () => '',
    };
  };

  setTimeout(() => controller.abort(), 10);

  try {
    await streamFetch('test', 'test-model', [], controller.signal);
    console.assert(false, 'Expected AbortError');
  } catch (e) {
    console.assert(e.name === 'AbortError', `Expected AbortError, got ${e.name}`);
    console.log('  PASS');
  }
}

async function testStreamFetchHTTPError() {
  console.log('Test: streamFetch HTTP error');
  global.fetch = async (url, options) => {
    mockFetchCalls.push({ url, options });
    return {
      ok: false,
      status: 500,
      body: null,
      text: async () => 'Internal Server Error',
    };
  };

  try {
    await streamFetch('test', 'test-model', []);
    console.assert(false, 'Expected error to be thrown');
  } catch (e) {
    console.assert(e.message.includes('500'), `Expected 500 error, got '${e.message}'`);
    console.log('  PASS');
  }
}

async function testStreamFetchChunkEvent() {
  console.log('Test: streamFetch dispatches chat-chunk events');
  let chunkReceived = '';
  const handler = (e) => { chunkReceived += e.detail.content; };
  window.addEventListener('chat-chunk', handler);

  const sseData = [
    'data: {"type":"chunk","content":"Hello"}',
    'data: {"type":"chunk","content":" world"}',
    'data: {"type":"done"}',
  ].join('\n');
  mockFetch(sseData);

  await streamFetch('test', 'test-model', []);
  console.assert(chunkReceived === 'Hello world', `Expected 'Hello world', got '${chunkReceived}'`);
  window.removeEventListener('chat-chunk', handler);
  console.log('  PASS');
}

// --- Run All Tests ---
(async () => {
  console.log('Running streaming fetch tests...\n');
  await testStreamFetchSuccess();
  resetMocks();
  await testStreamFetchError();
  resetMocks();
  await testStreamFetchCancellation();
  resetMocks();
  await testStreamFetchHTTPError();
  resetMocks();
  await testStreamFetchChunkEvent();
  resetMocks();
  console.log('\nAll tests completed.');
})();
