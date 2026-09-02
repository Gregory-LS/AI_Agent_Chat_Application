// ============================================================
// Agentic Chat — Main Application
// ============================================================

// --- State Management ---
const AppState = {
  conversations: [],
  currentConversationId: null,
  skills: [],
  config: {},
  models: [],
  theme: 'light',
  abortController: null,
  streaming: false,
};

// --- Utility Functions ---
function $(id) { return document.getElementById(id); }

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function formatDate(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

// --- API Helpers ---
async function apiFetch(url, options = {}) {
  const resp = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`API error ${resp.status}: ${text}`);
  }
  return resp.json();
}

// --- Theme ---
function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  AppState.theme = theme;
}

function toggleTheme() {
  const newTheme = AppState.theme === 'light' ? 'dark' : 'light';
  applyTheme(newTheme);
  apiFetch('/api/config', {
    method: 'PUT',
    body: JSON.stringify({ theme: newTheme }),
  }).catch(console.error);
}

// --- Conversation Management ---
async function loadConversations() {
  try {
    AppState.conversations = await apiFetch('/api/conversations');
    renderSidebar();
  } catch (e) {
    console.error('Failed to load conversations:', e);
  }
}

async function selectConversation(id) {
  if (AppState.streaming) return;
  AppState.currentConversationId = id;
  const conv = AppState.conversations.find(c => c.id === id);
  if (conv) {
    renderMessages(conv.messages || []);
  } else {
    renderMessages([]);
  }
  renderSidebar();
}

async function newConversation() {
  if (AppState.streaming) return;
  try {
    const conv = await apiFetch('/api/conversations', { method: 'POST' });
    AppState.conversations.unshift(conv);
    selectConversation(conv.id);
  } catch (e) {
    console.error('Failed to create conversation:', e);
  }
}

async function deleteConversation(id) {
  if (AppState.streaming) return;
  try {
    await apiFetch(`/api/conversations/${id}`, { method: 'DELETE' });
    AppState.conversations = AppState.conversations.filter(c => c.id !== id);
    if (AppState.currentConversationId === id) {
      AppState.currentConversationId = null;
      renderMessages([]);
    }
    renderSidebar();
  } catch (e) {
    console.error('Failed to delete conversation:', e);
  }
}

async function renameConversation(id, title) {
  try {
    const updated = await apiFetch(`/api/conversations/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ title }),
    });
    const idx = AppState.conversations.findIndex(c => c.id === id);
    if (idx !== -1) AppState.conversations[idx] = updated;
    renderSidebar();
  } catch (e) {
    console.error('Failed to rename conversation:', e);
  }
}

// --- Skills ---
async function loadSkills() {
  try {
    AppState.skills = await apiFetch('/api/skills');
    renderSkills();
  } catch (e) {
    console.error('Failed to load skills:', e);
  }
}

// --- Models ---
async function loadModels() {
  try {
    AppState.models = await apiFetch('/api/models');
    renderModelPicker();
  } catch (e) {
    console.error('Failed to load models:', e);
  }
}

// --- Config ---
async function loadConfig() {
  try {
    AppState.config = await apiFetch('/api/config');
    applyTheme(AppState.config.theme || 'light');
    if (AppState.config.defaultModel) {
      const modelSelect = $('model-select');
      if (modelSelect) modelSelect.value = AppState.config.defaultModel;
    }
  } catch (e) {
    console.error('Failed to load config:', e);
  }
}

// --- Rendering Functions ---
function renderSidebar() {
  const sidebar = $('sidebar-conversations');
  if (!sidebar) return;
  sidebar.innerHTML = AppState.conversations.map(conv => {
    const active = conv.id === AppState.currentConversationId ? 'active' : '';
    return `<div class="conversation-item ${active}" data-id="${conv.id}">
      <span class="conv-title">${escapeHtml(conv.title || 'New conversation')}</span>
      <button class="conv-delete" data-id="${conv.id}">×</button>
    </div>`;
  }).join('');
}

function renderMessages(messages) {
  const chatArea = $('chat-messages');
  if (!chatArea) return;
  chatArea.innerHTML = messages.map((msg, i) => {
    const isUser = msg.role === 'user';
    const cls = isUser ? 'message user' : 'message assistant';
    return `<div class="${cls}" data-index="${i}">
      <div class="message-content">${escapeHtml(msg.content)}</div>
      ${msg.usage ? `<div class="message-usage">Tokens: ${msg.usage.total_tokens || '?'}</div>` : ''}
    </div>`;
  }).join('');
  chatArea.scrollTop = chatArea.scrollHeight;
}

function renderSkills() {
  // Placeholder
}

function renderModelPicker() {
  // Placeholder
}

// --- Streaming Fetch Implementation ---

/**
 * Send a chat message and stream the response via SSE.
 * @param {string} content - The user's message.
 * @param {string} model - The model ID to use.
 * @param {Array} history - Previous messages in the conversation.
 * @param {AbortSignal} [signal] - Optional signal to cancel the stream.
 * @returns {Promise<Object>} Resolves with { content, usage } on completion.
 */
async function streamFetch(content, model, history, signal) {
  const messages = [...history, { role: 'user', content }];
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages, model }),
    signal,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Chat API error ${response.status}: ${text}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let assistantContent = '';
  let usage = null;
  let done = false;

  while (!done) {
    const { value, done: streamDone } = await reader.read();
    done = streamDone;
    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split('\n');
    buffer = lines.pop() || ''; // Keep incomplete line in buffer

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6).trim();
        if (!data) continue;
        try {
          const event = JSON.parse(data);
          switch (event.type) {
            case 'chunk':
              assistantContent += event.content || '';
              // Dispatch custom event for UI update
              window.dispatchEvent(new CustomEvent('chat-chunk', {
                detail: { content: assistantContent }
              }));
              break;
            case 'usage':
              usage = event.data;
              break;
            case 'done':
              // Stream complete
              break;
            case 'error':
              throw new Error(event.error || 'Unknown streaming error');
            default:
              // Ignore unknown event types
              break;
          }
        } catch (parseError) {
          // If JSON parse fails, skip invalid data
          console.warn('Failed to parse SSE data:', data, parseError);
        }
      }
    }
  }

  return { content: assistantContent, usage };
}

// --- Send Message ---
async function sendMessage() {
  if (AppState.streaming) return;
  const input = $('message-input');
  const content = input.value.trim();
  if (!content) return;

  input.value = '';
  AppState.streaming = true;
  AppState.abortController = new AbortController();

  // Ensure we have a current conversation
  if (!AppState.currentConversationId) {
    await newConversation();
  }

  const conv = AppState.conversations.find(c => c.id === AppState.currentConversationId);
  const history = conv ? conv.messages || [] : [];
  const model = AppState.config.defaultModel || 'openai/gpt-4o';

  // Add user message immediately
  const userMsg = { role: 'user', content };
  if (conv) {
    conv.messages = [...conv.messages, userMsg];
    renderMessages(conv.messages);
    // Persist user message
    apiFetch(`/api/conversations/${conv.id}`, {
      method: 'PATCH',
      body: JSON.stringify({ messages: conv.messages }),
    }).catch(console.error);
  }

  // Show assistant placeholder
  const assistantMsg = { role: 'assistant', content: '' };
  if (conv) {
    conv.messages.push(assistantMsg);
    renderMessages(conv.messages);
  }

  // Listen for chunks to update the placeholder
  const chunkHandler = (e) => {
    if (conv && conv.messages.length > 0) {
      const lastMsg = conv.messages[conv.messages.length - 1];
      if (lastMsg.role === 'assistant') {
        lastMsg.content = e.detail.content;
        renderMessages(conv.messages);
      }
    }
  };
  window.addEventListener('chat-chunk', chunkHandler);

  try {
    const result = await streamFetch(content, model, history, AppState.abortController.signal);
    if (conv && conv.messages.length > 0) {
      const lastMsg = conv.messages[conv.messages.length - 1];
      if (lastMsg.role === 'assistant') {
        lastMsg.content = result.content;
        if (result.usage) {
          lastMsg.usage = result.usage;
        }
        // Persist final state
        await apiFetch(`/api/conversations/${conv.id}`, {
          method: 'PATCH',
          body: JSON.stringify({ messages: conv.messages }),
        });
        renderMessages(conv.messages);
      }
    }
  } catch (e) {
    if (e.name === 'AbortError') {
      console.log('Stream cancelled by user');
      // Remove the empty assistant message if cancelled early
      if (conv && conv.messages.length > 0) {
        const lastMsg = conv.messages[conv.messages.length - 1];
        if (lastMsg.role === 'assistant' && !lastMsg.content) {
          conv.messages.pop();
        }
        renderMessages(conv.messages);
      }
    } else {
      console.error('Stream error:', e);
      // Show error in chat
      if (conv && conv.messages.length > 0) {
        const lastMsg = conv.messages[conv.messages.length - 1];
        if (lastMsg.role === 'assistant') {
          lastMsg.content = `Error: ${e.message}`;
          renderMessages(conv.messages);
        }
      }
    }
  } finally {
    window.removeEventListener('chat-chunk', chunkHandler);
    AppState.streaming = false;
    AppState.abortController = null;
  }
}

function stopStreaming() {
  if (AppState.abortController) {
    AppState.abortController.abort();
  }
}

// --- Event Handlers ---
document.addEventListener('DOMContentLoaded', async () => {
  await loadConfig();
  await loadConversations();
  await loadSkills();
  await loadModels();

  // Sidebar click delegation
  const sidebar = $('sidebar-conversations');
  if (sidebar) {
    sidebar.addEventListener('click', (e) => {
      const item = e.target.closest('.conversation-item');
      if (item && !e.target.classList.contains('conv-delete')) {
        selectConversation(item.dataset.id);
      }
      if (e.target.classList.contains('conv-delete')) {
        deleteConversation(e.target.dataset.id);
      }
    });
  }

  // New conversation button
  const newBtn = $('new-conversation-btn');
  if (newBtn) newBtn.addEventListener('click', newConversation);

  // Send message (Enter or button)
  const input = $('message-input');
  const sendBtn = $('send-btn');
  if (input) {
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });
  }
  if (sendBtn) sendBtn.addEventListener('click', sendMessage);

  // Stop button
  const stopBtn = $('stop-btn');
  if (stopBtn) stopBtn.addEventListener('click', stopStreaming);

  // Theme toggle
  const themeBtn = $('theme-toggle');
  if (themeBtn) themeBtn.addEventListener('click', toggleTheme);
});

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { AppState, streamFetch, sendMessage, stopStreaming };
}
