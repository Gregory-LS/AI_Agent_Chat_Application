// Agentic Chat - Frontend Application
// State management, streaming fetch, UI updates

const state = {
    conversations: [],
    currentConversation: null,
    models: [],
    skills: [],
    config: {},
    user: null,
    darkMode: false,
    streaming: false,
    abortController: null
};

// DOM references (populated after DOMContentLoaded)
let els = {};

// Initialize application
document.addEventListener('DOMContentLoaded', async () => {
    // Cache DOM elements
    els = {
        sidebar: document.getElementById('sidebar'),
        chatArea: document.getElementById('chat-area'),
        messages: document.getElementById('messages'),
        composer: document.getElementById('composer'),
        sendBtn: document.getElementById('send-btn'),
        modelSelect: document.getElementById('model-select'),
        newChatBtn: document.getElementById('new-chat-btn'),
        settingsBtn: document.getElementById('settings-btn'),
        settingsDrawer: document.getElementById('settings-drawer'),
        settingsClose: document.getElementById('settings-close'),
        apiKeyInput: document.getElementById('api-key'),
        saveSettingsBtn: document.getElementById('save-settings'),
        themeToggle: document.getElementById('theme-toggle'),
        balanceDisplay: document.getElementById('balance-display'),
        loginBtn: document.getElementById('login-btn'),
        loginModal: document.getElementById('login-modal'),
        loginForm: document.getElementById('login-form'),
        registerForm: document.getElementById('register-form'),
        userDisplay: document.getElementById('user-display'),
        logoutBtn: document.getElementById('logout-btn'),
        searchInput: document.getElementById('search-input'),
        conversationList: document.getElementById('conversation-list')
    };

    // Load initial data
    await loadConfig();
    await checkAuth();
    await loadConversations();
    await loadModels();
    await loadSkills();
    await updateBalance();

    // Apply theme
    applyTheme();

    // Setup event listeners
    setupEventListeners();

    // Start with a new conversation if none selected
    if (!state.currentConversation && state.conversations.length === 0) {
        newConversation();
    } else if (state.conversations.length > 0) {
        selectConversation(state.conversations[0].id);
    }
});

async function loadConfig() {
    try {
        const resp = await fetch('/api/config');
        state.config = await resp.json();
        if (state.config.darkMode) {
            state.darkMode = true;
        }
        if (state.config.api_key) {
            els.apiKeyInput.value = state.config.api_key;
        }
        if (state.config.defaultModel) {
            // Will be applied when models load
        }
    } catch (e) {
        console.error('Failed to load config:', e);
    }
}

async function checkAuth() {
    try {
        const resp = await fetch('/api/auth/me');
        const data = await resp.json();
        state.user = data.user;
        updateAuthUI();
    } catch (e) {
        console.error('Auth check failed:', e);
    }
}

function updateAuthUI() {
    if (state.user) {
        els.loginBtn.style.display = 'none';
        els.userDisplay.textContent = state.user;
        els.userDisplay.style.display = 'inline';
        els.logoutBtn.style.display = 'inline';
    } else {
        els.loginBtn.style.display = 'inline';
        els.userDisplay.textContent = '';
        els.userDisplay.style.display = 'none';
        els.logoutBtn.style.display = 'none';
    }
}

async function loadConversations() {
    try {
        const resp = await fetch('/api/conversations');
        state.conversations = await resp.json();
        renderConversationList();
    } catch (e) {
        console.error('Failed to load conversations:', e);
    }
}

async function loadModels() {
    try {
        const resp = await fetch('/api/models');
        const data = await resp.json();
        state.models = data.data || [];
        populateModelSelect();
    } catch (e) {
        console.error('Failed to load models:', e);
    }
}

async function loadSkills() {
    try {
        const resp = await fetch('/api/skills');
        state.skills = await resp.json();
        renderSkills();
    } catch (e) {
        console.error('Failed to load skills:', e);
    }
}

async function updateBalance() {
    try {
        const resp = await fetch('/api/balance');
        const data = await resp.json();
        if (data.credits !== undefined) {
            els.balanceDisplay.textContent = `Balance: ${data.credits.toFixed(4)} credits`;
        }
    } catch (e) {
        console.error('Failed to fetch balance:', e);
    }
}

function populateModelSelect() {
    els.modelSelect.innerHTML = '';
    state.models.forEach(model => {
        const opt = document.createElement('option');
        opt.value = model.id;
        opt.textContent = model.id;
        if (model.id === state.config.defaultModel) {
            opt.selected = true;
        }
        els.modelSelect.appendChild(opt);
    });
}

function renderConversationList() {
    els.conversationList.innerHTML = '';
    state.conversations.forEach(conv => {
        const item = document.createElement('div');
        item.className = 'conversation-item';
        if (state.currentConversation && state.currentConversation.id === conv.id) {
            item.classList.add('active');
        }
        item.textContent = conv.title || 'Untitled';
        item.dataset.id = conv.id;
        item.addEventListener('click', () => selectConversation(conv.id));
        els.conversationList.appendChild(item);
    });
}

function renderSkills() {
    // Skills UI placeholder
    console.log('Skills loaded:', state.skills.length);
}

function applyTheme() {
    if (state.darkMode) {
        document.documentElement.setAttribute('data-theme', 'dark');
        els.themeToggle.textContent = '☀️ Light';
    } else {
        document.documentElement.removeAttribute('data-theme');
        els.themeToggle.textContent = '🌙 Dark';
    }
}

function setupEventListeners() {
    // New conversation
    els.newChatBtn.addEventListener('click', newConversation);

    // Send message
    els.sendBtn.addEventListener('click', sendMessage);
    els.composer.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Settings drawer
    els.settingsBtn.addEventListener('click', () => {
        els.settingsDrawer.classList.add('open');
    });
    els.settingsClose.addEventListener('click', () => {
        els.settingsDrawer.classList.remove('open');
    });

    // Save settings
    els.saveSettingsBtn.addEventListener('click', saveSettings);

    // Theme toggle
    els.themeToggle.addEventListener('click', toggleTheme);

    // Login modal
    els.loginBtn.addEventListener('click', () => {
        els.loginModal.classList.add('open');
    });

    // Login form
    els.loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('login-username').value;
        const password = document.getElementById('login-password').value;
        await login(username, password);
    });

    // Register form
    els.registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('register-username').value;
        const password = document.getElementById('register-password').value;
        await register(username, password);
    });

    // Logout
    els.logoutBtn.addEventListener('click', logout);

    // Search conversations
    els.searchInput.addEventListener('input', filterConversations);

    // Close modals on outside click
    window.addEventListener('click', (e) => {
        if (e.target === els.loginModal) {
            els.loginModal.classList.remove('open');
        }
    });
}

function newConversation() {
    state.currentConversation = {
        id: 'new',
        title: 'New conversation',
        messages: [],
        model: els.modelSelect.value || 'openai/gpt-4o-mini'
    };
    renderMessages();
    renderConversationList();
}

async function selectConversation(id) {
    try {
        const resp = await fetch(`/api/conversations/${id}`);
        state.currentConversation = await resp.json();
        renderMessages();
        renderConversationList();
    } catch (e) {
        console.error('Failed to load conversation:', e);
    }
}

async function sendMessage() {
    const text = els.composer.value.trim();
    if (!text || state.streaming) return;

    // Add user message
    const userMessage = { role: 'user', content: text };
    if (state.currentConversation) {
        state.currentConversation.messages.push(userMessage);
    }
    renderMessages();
    els.composer.value = '';

    // Scroll to bottom
    scrollToBottom();

    // Prepare for streaming
    state.streaming = true;
    state.abortController = new AbortController();

    // Create assistant message placeholder
    const assistantMessage = { role: 'assistant', content: '' };
    if (state.currentConversation) {
        state.currentConversation.messages.push(assistantMessage);
    }
    renderMessages();

    const messageEl = els.messages.lastElementChild;
    const contentEl = messageEl ? messageEl.querySelector('.message-content') : null;

    try {
        const resp = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                messages: state.currentConversation ? state.currentConversation.messages.slice(0, -1) : [],
                model: els.modelSelect.value || 'openai/gpt-4o-mini',
                stream: true
            }),
            signal: state.abortController.signal
        });

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
                    if (data === '[DONE]') continue;
                    try {
                        const parsed = JSON.parse(data);
                        const choices = parsed.choices;
                        if (choices && choices[0] && choices[0].delta && choices[0].delta.content) {
                            assistantMessage.content += choices[0].delta.content;
                            if (contentEl) {
                                contentEl.textContent = assistantMessage.content;
                            }
                            scrollToBottom();
                        }
                    } catch (e) {
                        // Skip non-JSON lines
                    }
                }
            }
        }

        // Save conversation if new
        if (state.currentConversation && state.currentConversation.id === 'new') {
            const title = text.slice(0, 50) + (text.length > 50 ? '...' : '');
            const resp2 = await fetch('/api/conversations', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title: title,
                    model: els.modelSelect.value || 'openai/gpt-4o-mini'
                })
            });
            const saved = await resp2.json();
            state.currentConversation.id = saved.id;
            // Update conversation with messages
            await fetch(`/api/conversations/${saved.id}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    messages: state.currentConversation.messages,
                    title: title
                })
            });
            await loadConversations();
        } else if (state.currentConversation && state.currentConversation.id !== 'new') {
            // Update existing conversation
            await fetch(`/api/conversations/${state.currentConversation.id}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    messages: state.currentConversation.messages
                })
            });
        }
    } catch (e) {
        if (e.name === 'AbortError') {
            console.log('Stream cancelled');
        } else {
            console.error('Stream error:', e);
            if (contentEl) {
                contentEl.textContent = 'Error: Failed to get response';
            }
        }
    } finally {
        state.streaming = false;
        state.abortController = null;
    }
}

function renderMessages() {
    els.messages.innerHTML = '';
    if (!state.currentConversation) return;

    state.currentConversation.messages.forEach(msg => {
        const div = document.createElement('div');
        div.className = `message message-${msg.role}`;
        const content = document.createElement('div');
        content.className = 'message-content';
        content.textContent = msg.content;
        div.appendChild(content);
        els.messages.appendChild(div);
    });
}

function scrollToBottom() {
    els.messages.scrollTop = els.messages.scrollHeight;
}

function filterConversations() {
    const query = els.searchInput.value.toLowerCase();
    const items = els.conversationList.querySelectorAll('.conversation-item');
    items.forEach(item => {
        const title = item.textContent.toLowerCase();
        item.style.display = title.includes(query) ? 'block' : 'none';
    });
}

async function saveSettings() {
    const apiKey = els.apiKeyInput.value.trim();
    const config = { api_key: apiKey, darkMode: state.darkMode };
    try {
        await fetch('/api/config', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        alert('Settings saved!');
    } catch (e) {
        console.error('Failed to save settings:', e);
    }
}

function toggleTheme() {
    state.darkMode = !state.darkMode;
    applyTheme();
}

async function login(username, password) {
    try {
        const resp = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await resp.json();
        if (resp.ok) {
            state.user = data.user;
            updateAuthUI();
            els.loginModal.classList.remove('open');
            document.getElementById('login-username').value = '';
            document.getElementById('login-password').value = '';
            // Reload conversations to show user-specific ones
            await loadConversations();
        } else {
            alert(data.error || 'Login failed');
        }
    } catch (e) {
        console.error('Login error:', e);
        alert('Login failed');
    }
}

async function register(username, password) {
    try {
        const resp = await fetch('/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await resp.json();
        if (resp.ok) {
            state.user = data.user;
            updateAuthUI();
            els.loginModal.classList.remove('open');
            document.getElementById('register-username').value = '';
            document.getElementById('register-password').value = '';
            await loadConversations();
        } else {
            alert(data.error || 'Registration failed');
        }
    } catch (e) {
        console.error('Registration error:', e);
        alert('Registration failed');
    }
}

async function logout() {
    try {
        await fetch('/api/auth/logout', { method: 'POST' });
        state.user = null;
        updateAuthUI();
        await loadConversations();
    } catch (e) {
        console.error('Logout error:', e);
    }
}

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { state, login, register, logout, checkAuth };
}
