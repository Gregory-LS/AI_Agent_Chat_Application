// app.js — Claude-style AI chat UI
// State
let state = {
  conversations: [],
  currentConversationId: null,
  skills: [],
  activeSkills: [],
  config: {},
  models: [],
  balance: null,
  streaming: false,
  abortController: null,
  theme: 'light',
  messageHistory: [],
  historyIndex: -1
};

// DOM refs
const $ = id => document.getElementById(id);
const sidebar = $('sidebar');
const chatArea = $('chat-area');
const messagesEl = $('messages');
const composer = $('composer');
const sendBtn = $('send-btn');
const modelSelect = $('model-select');
const settingsDrawer = $('settings-drawer');
const modelDrawer = $('model-drawer');
const skillsDrawer = $('skills-drawer');
const attachmentInput = $('attachment-input');

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
  const ctrl = e.ctrlKey || e.metaKey;
  const shift = e.shiftKey;
  const key = e.key;

  // Close drawers/modals with Escape
  if (key === 'Escape') {
    closeAllDrawers();
    return;
  }

  // Ctrl+Enter: send message (alternative to clicking send)
  if (ctrl && !shift && key === 'Enter') {
    e.preventDefault();
    sendMessage();
    return;
  }

  // Ctrl+Shift+Enter: insert newline in composer
  if (ctrl && shift && key === 'Enter') {
    // Default behavior is newline; do nothing special
    return;
  }

  // Ctrl+Shift+C: copy last assistant message
  if (ctrl && shift && key === 'C') {
    e.preventDefault();
    copyLastAssistantMessage();
    return;
  }

  // Ctrl+Shift+Delete: clear current conversation
  if (ctrl && shift && key === 'Delete') {
    e.preventDefault();
    clearConversation();
    return;
  }

  // Ctrl+Shift+N: new conversation
  if (ctrl && shift && key === 'N') {
    e.preventDefault();
    newConversation();
    return;
  }

  // Ctrl+Shift+,: open settings
  if (ctrl && shift && key === ',') {
    e.preventDefault();
    openSettings();
    return;
  }

  // Ctrl+Shift+B: toggle sidebar
  if (ctrl && shift && key === 'B') {
    e.preventDefault();
    toggleSidebar();
    return;
  }

  // Ctrl+Shift+M: open model picker
  if (ctrl && shift && key === 'M') {
    e.preventDefault();
    openModelPicker();
    return;
  }

  // ArrowUp: navigate conversation history (if composer is focused and empty)
  if (key === 'ArrowUp' && document.activeElement === composer && composer.value.trim() === '') {
    e.preventDefault();
    navigateHistory(-1);
    return;
  }

  // ArrowDown: navigate conversation history
  if (key === 'ArrowDown' && document.activeElement === composer && state.historyIndex >= 0) {
    e.preventDefault();
    navigateHistory(1);
    return;
  }
});

function closeAllDrawers() {
  settingsDrawer.classList.remove('open');
  modelDrawer.classList.remove('open');
  skillsDrawer.classList.remove('open');
}

function sendMessage() {
  const text = composer.value.trim();
  if (!text || state.streaming) return;
  // ... actual send logic (already exists)
}

function copyLastAssistantMessage() {
  const messages = messagesEl.querySelectorAll('.message.assistant');
  if (messages.length === 0) return;
  const last = messages[messages.length - 1];
  const text = last.querySelector('.message-content')?.textContent || '';
  if (text) {
    navigator.clipboard.writeText(text).catch(() => {});
  }
}

function clearConversation() {
  if (!state.currentConversationId) return;
  if (!confirm('Clear all messages in this conversation?')) return;
  // ... clear logic
}

function newConversation() {
  // ... new conversation logic
}

function openSettings() {
  settingsDrawer.classList.add('open');
}

function toggleSidebar() {
  sidebar.classList.toggle('collapsed');
}

function openModelPicker() {
  modelDrawer.classList.add('open');
}

function navigateHistory(direction) {
  if (state.messageHistory.length === 0) return;
  if (direction === -1) {
    // Save current value if starting fresh
    if (state.historyIndex === -1) {
      state.pendingMessage = composer.value;
    }
    state.historyIndex = Math.min(state.historyIndex + 1, state.messageHistory.length - 1);
  } else {
    state.historyIndex = state.historyIndex - 1;
    if (state.historyIndex < 0) {
      state.historyIndex = -1;
      composer.value = state.pendingMessage || '';
      return;
    }
  }
  const entry = state.messageHistory[state.historyIndex];
  if (entry) {
    composer.value = entry;
  }
}

// ... rest of existing app.js code (abbreviated for brevity, but in real implementation would be full)
