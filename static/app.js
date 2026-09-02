// State
let state = {
  conversations: [],
  currentConversationId: null,
  models: [],
  skills: [],
  config: {},
  streaming: false,
  abortController: null,
  settingsOpen: false
};

// DOM references
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const messagesEl = $('#messages');
const messageInput = $('#message-input');
const sendBtn = $('#send-btn');
const stopBtn = $('#stop-btn');
const newChatBtn = $('#new-chat-btn');
const settingsBtn = $('#settings-btn');
const settingsDrawer = $('#settings-drawer');
const settingsCloseBtn = $('#settings-close-btn');
const overlay = $('#overlay');
const apiKeyInput = $('#api-key-input');
const defaultModelSelect = $('#default-model-select');
const themeSelect = $('#theme-select');
const saveApiKeyBtn = $('#save-api-key-btn');
const saveSettingsBtn = $('#save-settings-btn');
const settingsStatus = $('#settings-status');

// API helpers
async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`API error ${res.status}: ${err}`);
  }
  if (options.raw) return res;
  return res.json();
}

// Load config
async function loadConfig() {
  try {
    state.config = await api('/api/config');
    if (state.config.apiKey) apiKeyInput.value = state.config.apiKey;
    if (state.config.defaultModel) defaultModelSelect.value = state.config.defaultModel;
    if (state.config.theme) {
      themeSelect.value = state.config.theme;
      document.documentElement.setAttribute('data-theme', state.config.theme);
    }
  } catch (e) {
    console.error('Failed to load config:', e);
  }
}

// Save config
async function saveConfig(updates) {
  try {
    const newConfig = { ...state.config, ...updates };
    await api('/api/config', {
      method: 'PUT',
      body: JSON.stringify(newConfig)
    });
    state.config = newConfig;
    return true;
  } catch (e) {
    console.error('Failed to save config:', e);
    return false;
  }
}

// Load models
async function loadModels() {
  try {
    const data = await api('/api/models');
    state.models = data.data || [];
    populateModelSelect();
  } catch (e) {
    console.error('Failed to load models:', e);
    defaultModelSelect.innerHTML = '<option value="">Error loading models</option>';
  }
}

function populateModelSelect() {
  defaultModelSelect.innerHTML = '<option value="">Select a model</option>';
  state.models.forEach(model => {
    const opt = document.createElement('option');
    opt.value = model.id;
    opt.textContent = model.name || model.id;
    defaultModelSelect.appendChild(opt);
  });
  if (state.config.defaultModel) {
    defaultModelSelect.value = state.config.defaultModel;
  }
}

// Toggle settings drawer
function openSettings() {
  state.settingsOpen = true;
  settingsDrawer.classList.remove('hidden');
  overlay.classList.remove('hidden');
}

function closeSettings() {
  state.settingsOpen = false;
  settingsDrawer.classList.add('hidden');
  overlay.classList.add('hidden');
}

// Event listeners
settingsBtn.addEventListener('click', openSettings);
settingsCloseBtn.addEventListener('click', closeSettings);
overlay.addEventListener('click', closeSettings);

saveApiKeyBtn.addEventListener('click', async () => {
  const apiKey = apiKeyInput.value.trim();
  if (!apiKey) {
    settingsStatus.textContent = 'Please enter an API key.';
    return;
  }
  const success = await saveConfig({ apiKey });
  settingsStatus.textContent = success ? 'API key saved.' : 'Failed to save API key.';
});

saveSettingsBtn.addEventListener('click', async () => {
  const defaultModel = defaultModelSelect.value;
  const theme = themeSelect.value;
  const success = await saveConfig({ defaultModel, theme });
  if (success) {
    document.documentElement.setAttribute('data-theme', theme);
    settingsStatus.textContent = 'Settings saved.';
  } else {
    settingsStatus.textContent = 'Failed to save settings.';
  }
});

// Init
async function init() {
  await loadConfig();
  await loadModels();
}

init();