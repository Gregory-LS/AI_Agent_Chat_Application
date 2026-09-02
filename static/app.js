// State
let state = {
  conversations: [],
  currentConversationId: null,
  models: [],
  skills: [],
  config: {},
  streaming: false,
  theme: 'light'
};

// Utility
function $(sel, ctx = document) { return ctx.querySelector(sel); }
function $$(sel, ctx = document) { return [...ctx.querySelectorAll(sel)]; }

// API helpers
async function api(method, path, body) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const res = await fetch(path, opts);
  if (!res.ok) throw new Error(`API ${method} ${path} failed: ${res.status}`);
  return res.json();
}

// Initialize
async function init() {
  await loadConfig();
  await loadModels();
  await loadConversations();
  renderConversations();
  populateModelPicker();
  bindEvents();
}

async function loadConfig() {
  try {
    state.config = await api('GET', '/api/config');
    if (state.config.theme) {
      state.theme = state.config.theme;
      document.documentElement.setAttribute('data-theme', state.theme);
    }
  } catch (e) {
    console.error('Failed to load config', e);
  }
}

async function loadModels() {
  try {
    state.models = await api('GET', '/api/models');
  } catch (e) {
    console.error('Failed to load models', e);
  }
}

async function loadConversations() {
  try {
    state.conversations = await api('GET', '/api/conversations');
  } catch (e) {
    console.error('Failed to load conversations', e);
  }
}

function renderConversations() {
  const list = $('#conversation-list');
  list.innerHTML = '';
  for (const conv of state.conversations) {
    const item = document.createElement('div');
    item.className = 'conversation-item';
    item.textContent = conv.title || 'Untitled';
    item.dataset.id = conv.id;
    if (conv.id === state.currentConversationId) {
      item.classList.add('active');
    }
    list.appendChild(item);
  }
}

function populateModelPicker() {
  const select = $('#model-select');
  select.innerHTML = '';
  for (const model of state.models) {
    const opt = document.createElement('option');
    opt.value = model.id;
    opt.textContent = model.name || model.id;
    if (state.config.default_model && model.id === state.config.default_model) {
      opt.selected = true;
    }
    select.appendChild(opt);
  }
}

// Settings modal
function openSettingsModal() {
  const modal = $('#settings-modal');
  modal.style.display = 'flex';
  // Populate fields with current config
  const apiKeyInput = $('#settings-api-key');
  const defaultModelSelect = $('#settings-default-model');
  apiKeyInput.value = state.config.api_key || '';
  // Populate model select
  defaultModelSelect.innerHTML = '';
  for (const model of state.models) {
    const opt = document.createElement('option');
    opt.value = model.id;
    opt.textContent = model.name || model.id;
    if (state.config.default_model && model.id === state.config.default_model) {
      opt.selected = true;
    }
    defaultModelSelect.appendChild(opt);
  }
}

function closeSettingsModal() {
  $('#settings-modal').style.display = 'none';
}

async function saveSettings() {
  const apiKey = $('#settings-api-key').value.trim();
  const defaultModel = $('#settings-default-model').value;
  const newConfig = { ...state.config, api_key: apiKey, default_model: defaultModel };
  try {
    const saved = await api('PUT', '/api/config', newConfig);
    state.config = saved;
    // Update model picker default selection
    const modelSelect = $('#model-select');
    if (saved.default_model) {
      modelSelect.value = saved.default_model;
    }
    closeSettingsModal();
  } catch (e) {
    console.error('Failed to save settings', e);
    alert('Failed to save settings: ' + e.message);
  }
}

// Event binding
function bindEvents() {
  // Settings button
  $('#settings-btn').addEventListener('click', openSettingsModal);
  $('#settings-close-btn').addEventListener('click', closeSettingsModal);
  $('#settings-cancel-btn').addEventListener('click', closeSettingsModal);
  $('#settings-save-btn').addEventListener('click', saveSettings);
  // Close modal on backdrop click
  $('#settings-modal').addEventListener('click', (e) => {
    if (e.target === $('#settings-modal')) {
      closeSettingsModal();
    }
  });
}

// Start
init();