// app.js — Agentic Chat frontend

// ===== State =====
const state = {
  conversations: [],
  currentConversationId: null,
  messages: [],
  models: [],
  skills: [],
  config: {},
  theme: 'light',
  abortController: null,
  streaming: false
};

// ===== DOM refs =====
const $ = (id) => document.getElementById(id);
const conversationList = $('conversation-list');
const messagesEl = $('messages');
const messageInput = $('message-input');
const sendBtn = $('send-btn');
const newChatBtn = $('new-chat-btn');
const searchInput = $('search-input');
const settingsBtn = $('settings-btn');
const skillsBtn = $('skills-btn');
const settingsDrawer = $('settings-drawer');
const skillsDrawer = $('skills-drawer');
const modelPickerModal = $('model-picker-modal');
const apiKeyInput = $('api-key-input');
const defaultModelSelect = $('default-model-select');
const balanceDisplay = $('balance-display');
const modelBadge = $('model-badge');
const modelPickerBtn = $('model-picker-btn');
const stopBtn = $('stop-btn');
const copyBtn = $('copy-btn');
const themeToggleBtn = $('theme-toggle-btn');
const skillsList = $('skills-list');
const addSkillBtn = $('add-skill-btn');
const modelSearchInput = $('model-search-input');
const modelList = $('model-list');
const closeSettingsBtn = $('close-settings-btn');
const closeSkillsBtn = $('close-skills-btn');
const closeModelPickerBtn = $('close-model-picker-btn');
const attachBtn = $('attach-btn');

// ===== Theme management =====
function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('theme', theme);
  state.theme = theme;
}

function toggleTheme() {
  const newTheme = state.theme === 'light' ? 'dark' : 'light';
  applyTheme(newTheme);
}

function loadTheme() {
  const saved = localStorage.getItem('theme');
  const theme = saved || 'light';
  applyTheme(theme);
}

// ===== API helpers =====

async function api(url, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  const res = await fetch(url, { ...options, headers });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`API error ${res.status}: ${err}`);
  }
  return res.json();
}

async function loadConfig() {
  state.config = await api('/api/config');
  if (state.config.apiKey) apiKeyInput.value = state.config.apiKey;
  if (state.config.defaultModel) defaultModelSelect.value = state.config.defaultModel;
}

async function saveConfig() {
  state.config.apiKey = apiKeyInput.value;
  state.config.defaultModel = defaultModelSelect.value;
  await fetch('/api/config', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(state.config)
  });
}

async function loadModels() {
  state.models = await api('/api/models');
  populateModelSelect();
  populateModelList();
}

function populateModelSelect() {
  defaultModelSelect.innerHTML = '';
  state.models.forEach(m => {
    const opt = document.createElement('option');
    opt.value = m.id;
    opt.textContent = m.name || m.id;
    if (m.id === state.config.defaultModel) opt.selected = true;
    defaultModelSelect.appendChild(opt);
  });
}

function populateModelList(filter = '') {
  modelList.innerHTML = '';
  const filtered = state.models.filter(m =>
    !filter || m.id.toLowerCase().includes(filter.toLowerCase()) || (m.name && m.name.toLowerCase().includes(filter.toLowerCase()))
  );
  filtered.forEach(m => {
    const card = document.createElement('div');
    card.className = 'model-card';
    card.innerHTML = `<strong>${m.name || m.id}</strong><br><small>${m.id}</small>`;
    card.addEventListener('click', () => selectModel(m.id));
    modelList.appendChild(card);
  });
}

function selectModel(modelId) {
  state.config.defaultModel = modelId;
  defaultModelSelect.value = modelId;
  modelBadge.textContent = modelId;
  saveConfig();
  closeModelPicker();
}

async function loadBalance() {
  try {
    const data = await api('/api/balance');
    balanceDisplay.textContent = `Credits: ${data.credits}, Usage: ${data.usage}, Total: ${data.total}`;
  } catch (e) {
    balanceDisplay.textContent = 'Failed to load balance';
  }
}

async function loadConversations() {
  state.conversations = await api('/api/conversations');
  renderConversationList();
}

function renderConversationList() {
  const search = searchInput.value.toLowerCase();
  conversationList.innerHTML = '';
  state.conversations
    .filter(c => !search || c.title.toLowerCase().includes(search))
    .forEach(c => {
      const item = document.createElement('div');
      item.className = 'conversation-item' + (c.id === state.currentConversationId ? ' active' : '');
      item.textContent = c.title || 'Untitled';
      item.addEventListener('click', () => openConversation(c.id));
      conversationList.appendChild(item);
    });
}

async function openConversation(id) {
  state.currentConversationId = id;
  const conv = await api(`/api/conversations/${id}`);
  state.messages = conv.messages || [];
  renderMessages();
  renderConversationList();
}

async function newConversation() {
  const conv = await api('/api/conversations', {
    method: 'POST',
    body: JSON.stringify({ title: 'New conversation', messages: [] })
  });
  state.currentConversationId = conv.id;
  state.messages = [];
  renderMessages();
  await loadConversations();
}

function renderMessages() {
  messagesEl.innerHTML = '';
  state.messages.forEach(msg => {
    const div = document.createElement('div');
    div.className = `message message-${msg.role}`;
    div.textContent = msg.content;
    messagesEl.appendChild(div);
  });
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

// ===== Streaming chat =====

async function sendMessage() {
  const text = messageInput.value.trim();
  if (!text) return;
  if (!state.currentConversationId) await newConversation();

  // Add user message
  state.messages.push({ role: 'user', content: text });
  renderMessages();
  messageInput.value = '';

  // Start streaming
  state.abortController = new AbortController();
  state.streaming = true;
  stopBtn.style.display = 'inline-block';

  const assistantMsg = { role: 'assistant', content: '' };
  state.messages.push(assistantMsg);

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        conversationId: state.currentConversationId,
        message: text
      }),
      signal: state.abortController.signal
    });

    const reader = response.body.getReader();
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
          if (data === '[DONE]') continue;
          try {
            const parsed = JSON.parse(data);
            if (parsed.type === 'chunk') {
              assistantMsg.content += parsed.content;
              renderMessages();
            } else if (parsed.type === 'usage') {
              console.log('Token usage:', parsed);
            } else if (parsed.type === 'error') {
              console.error('Stream error:', parsed.content);
            }
          } catch (e) {
            // ignore parse errors
          }
        }
      }
    }
  } catch (e) {
    if (e.name !== 'AbortError') {
      console.error('Stream error:', e);
    }
  } finally {
    state.streaming = false;
    stopBtn.style.display = 'none';
    state.abortController = null;
    renderMessages();
  }
}

function stopStreaming() {
  if (state.abortController) {
    state.abortController.abort();
  }
}

// ===== Skills =====

async function loadSkills() {
  state.skills = await api('/api/skills');
  renderSkills();
}

function renderSkills() {
  skillsList.innerHTML = '';
  state.skills.forEach(skill => {
    const div = document.createElement('div');
    div.className = 'skill-item';
    div.innerHTML = `<label><input type="checkbox" ${skill.enabled ? 'checked' : ''}> ${skill.name}</label>`;
    skillsList.appendChild(div);
  });
}

// ===== Drawer/Modal controls =====

function openSettings() {
  settingsDrawer.style.display = 'block';
  loadBalance();
}

function closeSettings() {
  settingsDrawer.style.display = 'none';
  saveConfig();
}

function openSkills() {
  skillsDrawer.style.display = 'block';
  loadSkills();
}

function closeSkills() {
  skillsDrawer.style.display = 'none';
}

function openModelPicker() {
  modelPickerModal.style.display = 'block';
  modelSearchInput.value = '';
  populateModelList();
}

function closeModelPicker() {
  modelPickerModal.style.display = 'none';
}

// ===== Copy last message =====

function copyLastMessage() {
  const last = state.messages[state.messages.length - 1];
  if (last && last.content) {
    navigator.clipboard.writeText(last.content);
  }
}

// ===== Attachments =====

attachBtn.addEventListener('click', () => {
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = 'image/*,.txt,.js,.py,.html,.css,.json,.md';
  input.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    try {
      const result = await fetch('/api/attachments', {
        method: 'POST',
        body: formData
      });
      const data = await result.json();
      console.log('Attachment uploaded:', data);
    } catch (err) {
      console.error('Upload failed:', err);
    }
  });
  input.click();
});

// ===== Event listeners =====

sendBtn.addEventListener('click', sendMessage);
messageInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});
newChatBtn.addEventListener('click', newConversation);
searchInput.addEventListener('input', renderConversationList);
settingsBtn.addEventListener('click', openSettings);
skillsBtn.addEventListener('click', openSkills);
closeSettingsBtn.addEventListener('click', closeSettings);
closeSkillsBtn.addEventListener('click', closeSkills);
modelPickerBtn.addEventListener('click', openModelPicker);
closeModelPickerBtn.addEventListener('click', closeModelPicker);
stopBtn.addEventListener('click', stopStreaming);
copyBtn.addEventListener('click', copyLastMessage);
themeToggleBtn.addEventListener('click', toggleTheme);
modelSearchInput.addEventListener('input', (e) => populateModelList(e.target.value));

apiKeyInput.addEventListener('change', saveConfig);
defaultModelSelect.addEventListener('change', saveConfig);

addSkillBtn.addEventListener('click', async () => {
  const name = prompt('Skill name:');
  if (!name) return;
  await api('/api/skills', {
    method: 'POST',
    body: JSON.stringify({ name, prompt: '', enabled: true })
  });
  loadSkills();
});

// ===== Init =====

async function init() {
  loadTheme();
  await loadConfig();
  await loadModels();
  await loadConversations();
  if (state.conversations.length > 0) {
    await openConversation(state.conversations[0].id);
  }
}

init();