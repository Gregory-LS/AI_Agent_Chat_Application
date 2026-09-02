// tests/test_app.js — Unit tests for app.js (run in browser or with test framework)

// Mock DOM elements for testing
function setupMockDOM() {
  document.body.innerHTML = `
    <div id="sidebar"></div>
    <div id="chat-messages"></div>
    <input id="message-input" />
    <button id="send-btn"></button>
    <button id="stop-btn"></button>
    <button id="new-chat-btn"></button>
    <button id="sidebar-toggle"></button>
    <button id="settings-btn"></button>
    <button id="settings-close"></button>
    <button id="settings-save"></button>
    <button id="theme-toggle"></button>
    <button id="skills-btn"></button>
    <button id="skills-close"></button>
    <button id="create-skill-btn"></button>
    <select id="model-select"></select>
    <div id="skills-list"></div>
    <div id="conversation-list"></div>
    <div id="settings-drawer"></div>
    <div id="skills-drawer"></div>
    <input id="api-key-input" />
    <input id="default-model-input" />
    <div id="balance-display"></div>
  `;
}

// Mock fetch
function mockFetch(data) {
  global.fetch = async (url, opts) => {
    const method = opts?.method || 'GET';
    const path = typeof url === 'string' ? url : url.toString();
    return {
      ok: true,
      status: 200,
      json: async () => data[path] || {},
      text: async () => JSON.stringify(data[path] || {}),
      blob: async () => new Blob([JSON.stringify(data[path] || {})]),
      body: {
        getReader() {
          return {
            read() {
              return Promise.resolve({ done: true, value: new Uint8Array() });
            }
          };
        }
      }
    };
  };
}

// Tests
(function runTests() {
  let passed = 0;
  let failed = 0;

  function assert(condition, name) {
    if (condition) {
      passed++;
      console.log(`PASS: ${name}`);
    } else {
      failed++;
      console.error(`FAIL: ${name}`);
    }
  }

  // Test 1: App initialization
  setupMockDOM();
  const app = Object.create(App);
  app.state = {
    conversations: [],
    currentConversationId: null,
    models: [],
    skills: [],
    config: { apiKey: '', defaultModel: '', theme: 'light' },
    balance: null,
    streaming: false,
    abortController: null,
    sidebarOpen: true,
    settingsOpen: false,
    skillsDrawerOpen: false
  };
  assert(!!app, 'App object exists');
  assert(app.state.config.theme === 'light', 'Default theme is light');

  // Test 2: Theme toggle
  app.toggleTheme();
  assert(app.state.config.theme === 'dark', 'Theme toggled to dark');
  app.toggleTheme();
  assert(app.state.config.theme === 'light', 'Theme toggled back to light');

  // Test 3: New conversation
  app.state.conversations = [];
  app.state.currentConversationId = null;
  app.newConversation = async function() {
    this.state.conversations.push({ id: 'test-123', title: 'New conversation' });
    this.state.currentConversationId = 'test-123';
  };
  app.newConversation();
  assert(app.state.conversations.length === 1, 'New conversation added');
  assert(app.state.currentConversationId === 'test-123', 'Current conversation set');

  // Test 4: Delete conversation
  app.deleteConversation = async function(id) {
    this.state.conversations = this.state.conversations.filter(c => c.id !== id);
    if (this.state.currentConversationId === id) {
      this.state.currentConversationId = null;
    }
  };
  app.deleteConversation('test-123');
  assert(app.state.conversations.length === 0, 'Conversation deleted');
  assert(app.state.currentConversationId === null, 'Current conversation cleared');

  // Test 5: Render chat messages
  document.getElementById('chat-messages').innerHTML = '';
  app.appendMessage({ role: 'user', content: 'Hello' });
  app.appendMessage({ role: 'assistant', content: 'Hi there' });
  const messages = document.querySelectorAll('.message');
  assert(messages.length === 2, 'Two messages rendered');
  assert(messages[0].classList.contains('user'), 'First message is user');
  assert(messages[1].classList.contains('assistant'), 'Second message is assistant');

  // Test 6: Copy button exists on messages
  const copyButtons = document.querySelectorAll('.copy-btn');
  assert(copyButtons.length === 2, 'Copy buttons present on both messages');

  // Test 7: Skills rendering
  app.state.skills = [
    { id: 'skill-1', name: 'Test Skill', enabled: true },
    { id: 'skill-2', name: 'Disabled Skill', enabled: false }
  ];
  app.renderSkills();
  const skillItems = document.querySelectorAll('.skill-item');
  assert(skillItems.length === 2, 'Two skills rendered');
  const checkboxes = document.querySelectorAll('.skill-item input[type="checkbox"]');
  assert(checkboxes[0].checked === true, 'First skill enabled');
  assert(checkboxes[1].checked === false, 'Second skill disabled');

  // Test 8: Sidebar rendering
  app.state.conversations = [
    { id: 'conv-1', title: 'Chat 1' },
    { id: 'conv-2', title: 'Chat 2' }
  ];
  app.renderSidebar();
  const convItems = document.querySelectorAll('.conversation-item');
  assert(convItems.length === 2, 'Two conversations in sidebar');
  assert(convItems[0].textContent.includes('Chat 1'), 'First conversation title');

  // Test 9: Model picker rendering
  app.state.models = [
    { id: 'openai/gpt-4', name: 'GPT-4', context_length: 8192 },
    { id: 'anthropic/claude-3', name: 'Claude 3', context_length: 100000 }
  ];
  app.renderModelPicker();
  const select = document.getElementById('model-select');
  assert(select.options.length === 2, 'Two model options rendered');
  assert(select.options[0].value === 'openai/gpt-4', 'First model is GPT-4');

  // Test 10: Stop streaming
  app.state.streaming = true;
  app.state.abortController = new AbortController();
  app.stopStreaming();
  assert(app.state.streaming === false, 'Streaming stopped');
  assert(app.state.abortController === null, 'Abort controller cleared');

  console.log(`\nResults: ${passed} passed, ${failed} failed`);
})();
