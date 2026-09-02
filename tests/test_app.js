/**
 * Tests for app.js chat state management functions.
 * Run in browser (test_app.html) or with a headless browser.
 */

// Mock fetch for testing
const originalFetch = window.fetch;
let fetchMock;

function setupFetchMock() {
  fetchMock = {
    calls: [],
    responses: {}
  };
  window.fetch = async (url, options = {}) => {
    fetchMock.calls.push({ url, options });
    const key = `${options.method || 'GET'} ${url}`;
    const response = fetchMock.responses[key];
    if (response) {
      return {
        ok: response.ok !== false,
        status: response.status || 200,
        json: async () => response.data,
        text: async () => response.text || JSON.stringify(response.data),
        blob: async () => new Blob([response.text || JSON.stringify(response.data)])
      };
    }
    return {
      ok: false,
      status: 404,
      json: async () => ({ error: 'Not found' }),
      text: async () => 'Not found'
    };
  };
}

function teardownFetchMock() {
  window.fetch = originalFetch;
}

// Tests
async function testLoadConversations() {
  setupFetchMock();
  fetchMock.responses['GET /api/conversations'] = {
    data: [
      { id: '1', title: 'Test 1', messages: [], updatedAt: '2024-01-01T00:00:00Z' },
      { id: '2', title: 'Test 2', messages: [], updatedAt: '2024-01-02T00:00:00Z' }
    ]
  };
  
  state.conversations = [];
  await loadConversations();
  
  console.assert(state.conversations.length === 2, 'loadConversations: should load 2 conversations');
  console.assert(state.conversations[0].id === '1', 'loadConversations: first conversation id should be 1');
  
  teardownFetchMock();
  console.log('✓ testLoadConversations passed');
}

async function testCreateConversation() {
  setupFetchMock();
  fetchMock.responses['POST /api/conversations'] = { data: {} };
  fetchMock.responses['GET /api/conversations'] = { data: [] };
  
  state.conversations = [];
  state.currentConversationId = null;
  state.messages = [];
  
  const conv = await createConversation();
  
  console.assert(conv.id !== undefined, 'createConversation: should return a conversation with id');
  console.assert(conv.title === 'New conversation', 'createConversation: title should be New conversation');
  console.assert(state.currentConversationId === conv.id, 'createConversation: should set currentConversationId');
  console.assert(state.conversations.length === 1, 'createConversation: should add to conversations list');
  
  teardownFetchMock();
  console.log('✓ testCreateConversation passed');
}

async function testLoadConversation() {
  setupFetchMock();
  fetchMock.responses['GET /api/conversations/1'] = {
    data: {
      id: '1',
      title: 'Test',
      messages: [
        { id: 'm1', role: 'user', content: 'Hello', timestamp: '2024-01-01T00:00:00Z' },
        { id: 'm2', role: 'assistant', content: 'Hi', timestamp: '2024-01-01T00:00:01Z' }
      ],
      model: 'gpt-3.5-turbo'
    }
  };
  
  state.currentConversationId = null;
  state.messages = [];
  state.selectedModel = null;
  
  await loadConversation('1');
  
  console.assert(state.currentConversationId === '1', 'loadConversation: should set currentConversationId');
  console.assert(state.messages.length === 2, 'loadConversation: should load 2 messages');
  console.assert(state.messages[0].role === 'user', 'loadConversation: first message should be from user');
  console.assert(state.selectedModel === 'gpt-3.5-turbo', 'loadConversation: should set selectedModel');
  
  teardownFetchMock();
  console.log('✓ testLoadConversation passed');
}

async function testDeleteConversation() {
  setupFetchMock();
  fetchMock.responses['DELETE /api/conversations/1'] = { data: {} };
  
  state.conversations = [
    { id: '1', title: 'Test' },
    { id: '2', title: 'Test 2' }
  ];
  state.currentConversationId = '1';
  state.messages = [{ role: 'user', content: 'test' }];
  
  await deleteConversation('1');
  
  console.assert(state.conversations.length === 1, 'deleteConversation: should remove conversation');
  console.assert(state.conversations[0].id === '2', 'deleteConversation: remaining conversation should be id 2');
  console.assert(state.currentConversationId === null, 'deleteConversation: should clear currentConversationId if deleted');
  console.assert(state.messages.length === 0, 'deleteConversation: should clear messages');
  
  teardownFetchMock();
  console.log('✓ testDeleteConversation passed');
}

async function testRenameConversation() {
  setupFetchMock();
  fetchMock.responses['PATCH /api/conversations/1'] = { data: {} };
  
  state.conversations = [{ id: '1', title: 'Old title' }];
  
  await renameConversation('1', 'New title');
  
  console.assert(state.conversations[0].title === 'New title', 'renameConversation: should update title');
  
  teardownFetchMock();
  console.log('✓ testRenameConversation passed');
}

function testAddMessage() {
  state.messages = [];
  const msg = addMessage('user', 'Hello');
  
  console.assert(state.messages.length === 1, 'addMessage: should add one message');
  console.assert(state.messages[0].role === 'user', 'addMessage: role should be user');
  console.assert(state.messages[0].content === 'Hello', 'addMessage: content should be Hello');
  console.assert(msg.id !== undefined, 'addMessage: should return message with id');
  
  console.log('✓ testAddMessage passed');
}

function testUpdateLastMessage() {
  state.messages = [
    { id: '1', role: 'user', content: 'Hello' },
    { id: '2', role: 'assistant', content: 'Hi' }
  ];
  
  updateLastMessage('Hi there');
  
  console.assert(state.messages[1].content === 'Hi there', 'updateLastMessage: should update last message content');
  
  console.log('✓ testUpdateLastMessage passed');
}

function testClearMessages() {
  state.messages = [{ id: '1', role: 'user', content: 'Hello' }];
  clearMessages();
  console.assert(state.messages.length === 0, 'clearMessages: should clear all messages');
  console.log('✓ testClearMessages passed');
}

function testToggleSkill() {
  state.activeSkills = ['skill1'];
  
  toggleSkill('skill2');
  console.assert(state.activeSkills.length === 2, 'toggleSkill: should add skill2');
  console.assert(state.activeSkills.includes('skill2'), 'toggleSkill: skill2 should be in activeSkills');
  
  toggleSkill('skill1');
  console.assert(state.activeSkills.length === 1, 'toggleSkill: should remove skill1');
  console.assert(!state.activeSkills.includes('skill1'), 'toggleSkill: skill1 should not be in activeSkills');
  
  console.log('✓ testToggleSkill passed');
}

function testEscapeHtml() {
  console.assert(escapeHtml('<script>') === '&lt;script&gt;', 'escapeHtml: should escape < and >');
  console.assert(escapeHtml('"&")') === '&quot;&amp;&quot;)', 'escapeHtml: should escape quotes and &');
  console.log('✓ testEscapeHtml passed');
}

function testFormatDate() {
  const result = formatDate('2024-01-15T12:30:00Z');
  console.assert(result.includes('2024'), 'formatDate: should include year');
  console.log('✓ testFormatDate passed');
}

function testRenderMarkdown() {
  const result = renderMarkdown('**bold** and *italic* and `code`');
  console.assert(result.includes('<strong>bold</strong>'), 'renderMarkdown: should render bold');
  console.assert(result.includes('<em>italic</em>'), 'renderMarkdown: should render italic');
  console.assert(result.includes('<code>code</code>'), 'renderMarkdown: should render inline code');
  console.log('✓ testRenderMarkdown passed');
}

// Run all tests
document.addEventListener('DOMContentLoaded', async () => {
  console.log('Running app.js tests...');
  
  // Need to initialize state and dom for tests
  // We'll manually set up minimal state
  
  try {
    await testLoadConversations();
    await testCreateConversation();
    await testLoadConversation();
    await testDeleteConversation();
    await testRenameConversation();
    testAddMessage();
    testUpdateLastMessage();
    testClearMessages();
    testToggleSkill();
    testEscapeHtml();
    testFormatDate();
    testRenderMarkdown();
    
    console.log('\nAll tests passed! ✅');
  } catch (err) {
    console.error('Test failed:', err);
  }
});
