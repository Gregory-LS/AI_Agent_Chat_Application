/**
 * Agentic Chat — main application JavaScript
 * Handles state management, streaming, UI updates, and event handlers.
 */

// ============================================================
// State
// ============================================================

const state = {
  conversations: [],
  currentConversationId: null,
  messages: [],
  streaming: false,
  abortController: null,
  config: {
    apiKey: '',
    defaultModel: '',
    theme: 'light'
  },
  skills: [],
  activeSkills: [],
  models: [],
  balance: null,
  selectedModel: null,
  searchQuery: '',
  conversationSearchQuery: ''
};

// ============================================================
// DOM references (populated on DOMContentLoaded)
// ============================================================

let $ = (sel) => document.querySelector(sel);
let $$ = (sel) => document.querySelectorAll(sel);

const dom = {};

function initDom() {
  dom.sidebar = $('#sidebar');
  dom.conversationList = $('#conversation-list');
  dom.chatArea = $('#chat-area');
  dom.messagesContainer = $('#messages');
  dom.composer = $('#composer');
  dom.composerInput = $('#composer-input');
  dom.sendButton = $('#send-button');
  dom.stopButton = $('#stop-button');
  dom.modelPicker = $('#model-picker');
  dom.modelPickerTrigger = $('#model-picker-trigger');
  dom.settingsDrawer = $('#settings-drawer');
  dom.settingsToggle = $('#settings-toggle');
  dom.skillsDrawer = $('#skills-drawer');
  dom.skillsToggle = $('#skills-toggle');
  dom.newChatButton = $('#new-chat');
  dom.searchInput = $('#search-input');
  dom.conversationSearchInput = $('#conversation-search');
  dom.themeToggle = $('#theme-toggle');
  dom.apiKeyInput = $('#api-key-input');
  dom.defaultModelSelect = $('#default-model-select');
  dom.balanceDisplay = $('#balance-display');
  dom.exportButton = $('#export-button');
  dom.importButton = $('#import-button');
  dom.importFileInput = $('#import-file-input');
  dom.attachmentButton = $('#attachment-button');
  dom.attachmentInput = $('#attachment-input');
  dom.attachmentPreview = $('#attachment-preview');
  dom.modelList = $('#model-list');
  dom.modelSearch = $('#model-search');
  dom.skillsList = $('#skills-list');
  dom.newSkillButton = $('#new-skill-button');
  dom.newSkillModal = $('#new-skill-modal');
  dom.newSkillForm = $('#new-skill-form');
  dom.newSkillName = $('#new-skill-name');
  dom.newSkillPrompt = $('#new-skill-prompt');
  dom.cancelNewSkill = $('#cancel-new-skill');
  dom.renameModal = $('#rename-modal');
  dom.renameForm = $('#rename-form');
  dom.renameInput = $('#rename-input');
  dom.cancelRename = $('#cancel-rename');
  dom.deleteConfirmModal = $('#delete-confirm-modal');
  dom.confirmDelete = $('#confirm-delete');
  dom.cancelDelete = $('#cancel-delete');
  dom.settingsClose = $('#settings-close');
  dom.skillsClose = $('#skills-close');
}

// ============================================================
// Utility functions
// ============================================================

function uuid() {
  return crypto.randomUUID();
}

function debounce(fn, delay) {
  let timer;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function formatDate(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

// ============================================================
// API helpers
// ============================================================

async function apiRequest(method, path, body) {
  const options = {
    method,
    headers: { 'Content-Type': 'application/json' }
  };
  if (body !== undefined) {
    options.body = JSON.stringify(body);
  }
  const resp = await fetch(path, options);
  if (!resp.ok) {
    const err = await resp.text();
    throw new Error(`API ${method} ${path} failed: ${resp.status} ${err}`);
  }
  return resp.json();
}

// ============================================================
// Conversation management
// ============================================================

async function loadConversations() {
  const data = await apiRequest('GET', '/api/conversations');
  state.conversations = data;
  renderConversationList();
}

async function createConversation() {
  const conversation = {
    id: uuid(),
    title: 'New conversation',
    messages: [],
    model: state.selectedModel || state.config.defaultModel || '',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  };
  await apiRequest('POST', '/api/conversations', conversation);
  state.conversations.unshift(conversation);
  state.currentConversationId = conversation.id;
  state.messages = [];
  renderConversationList();
  renderMessages();
  updateActiveConversation();
  return conversation;
}

async function loadConversation(id) {
  const conversation = await apiRequest('GET', `/api/conversations/${id}`);
  state.currentConversationId = id;
  state.messages = conversation.messages || [];
  state.selectedModel = conversation.model || state.config.defaultModel;
  renderMessages();
  updateActiveConversation();
  updateModelPickerLabel();
}

async function saveConversation() {
  if (!state.currentConversationId) return;
  const conversation = state.conversations.find(c => c.id === state.currentConversationId);
  if (!conversation) return;
  conversation.messages = state.messages;
  conversation.updatedAt = new Date().toISOString();
  await apiRequest('PATCH', `/api/conversations/${conversation.id}`, { messages: state.messages, updatedAt: conversation.updatedAt });
  renderConversationList();
}

async function deleteConversation(id) {
  await apiRequest('DELETE', `/api/conversations/${id}`);
  state.conversations = state.conversations.filter(c => c.id !== id);
  if (state.currentConversationId === id) {
    state.currentConversationId = null;
    state.messages = [];
    renderMessages();
  }
  renderConversationList();
}

async function renameConversation(id, title) {
  await apiRequest('PATCH', `/api/conversations/${id}`, { title });
  const conversation = state.conversations.find(c => c.id === id);
  if (conversation) {
    conversation.title = title;
  }
  renderConversationList();
}

async function searchConversations(query) {
  state.conversationSearchQuery = query;
  renderConversationList();
}

async function exportConversation(id, format = 'json') {
  const resp = await fetch(`/api/conversations/${id}/export?format=${format}`);
  if (!resp.ok) throw new Error('Export failed');
  const blob = await resp.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `conversation-${id}.${format}`;
  a.click();
  URL.revokeObjectURL(url);
}

async function importConversation(file) {
  const formData = new FormData();
  formData.append('file', file);
  const resp = await fetch('/api/conversations/import', { method: 'POST', body: formData });
  if (!resp.ok) throw new Error('Import failed');
  return resp.json();
}

// ============================================================
// Messages
// ============================================================

function addMessage(role, content, model = null) {
  const message = {
    id: uuid(),
    role,
    content,
    model,
    timestamp: new Date().toISOString()
  };
  state.messages.push(message);
  renderMessages();
  return message;
}

function updateLastMessage(content) {
  if (state.messages.length === 0) return;
  state.messages[state.messages.length - 1].content = content;
  renderMessages();
}

function clearMessages() {
  state.messages = [];
  renderMessages();
}

// ============================================================
// Streaming
// ============================================================

async function startStreaming(userMessage) {
  if (state.streaming) return;
  state.streaming = true;
  state.abortController = new AbortController();
  
  addMessage('user', userMessage);
  addMessage('assistant', '', state.selectedModel);
  
  dom.sendButton.style.display = 'none';
  dom.stopButton.style.display = 'inline-flex';
  dom.composerInput.disabled = true;
  
  const skillsPayload = state.activeSkills.map(skillId => {
    const skill = state.skills.find(s => s.id === skillId);
    return skill ? { name: skill.name, prompt: skill.prompt } : null;
  }).filter(Boolean);
  
  try {
    const resp = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: state.selectedModel,
        messages: state.messages.slice(0, -1).map(m => ({ role: m.role, content: m.content })),
        skills: skillsPayload
      }),
      signal: state.abortController.signal
    });
    
    if (!resp.ok) {
      const errText = await resp.text();
      throw new Error(errText);
    }
    
    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data === '[DONE]') {
            // stream complete
            break;
          }
          try {
            const parsed = JSON.parse(data);
            if (parsed.type === 'chunk') {
              appendToLastMessage(parsed.content);
            } else if (parsed.type === 'error') {
              appendToLastMessage(`\n\nError: ${parsed.message}`);
            } else if (parsed.type === 'usage') {
              // could display usage info
            }
          } catch (e) {
            // ignore parse errors
          }
        }
      }
    }
  } catch (err) {
    if (err.name !== 'AbortError') {
      appendToLastMessage(`\n\nError: ${err.message}`);
    }
  } finally {
    state.streaming = false;
    state.abortController = null;
    dom.sendButton.style.display = 'inline-flex';
    dom.stopButton.style.display = 'none';
    dom.composerInput.disabled = false;
    dom.composerInput.focus();
    await saveConversation();
  }
}

function stopStreaming() {
  if (state.abortController) {
    state.abortController.abort();
  }
}

function appendToLastMessage(text) {
  if (state.messages.length === 0) return;
  const last = state.messages[state.messages.length - 1];
  last.content += text;
  // Update the last message element in DOM
  const messageElements = dom.messagesContainer.querySelectorAll('.message');
  if (messageElements.length > 0) {
    const lastEl = messageElements[messageElements.length - 1];
    const contentEl = lastEl.querySelector('.message-content');
    if (contentEl) {
      contentEl.innerHTML = renderMarkdown(last.content);
    }
  }
}

// ============================================================
// Config
// ============================================================

async function loadConfig() {
  const config = await apiRequest('GET', '/api/config');
  state.config = config;
  applyConfig();
}

async function saveConfig(updates) {
  const newConfig = { ...state.config, ...updates };
  await apiRequest('PUT', '/api/config', newConfig);
  state.config = newConfig;
  applyConfig();
}

function applyConfig() {
  if (state.config.theme) {
    document.documentElement.setAttribute('data-theme', state.config.theme);
  }
  if (dom.apiKeyInput) {
    dom.apiKeyInput.value = state.config.apiKey || '';
  }
}

// ============================================================
// Skills
// ============================================================

async function loadSkills() {
  const skills = await apiRequest('GET', '/api/skills');
  state.skills = skills;
  renderSkillsList();
}

async function saveSkill(skill) {
  if (skill.id) {
    await apiRequest('PATCH', `/api/skills/${skill.id}`, skill);
  } else {
    skill.id = uuid();
    await apiRequest('POST', '/api/skills', skill);
  }
  await loadSkills();
}

async function deleteSkill(id) {
  await apiRequest('DELETE', `/api/skills/${id}`);
  state.activeSkills = state.activeSkills.filter(s => s !== id);
  await loadSkills();
}

function toggleSkill(id) {
  const idx = state.activeSkills.indexOf(id);
  if (idx === -1) {
    state.activeSkills.push(id);
  } else {
    state.activeSkills.splice(idx, 1);
  }
  renderSkillsList();
}

// ============================================================
// Models
// ============================================================

async function loadModels() {
  const models = await apiRequest('GET', '/api/models');
  state.models = models;
  renderModelList();
}

async function loadBalance() {
  try {
    const balance = await apiRequest('GET', '/api/balance');
    state.balance = balance;
    updateBalanceDisplay();
  } catch (e) {
    console.error('Failed to load balance', e);
  }
}

function selectModel(modelId) {
  state.selectedModel = modelId;
  updateModelPickerLabel();
  if (dom.modelList) {
    dom.modelList.querySelectorAll('.model-item').forEach(el => {
      el.classList.toggle('selected', el.dataset.modelId === modelId);
    });
  }
}

// ============================================================
// Rendering
// ============================================================

function renderConversationList() {
  if (!dom.conversationList) return;
  const query = state.conversationSearchQuery.toLowerCase();
  const filtered = query
    ? state.conversations.filter(c => c.title.toLowerCase().includes(query))
    : state.conversations;
  
  dom.conversationList.innerHTML = filtered.map(c => `
    <div class="conversation-item ${c.id === state.currentConversationId ? 'active' : ''}" data-id="${c.id}">
      <span class="conversation-title">${escapeHtml(c.title)}</span>
      <span class="conversation-date">${formatDate(c.updatedAt)}</span>
      <div class="conversation-actions">
        <button class="rename-btn" data-id="${c.id}" title="Rename">✏️</button>
        <button class="delete-btn" data-id="${c.id}" title="Delete">🗑️</button>
      </div>
    </div>
  `).join('');
}

function renderMessages() {
  if (!dom.messagesContainer) return;
  dom.messagesContainer.innerHTML = state.messages.map(m => `
    <div class="message ${m.role}" data-id="${m.id}">
      <div class="message-role">${m.role === 'user' ? 'You' : 'Assistant'}</div>
      <div class="message-content">${renderMarkdown(m.content)}</div>
      ${m.model ? `<div class="message-model">${escapeHtml(m.model)}</div>` : ''}
      <div class="message-timestamp">${formatDate(m.timestamp)}</div>
    </div>
  `).join('');
  dom.messagesContainer.scrollTop = dom.messagesContainer.scrollHeight;
}

function renderMarkdown(text) {
  // Simple markdown-like rendering (no library)
  let html = escapeHtml(text);
  // Code blocks
  html = html.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
  // Bold
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  // Italic
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
  // Links
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
  // Newlines to <br>
  html = html.replace(/\n/g, '<br>');
  return html;
}

function renderModelList() {
  if (!dom.modelList) return;
  const query = (dom.modelSearch?.value || '').toLowerCase();
  const filtered = query
    ? state.models.filter(m => m.id.toLowerCase().includes(query) || (m.name && m.name.toLowerCase().includes(query)))
    : state.models;
  
  // Group by provider
  const grouped = {};
  for (const model of filtered) {
    const provider = model.provider || 'Other';
    if (!grouped[provider]) grouped[provider] = [];
    grouped[provider].push(model);
  }
  
  dom.modelList.innerHTML = Object.entries(grouped).map(([provider, models]) => `
    <div class="model-group">
      <div class="model-group-title">${escapeHtml(provider)}</div>
      ${models.map(m => `
        <div class="model-item ${m.id === state.selectedModel ? 'selected' : ''}" data-model-id="${m.id}">
          <span class="model-name">${escapeHtml(m.name || m.id)}</span>
          <span class="model-context">${m.context_length ? `${m.context_length} ctx` : ''}</span>
          <span class="model-pricing">${m.pricing ? `$${m.pricing.prompt}/${m.pricing.completion}` : ''}</span>
        </div>
      `).join('')}
    </div>
  `).join('');
}

function renderSkillsList() {
  if (!dom.skillsList) return;
  dom.skillsList.innerHTML = state.skills.map(s => `
    <div class="skill-item">
      <label>
        <input type="checkbox" ${state.activeSkills.includes(s.id) ? 'checked' : ''} data-skill-id="${s.id}">
        <span class="skill-name">${escapeHtml(s.name)}</span>
      </label>
      <button class="delete-skill-btn" data-skill-id="${s.id}" title="Delete skill">🗑️</button>
    </div>
  `).join('');
}

function updateActiveConversation() {
  document.querySelectorAll('.conversation-item').forEach(el => {
    el.classList.toggle('active', el.dataset.id === state.currentConversationId);
  });
}

function updateModelPickerLabel() {
  if (dom.modelPickerTrigger) {
    const model = state.models.find(m => m.id === state.selectedModel);
    dom.modelPickerTrigger.textContent = model ? (model.name || model.id) : 'Select model';
  }
}

function updateBalanceDisplay() {
  if (dom.balanceDisplay && state.balance) {
    dom.balanceDisplay.textContent = `Credits: ${state.balance.credits?.toFixed(4) || 'N/A'}`;
  }
}

// ============================================================
// Event handlers
// ============================================================

function setupEventListeners() {
  // New chat
  dom.newChatButton?.addEventListener('click', async () => {
    await createConversation();
  });
  
  // Send message
  dom.sendButton?.addEventListener('click', async () => {
    const text = dom.composerInput.value.trim();
    if (!text || state.streaming) return;
    dom.composerInput.value = '';
    await startStreaming(text);
  });
  
  // Stop streaming
  dom.stopButton?.addEventListener('click', stopStreaming);
  
  // Enter to send (Shift+Enter for newline)
  dom.composerInput?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      dom.sendButton.click();
    }
  });
  
  // Conversation list click delegation
  dom.conversationList?.addEventListener('click', async (e) => {
    const item = e.target.closest('.conversation-item');
    if (!item) return;
    const id = item.dataset.id;
    
    if (e.target.closest('.rename-btn')) {
      dom.renameModal?.classList.add('open');
      dom.renameInput.value = state.conversations.find(c => c.id === id)?.title || '';
      dom.renameForm.dataset.id = id;
      return;
    }
    
    if (e.target.closest('.delete-btn')) {
      dom.deleteConfirmModal?.classList.add('open');
      dom.confirmDelete.dataset.id = id;
      return;
    }
    
    await loadConversation(id);
  });
  
  // Conversation search
  dom.conversationSearchInput?.addEventListener('input', debounce((e) => {
    searchConversations(e.target.value);
  }, 300));
  
  // Settings toggle
  dom.settingsToggle?.addEventListener('click', () => {
    dom.settingsDrawer?.classList.toggle('open');
    loadBalance();
  });
  
  dom.settingsClose?.addEventListener('click', () => {
    dom.settingsDrawer?.classList.remove('open');
  });
  
  // Skills toggle
  dom.skillsToggle?.addEventListener('click', () => {
    dom.skillsDrawer?.classList.toggle('open');
  });
  
  dom.skillsClose?.addEventListener('click', () => {
    dom.skillsDrawer?.classList.remove('open');
  });
  
  // Theme toggle
  dom.themeToggle?.addEventListener('click', async () => {
    const newTheme = state.config.theme === 'dark' ? 'light' : 'dark';
    await saveConfig({ theme: newTheme });
  });
  
  // API key input
  dom.apiKeyInput?.addEventListener('change', async (e) => {
    await saveConfig({ apiKey: e.target.value });
    loadBalance();
  });
  
  // Model picker
  dom.modelPickerTrigger?.addEventListener('click', () => {
    dom.modelPicker?.classList.toggle('open');
    if (dom.modelPicker?.classList.contains('open')) {
      loadModels();
    }
  });
  
  dom.modelSearch?.addEventListener('input', debounce(() => {
    renderModelList();
  }, 300));
  
  dom.modelList?.addEventListener('click', (e) => {
    const item = e.target.closest('.model-item');
    if (!item) return;
    selectModel(item.dataset.modelId);
    dom.modelPicker?.classList.remove('open');
  });
  
  // Skills
  dom.skillsList?.addEventListener('change', (e) => {
    if (e.target.type === 'checkbox') {
      toggleSkill(e.target.dataset.skillId);
    }
  });
  
  dom.skillsList?.addEventListener('click', async (e) => {
    const btn = e.target.closest('.delete-skill-btn');
    if (btn) {
      await deleteSkill(btn.dataset.skillId);
    }
  });
  
  dom.newSkillButton?.addEventListener('click', () => {
    dom.newSkillModal?.classList.add('open');
  });
  
  dom.cancelNewSkill?.addEventListener('click', () => {
    dom.newSkillModal?.classList.remove('open');
  });
  
  dom.newSkillForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = dom.newSkillName.value.trim();
    const prompt = dom.newSkillPrompt.value.trim();
    if (!name || !prompt) return;
    await saveSkill({ name, prompt });
    dom.newSkillModal?.classList.remove('open');
    dom.newSkillForm.reset();
  });
  
  // Rename modal
  dom.cancelRename?.addEventListener('click', () => {
    dom.renameModal?.classList.remove('open');
  });
  
  dom.renameForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const id = dom.renameForm.dataset.id;
    const title = dom.renameInput.value.trim();
    if (!id || !title) return;
    await renameConversation(id, title);
    dom.renameModal?.classList.remove('open');
  });
  
  // Delete confirm
  dom.cancelDelete?.addEventListener('click', () => {
    dom.deleteConfirmModal?.classList.remove('open');
  });
  
  dom.confirmDelete?.addEventListener('click', async () => {
    const id = dom.confirmDelete.dataset.id;
    if (!id) return;
    await deleteConversation(id);
    dom.deleteConfirmModal?.classList.remove('open');
  });
  
  // Export
  dom.exportButton?.addEventListener('click', async () => {
    if (!state.currentConversationId) return;
    await exportConversation(state.currentConversationId, 'json');
  });
  
  // Import
  dom.importButton?.addEventListener('click', () => {
    dom.importFileInput?.click();
  });
  
  dom.importFileInput?.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    try {
      const result = await importConversation(file);
      await loadConversations();
      if (result.id) {
        await loadConversation(result.id);
      }
    } catch (err) {
      alert('Import failed: ' + err.message);
    }
    e.target.value = '';
  });
  
  // Attachment
  dom.attachmentButton?.addEventListener('click', () => {
    dom.attachmentInput?.click();
  });
  
  dom.attachmentInput?.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    try {
      const resp = await fetch('/api/attachments', { method: 'POST', body: formData });
      if (!resp.ok) throw new Error('Upload failed');
      const result = await resp.json();
      // Add attachment reference to composer
      if (dom.attachmentPreview) {
        dom.attachmentPreview.innerHTML = `<span class="attachment-name">${escapeHtml(file.name)}</span>`;
      }
    } catch (err) {
      alert('Upload failed: ' + err.message);
    }
    e.target.value = '';
  });
  
  // Keyboard shortcuts
  document.addEventListener('keydown', (e) => {
    // Ctrl+Shift+N: new chat
    if (e.ctrlKey && e.shiftKey && e.key === 'N') {
      e.preventDefault();
      dom.newChatButton?.click();
    }
    // Escape: close drawers/modals
    if (e.key === 'Escape') {
      dom.settingsDrawer?.classList.remove('open');
      dom.skillsDrawer?.classList.remove('open');
      dom.modelPicker?.classList.remove('open');
      dom.newSkillModal?.classList.remove('open');
      dom.renameModal?.classList.remove('open');
      dom.deleteConfirmModal?.classList.remove('open');
    }
  });
}

// ============================================================
// Initialization
// ============================================================

document.addEventListener('DOMContentLoaded', async () => {
  initDom();
  await loadConfig();
  await loadConversations();
  await loadSkills();
  await loadModels();
  setupEventListeners();
  
  // If there are conversations, load the first one
  if (state.conversations.length > 0) {
    await loadConversation(state.conversations[0].id);
  }
  
  // Focus composer
  dom.composerInput?.focus();
});
