// app.js — Agentic Chat frontend
// State
let state = {
  config: {},
  conversations: [],
  currentConversationId: null,
  skills: [],
  models: [],
  theme: 'light'
};

// DOM references
const $ = (id) => document.getElementById(id);
const sidebar = $('sidebar');
const newChatBtn = $('new-chat-btn');
const settingsBtn = $('settings-btn');
const skillsBtn = $('skills-btn');
const conversationList = $('conversations');
const searchInput = $('search-conversations');
const clearBtn = $('clear-conversations-btn');
const messagesEl = $('messages');
const messageInput = $('message-input');
const sendBtn = $('send-btn');
const attachBtn = $('attach-btn');
const modelPickerBtn = $('model-picker-btn');
const modelNameEl = $('model-name');
const stopBtn = $('stop-btn');
const overlay = $('overlay');
const settingsDrawer = $('settings-drawer');
const settingsCloseBtn = $('settings-close-btn');
const apiKeyInput = $('api-key-input');
const defaultModelInput = $('default-model-input');
const themeSelect = $('theme-select');
const saveSettingsBtn = $('save-settings-btn');
const logoutBtn = $('logout-btn');
const balanceInfo = $('balance-info');
const skillsDrawer = $('skills-drawer');
const skillsCloseBtn = $('skills-close-btn');
const skillsList = $('skills-list');
const addSkillBtn = $('add-skill-btn');
const modelPickerDrawer = $('model-picker-drawer');
const modelPickerCloseBtn = $('model-picker-close-btn');
const modelSearch = $('model-search');
const modelList = $('model-list');
const chatHeader = $('chat-header');

// Settings Modal references
const settingsModal = $('settings-modal');
const settingsModalClose = $('settings-modal-close');
const modalApiKey = $('modal-api-key');
const modalDefaultModel = $('modal-default-model');
const modalTheme = $('modal-theme');
const modalSaveSettings = $('modal-save-settings');

// Fetch helpers
async function api(method, path, body) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body) opts.body = JSON.stringify(body);
  const resp = await fetch(path, opts);
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ error: resp.statusText }));
    throw new Error(err.error || 'Request failed');
  }
  return resp.json();
}

// Config
async function loadConfig() {
  state.config = await api('GET', '/api/config');
  apiKeyInput.value = state.config.api_key || '';
  defaultModelInput.value = state.config.default_model || '';
  themeSelect.value = state.config.theme || 'light';
  state.theme = state.config.theme || 'light';
  applyTheme(state.theme);
}

async function saveConfig(updates) {
  const newConfig = await api('POST', '/api/config', updates);
  state.config = newConfig;
  apiKeyInput.value = newConfig.api_key || '';
  defaultModelInput.value = newConfig.default_model || '';
  themeSelect.value = newConfig.theme || 'light';
  state.theme = newConfig.theme || 'light';
  applyTheme(state.theme);
}

// Theme
function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('theme', theme);
}

// Conversations
async function loadConversations() {
  state.conversations = await api('GET', '/api/conversations');
  renderConversations();
}

async function createConversation() {
  const conv = await api('POST', '/api/conversations', { title: 'New conversation', messages: [] });
  state.conversations.unshift(conv);
  state.currentConversationId = conv.id;
  renderConversations();
  selectConversation(conv.id);
}

async function deleteConversation(id) {
  await api('DELETE', `/api/conversations/${id}`);
  state.conversations = state.conversations.filter(c => c.id !== id);
  if (state.currentConversationId === id) {
    state.currentConversationId = null;
    messagesEl.innerHTML = '';
  }
  renderConversations();
}

async function clearConversations() {
  for (const c of state.conversations) {
    await api('DELETE', `/api/conversations/${c.id}`);
  }
  state.conversations = [];
  state.currentConversationId = null;
  messagesEl.innerHTML = '';
  renderConversations();
}

function renderConversations() {
  const query = searchInput.value.toLowerCase();
  const filtered = state.conversations.filter(c => c.title.toLowerCase().includes(query));
  conversationList.innerHTML = filtered.map(c => `
    <div class="conversation-item ${c.id === state.currentConversationId ? 'active' : ''}" data-id="${c.id}">
      <span class="conv-title">${escapeHtml(c.title)}</span>
      <button class="delete-conv-btn" data-id="${c.id}">&times;</button>
    </div>
  `).join('');
  document.querySelectorAll('.conversation-item').forEach(el => {
    el.addEventListener('click', (e) => {
      if (e.target.classList.contains('delete-conv-btn')) return;
      selectConversation(el.dataset.id);
    });
  });
  document.querySelectorAll('.delete-conv-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      deleteConversation(btn.dataset.id);
    });
  });
}

function selectConversation(id) {
  state.currentConversationId = id;
  const conv = state.conversations.find(c => c.id === id);
  if (conv) {
    messagesEl.innerHTML = conv.messages.map(m => renderMessage(m)).join('');
    modelNameEl.textContent = conv.model || 'No model';
  }
  renderConversations();
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function renderMessage(msg) {
  const role = msg.role === 'assistant' ? 'assistant' : 'user';
  return `<div class="message ${role}"><div class="message-content">${escapeHtml(msg.content)}</div></div>`;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Settings Drawer
function openSettings() {
  settingsDrawer.classList.remove('hidden');
  overlay.classList.remove('hidden');
}

function closeSettings() {
  settingsDrawer.classList.add('hidden');
  overlay.classList.add('hidden');
}

// Skills Drawer
function openSkills() {
  skillsDrawer.classList.remove('hidden');
  overlay.classList.remove('hidden');
  loadSkills();
}

function closeSkills() {
  skillsDrawer.classList.add('hidden');
  overlay.classList.add('hidden');
}

async function loadSkills() {
  state.skills = await api('GET', '/api/skills');
  renderSkills();
}

function renderSkills() {
  skillsList.innerHTML = state.skills.map(s => `
    <div class="skill-item" data-id="${s.id}">
      <span>${escapeHtml(s.name)}</span>
      <label class="switch">
        <input type="checkbox" ${s.enabled ? 'checked' : ''} data-id="${s.id}">
        <span class="slider"></span>
      </label>
    </div>
  `).join('');
  skillsList.querySelectorAll('input[type="checkbox"]').forEach(cb => {
    cb.addEventListener('change', async () => {
      const skill = state.skills.find(s => s.id === cb.dataset.id);
      if (skill) {
        skill.enabled = cb.checked;
        await api('PATCH', `/api/skills/${skill.id}`, { enabled: skill.enabled });
      }
    });
  });
}

// Model Picker
async function loadModels() {
  state.models = await api('GET', '/api/models');
  renderModels();
}

function openModelPicker() {
  modelPickerDrawer.classList.remove('hidden');
  overlay.classList.remove('hidden');
  loadModels();
}

function closeModelPicker() {
  modelPickerDrawer.classList.add('hidden');
  overlay.classList.add('hidden');
}

function renderModels() {
  const query = modelSearch.value.toLowerCase();
  const filtered = state.models.filter(m => m.id.toLowerCase().includes(query));
  modelList.innerHTML = filtered.map(m => `
    <div class="model-item" data-id="${m.id}">
      <strong>${escapeHtml(m.id)}</strong>
      <span class="model-provider">${escapeHtml(m.provider || '')}</span>
      <span class="model-context">${m.context_length || '?'}</span>
    </div>
  `).join('');
  modelList.querySelectorAll('.model-item').forEach(el => {
    el.addEventListener('click', () => {
      selectModel(el.dataset.id);
    });
  });
}

function selectModel(modelId) {
  modelNameEl.textContent = modelId;
  closeModelPicker();
  if (state.currentConversationId) {
    const conv = state.conversations.find(c => c.id === state.currentConversationId);
    if (conv) {
      conv.model = modelId;
      api('PATCH', `/api/conversations/${conv.id}`, { model: modelId });
    }
  }
}

// Balance
async function loadBalance() {
  try {
    const balance = await api('GET', '/api/balance');
    balanceInfo.innerHTML = `Balance: ${balance.credits} credits (used: ${balance.usage}, total: ${balance.total})`;
  } catch (e) {
    balanceInfo.innerHTML = 'Failed to load balance';
  }
}

// Chat
let abortController = null;

async function sendMessage() {
  const text = messageInput.value.trim();
  if (!text) return;
  if (!state.currentConversationId) {
    await createConversation();
  }
  const conv = state.conversations.find(c => c.id === state.currentConversationId);
  if (!conv) return;
  
  const userMsg = { role: 'user', content: text };
  conv.messages.push(userMsg);
  messagesEl.insertAdjacentHTML('beforeend', renderMessage(userMsg));
  messageInput.value = '';
  messagesEl.scrollTop = messagesEl.scrollHeight;
  
  // Save conversation
  await api('PATCH', `/api/conversations/${conv.id}`, { messages: conv.messages });
  
  // Send to API
  abortController = new AbortController();
  stopBtn.classList.remove('hidden');
  
  try {
    const resp = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: conv.model || state.config.default_model, messages: conv.messages }),
      signal: abortController.signal
    });
    
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ error: 'Request failed' }));
      throw new Error(err.error || 'Request failed');
    }
    
    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let assistantContent = '';
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n');
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data === '[DONE]') continue;
          try {
            const parsed = JSON.parse(data);
            if (parsed.type === 'chunk') {
              assistantContent += parsed.content || '';
              // Update last assistant message
              let lastMsg = conv.messages[conv.messages.length - 1];
              if (!lastMsg || lastMsg.role !== 'assistant') {
                lastMsg = { role: 'assistant', content: '' };
                conv.messages.push(lastMsg);
                messagesEl.insertAdjacentHTML('beforeend', renderMessage(lastMsg));
              }
              lastMsg.content = assistantContent;
              const msgEls = messagesEl.querySelectorAll('.message.assistant');
              if (msgEls.length > 0) {
                msgEls[msgEls.length - 1].querySelector('.message-content').textContent = assistantContent;
              }
              messagesEl.scrollTop = messagesEl.scrollHeight;
            } else if (parsed.type === 'error') {
              throw new Error(parsed.error);
            }
          } catch (e) {
            // ignore parse errors for incomplete chunks
          }
        }
      }
    }
    
    // Save final conversation
    await api('PATCH', `/api/conversations/${conv.id}`, { messages: conv.messages });
  } catch (e) {
    if (e.name !== 'AbortError') {
      const errMsg = { role: 'assistant', content: `Error: ${e.message}` };
      conv.messages.push(errMsg);
      messagesEl.insertAdjacentHTML('beforeend', renderMessage(errMsg));
      await api('PATCH', `/api/conversations/${conv.id}`, { messages: conv.messages });
    }
  } finally {
    stopBtn.classList.add('hidden');
    abortController = null;
  }
}

function stopGeneration() {
  if (abortController) {
    abortController.abort();
  }
}

// Settings Modal functions
function openSettingsModal() {
  settingsModal.classList.remove('hidden');
  // Populate with current config
  modalApiKey.value = state.config.api_key || '';
  modalDefaultModel.value = state.config.default_model || '';
  modalTheme.value = state.config.theme || 'light';
}

function closeSettingsModal() {
  settingsModal.classList.add('hidden');
}

async function saveSettingsModal() {
  const updates = {
    api_key: modalApiKey.value,
    default_model: modalDefaultModel.value,
    theme: modalTheme.value
  };
  await saveConfig(updates);
  closeSettingsModal();
}

// Event listeners
newChatBtn.addEventListener('click', createConversation);
settingsBtn.addEventListener('click', openSettings);
skillsBtn.addEventListener('click', openSkills);
settingsCloseBtn.addEventListener('click', closeSettings);
skillsCloseBtn.addEventListener('click', closeSkills);
overlay.addEventListener('click', () => {
  closeSettings();
  closeSkills();
  closeModelPicker();
  closeSettingsModal();
});
saveSettingsBtn.addEventListener('click', async () => {
  await saveConfig({
    api_key: apiKeyInput.value,
    default_model: defaultModelInput.value,
    theme: themeSelect.value
  });
  closeSettings();
});
logoutBtn.addEventListener('click', async () => {
  await api('POST', '/api/logout');
  apiKeyInput.value = '';
  balanceInfo.innerHTML = '';
});
modelPickerBtn.addEventListener('click', openModelPicker);
modelPickerCloseBtn.addEventListener('click', closeModelPicker);
modelSearch.addEventListener('input', renderModels);
sendBtn.addEventListener('click', sendMessage);
messageInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});
stopBtn.addEventListener('click', stopGeneration);
searchInput.addEventListener('input', renderConversations);
clearBtn.addEventListener('click', async () => {
  if (confirm('Clear all conversations?')) {
    await clearConversations();
  }
});

// Settings Modal listeners
settingsModalClose.addEventListener('click', closeSettingsModal);
modalSaveSettings.addEventListener('click', saveSettingsModal);

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
  const tag = document.activeElement.tagName;
  const isInput = tag === 'INPUT' || tag === 'TEXTAREA' || document.activeElement.isContentEditable;
  
  if (e.key === 'Escape') {
    closeSettings();
    closeSkills();
    closeModelPicker();
    closeSettingsModal();
    stopGeneration();
    return;
  }
  
  if (e.ctrlKey && e.shiftKey) {
    switch (e.key) {
      case 'O':
        e.preventDefault();
        messageInput.focus();
        break;
      case 'N':
        e.preventDefault();
        if (!isInput) createConversation();
        break;
      case ',':
        e.preventDefault();
        if (!isInput) openSettings();
        break;
      case 'E':
        e.preventDefault();
        if (!isInput) openSkills();
        break;
      case 'Delete':
        e.preventDefault();
        if (!isInput && confirm('Clear all conversations?')) clearConversations();
        break;
      case 'ArrowUp':
        e.preventDefault();
        if (!isInput) navigateConversation(-1);
        break;
      case 'ArrowDown':
        e.preventDefault();
        if (!isInput) navigateConversation(1);
        break;
      case 'S':
        e.preventDefault();
        if (!isInput) toggleTheme();
        break;
    }
  }
});

function navigateConversation(dir) {
  const idx = state.conversations.findIndex(c => c.id === state.currentConversationId);
  let newIdx = idx + dir;
  if (newIdx < 0) newIdx = state.conversations.length - 1;
  if (newIdx >= state.conversations.length) newIdx = 0;
  if (state.conversations[newIdx]) {
    selectConversation(state.conversations[newIdx].id);
  }
}

function toggleTheme() {
  const newTheme = state.theme === 'light' ? 'dark' : 'light';
  state.theme = newTheme;
  applyTheme(newTheme);
  saveConfig({ theme: newTheme });
}

// Init
async function init() {
  await loadConfig();
  await loadConversations();
  loadBalance();
}

init();
