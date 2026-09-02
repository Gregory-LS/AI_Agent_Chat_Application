// app.js — Agentic Chat frontend

const state = {
  conversations: [],
  currentConvId: null,
  models: [],
  config: {},
  skills: [],
  theme: 'light',
  apiKey: localStorage.getItem('openrouter_api_key') || '',
  abortController: null,
  streaming: false,
};

// Helper: fetch with auth header
function authedFetch(url, options = {}) {
  const headers = options.headers || {};
  if (state.apiKey) {
    headers['X-API-Key'] = state.apiKey;
  }
  return fetch(url, { ...options, headers });
}

// Initialize
async function init() {
  const savedKey = localStorage.getItem('openrouter_api_key');
  if (savedKey) {
    state.apiKey = savedKey;
  }
  loadTheme();
  await loadConfig();
  await loadSkills();
  await loadConversations();
  await loadModels();
  renderUI();
  bindEvents();
  if (state.conversations.length > 0) {
    selectConversation(state.conversations[0].id);
  }
}

function loadTheme() {
  const t = localStorage.getItem('theme') || 'light';
  state.theme = t;
  document.documentElement.setAttribute('data-theme', t);
}

async function loadConfig() {
  try {
    const res = await authedFetch('/api/config');
    if (res.ok) {
      state.config = await res.json();
      if (state.config.api_key && !state.apiKey) {
        state.apiKey = state.config.api_key;
        localStorage.setItem('openrouter_api_key', state.apiKey);
      }
    }
  } catch (e) {
    console.warn('Failed to load config', e);
  }
}

async function saveConfig() {
  await authedFetch('/api/config', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(state.config),
  });
}

async function loadConversations() {
  try {
    const res = await authedFetch('/api/conversations');
    if (res.ok) state.conversations = await res.json();
  } catch (e) { console.warn('Failed loadConversations', e); }
}

async function loadModels() {
  try {
    const res = await authedFetch('/api/models');
    if (res.ok) state.models = await res.json();
  } catch (e) { console.warn('Failed loadModels', e); }
}

async function loadSkills() {
  try {
    const res = await authedFetch('/api/skills');
    if (res.ok) state.skills = await res.json();
  } catch (e) { console.warn('Failed loadSkills', e); }
}

function renderUI() {
  renderConversations();
  renderModelPicker();
  updateModelIndicator();
  updateSendButton();
}

function renderConversations() {
  const list = document.getElementById('conversation-list');
  list.innerHTML = '';
  state.conversations.forEach(conv => {
    const div = document.createElement('div');
    div.className = 'conversation-item' + (conv.id === state.currentConvId ? ' active' : '');
    div.dataset.id = conv.id;
    div.textContent = conv.title || 'Untitled';
    div.addEventListener('click', () => selectConversation(conv.id));
    list.appendChild(div);
  });
}

function selectConversation(id) {
  state.currentConvId = id;
  renderConversations();
  loadMessages(id);
}

async function loadMessages(id) {
  try {
    const res = await authedFetch('/api/conversations/' + id);
    if (res.ok) {
      const conv = await res.json();
      renderMessages(conv.messages || []);
    }
  } catch (e) { console.warn('Failed loadMessages', e); }
}

function renderMessages(messages) {
  const container = document.getElementById('messages');
  container.innerHTML = '';
  messages.forEach(msg => {
    const div = document.createElement('div');
    div.className = 'message ' + msg.role;
    div.textContent = msg.content;
    container.appendChild(div);
  });
  container.scrollTop = container.scrollHeight;
}

function renderModelPicker() {
  const select = document.getElementById('default-model-select');
  select.innerHTML = '';
  state.models.forEach(m => {
    const opt = document.createElement('option');
    opt.value = m.id;
    opt.textContent = m.name || m.id;
    if (m.id === state.config.default_model) opt.selected = true;
    select.appendChild(opt);
  });
}

function updateModelIndicator() {
  const el = document.getElementById('model-indicator');
  const current = state.config.default_model || state.models[0]?.id || 'None';
  el.textContent = 'Model: ' + current;
}

function updateSendButton() {
  const btn = document.getElementById('send-btn');
  btn.disabled = !state.apiKey || state.streaming || !state.currentConvId;
}

function bindEvents() {
  // New conversation
  document.getElementById('new-chat').addEventListener('click', async () => {
    const res = await authedFetch('/api/conversations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: 'New Chat' }),
    });
    if (res.ok) {
      const conv = await res.json();
      state.conversations.unshift(conv);
      selectConversation(conv.id);
    }
  });

  // Settings
  document.getElementById('settings-btn').addEventListener('click', () => {
    document.getElementById('settings-drawer').classList.remove('hidden');
    document.getElementById('api-key-input').value = state.apiKey;
    document.getElementById('theme-select').value = state.theme;
  });

  document.getElementById('close-settings').addEventListener('click', () => {
    document.getElementById('settings-drawer').classList.add('hidden');
  });

  document.getElementById('save-settings').addEventListener('click', async () => {
    const apiKey = document.getElementById('api-key-input').value.trim();
    const theme = document.getElementById('theme-select').value;
    state.apiKey = apiKey;
    localStorage.setItem('openrouter_api_key', apiKey);
    state.config.api_key = apiKey;
    state.config.default_model = document.getElementById('default-model-select').value;
    state.theme = theme;
    localStorage.setItem('theme', theme);
    document.documentElement.setAttribute('data-theme', theme);
    await saveConfig();
    updateSendButton();
    document.getElementById('settings-drawer').classList.add('hidden');
  });

  // Logout button
  document.getElementById('logout-btn').addEventListener('click', async () => {
    // Clear API key from local storage and state
    localStorage.removeItem('openrouter_api_key');
    state.apiKey = '';
    state.config.api_key = '';
    // Clear conversations and messages
    state.conversations = [];
    state.currentConvId = null;
    renderConversations();
    renderMessages([]);
    updateSendButton();
    updateModelIndicator();
    // Also clear config on server side
    await saveConfig();
  });

  // Send / stop
  document.getElementById('send-btn').addEventListener('click', sendMessage);
  document.getElementById('stop-btn').addEventListener('click', stopStream);

  // Keyboard shortcuts
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      const active = document.activeElement;
      if (active && active.id === 'composer-input') {
        e.preventDefault();
        sendMessage();
      }
    }
    if (e.key === 'Escape') {
      document.getElementById('settings-drawer').classList.add('hidden');
      document.getElementById('model-picker-modal').classList.add('hidden');
    }
  });

  // Auto-resize textarea
  const textarea = document.getElementById('composer-input');
  textarea.addEventListener('input', () => {
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
  });
}

async function sendMessage() {
  if (!state.apiKey || state.streaming || !state.currentConvId) return;
  const input = document.getElementById('composer-input');
  const text = input.value.trim();
  if (!text) return;

  input.value = '';
  input.style.height = 'auto';

  // Add user message immediately
  const messagesContainer = document.getElementById('messages');
  const userDiv = document.createElement('div');
  userDiv.className = 'message user';
  userDiv.textContent = text;
  messagesContainer.appendChild(userDiv);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;

  // Start streaming
  state.streaming = true;
  state.abortController = new AbortController();
  document.getElementById('send-btn').disabled = true;
  document.getElementById('stop-btn').style.display = 'inline-block';

  const assistantDiv = document.createElement('div');
  assistantDiv.className = 'message assistant';
  assistantDiv.textContent = '';
  messagesContainer.appendChild(assistantDiv);

  try {
    const res = await authedFetch('/api/chat', {
      method: 'POST',
      signal: state.abortController.signal,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        conversation_id: state.currentConvId,
        message: text,
        model: state.config.default_model || undefined,
      }),
    });

    if (!res.ok) {
      assistantDiv.textContent = 'Error: ' + (await res.text());
      state.streaming = false;
      document.getElementById('send-btn').disabled = false;
      document.getElementById('stop-btn').style.display = 'none';
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop(); // keep incomplete line

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data === '[DONE]') {
            // stream finished
            break;
          }
          try {
            const parsed = JSON.parse(data);
            if (parsed.type === 'chunk') {
              assistantDiv.textContent += parsed.content;
              messagesContainer.scrollTop = messagesContainer.scrollHeight;
            } else if (parsed.type === 'done') {
              // finished
            } else if (parsed.type === 'error') {
              assistantDiv.textContent = 'Error: ' + parsed.content;
            }
          } catch (e) {
            // ignore malformed
          }
        }
      }
    }
  } catch (e) {
    if (e.name !== 'AbortError') {
      assistantDiv.textContent = 'Error: ' + e.message;
    }
  }

  state.streaming = false;
  state.abortController = null;
  document.getElementById('send-btn').disabled = false;
  document.getElementById('stop-btn').style.display = 'none';
}

function stopStream() {
  if (state.abortController) {
    state.abortController.abort();
  }
}

// Init on DOM ready
document.addEventListener('DOMContentLoaded', init);
