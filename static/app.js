// app.js — frontend state management and streaming fetch

const state = {
    conversations: [],
    currentConversationId: null,
    messages: [],
    models: [],
    skills: [],
    config: {},
    streaming: false,
    abortController: null,
    theme: localStorage.getItem('theme') || 'light'
};

// DOM references (populated on DOMContentLoaded)
let els = {};

function init() {
    els = {
        sidebar: document.getElementById('sidebar'),
        chatArea: document.getElementById('chat-area'),
        composer: document.getElementById('composer'),
        modelPicker: document.getElementById('model-picker'),
        settingsDrawer: document.getElementById('settings-drawer'),
        skillsDrawer: document.getElementById('skills-drawer'),
        newChatBtn: document.getElementById('new-chat-btn'),
        settingsBtn: document.getElementById('settings-btn'),
        skillsBtn: document.getElementById('skills-btn'),
        closeSettingsBtn: document.getElementById('close-settings-btn'),
        closeSkillsBtn: document.getElementById('close-skills-btn'),
        themeToggle: document.getElementById('theme-toggle'),
        apiKeyInput: document.getElementById('api-key-input'),
        defaultModelSelect: document.getElementById('default-model-select'),
        balanceInfo: document.getElementById('balance-info'),
        conversationList: document.getElementById('conversation-list'),
        messageContainer: document.getElementById('message-container'),
        sendBtn: document.getElementById('send-btn'),
        stopBtn: document.getElementById('stop-btn'),
        logoutBtn: document.getElementById('logout-btn'),
        searchInput: document.getElementById('search-input')
    };

    applyTheme(state.theme);
    loadConfig();
    loadConversations();
    loadModels();
    loadSkills();
    bindEvents();
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    state.theme = theme;
}

function toggleTheme() {
    const newTheme = state.theme === 'light' ? 'dark' : 'light';
    applyTheme(newTheme);
}

async function apiFetch(url, options = {}) {
    const response = await fetch(url, options);
    if (!response.ok) {
        const err = await response.json().catch(() => ({error: response.statusText}));
        throw new Error(err.error || 'API error');
    }
    return response.json();
}

async function loadConfig() {
    try {
        state.config = await apiFetch('/api/config');
        if (els.apiKeyInput) els.apiKeyInput.value = state.config.api_key || '';
        if (els.defaultModelSelect) els.defaultModelSelect.value = state.config.default_model || '';
    } catch (e) {
        console.error('Failed to load config:', e);
    }
}

async function saveConfig(updates) {
    try {
        state.config = await apiFetch('/api/config', {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(updates)
        });
    } catch (e) {
        console.error('Failed to save config:', e);
    }
}

async function loadConversations() {
    try {
        state.conversations = await apiFetch('/api/conversations');
        renderConversationList();
    } catch (e) {
        console.error('Failed to load conversations:', e);
    }
}

async function loadModels() {
    try {
        state.models = await apiFetch('/api/models');
        populateModelPicker();
    } catch (e) {
        console.error('Failed to load models:', e);
    }
}

async function loadSkills() {
    try {
        state.skills = await apiFetch('/api/skills');
        renderSkills();
    } catch (e) {
        console.error('Failed to load skills:', e);
    }
}

function populateModelPicker() {
    const select = els.defaultModelSelect;
    if (!select) return;
    select.innerHTML = '<option value="">Default model</option>';
    state.models.forEach(m => {
        const opt = document.createElement('option');
        opt.value = m.id;
        opt.textContent = m.name || m.id;
        select.appendChild(opt);
    });
    if (state.config.default_model) {
        select.value = state.config.default_model;
    }
}

function renderConversationList() {
    const list = els.conversationList;
    if (!list) return;
    list.innerHTML = '';
    state.conversations.forEach(conv => {
        const item = document.createElement('div');
        item.className = 'conversation-item';
        item.dataset.id = conv.id;
        item.textContent = conv.title || 'Untitled';
        item.addEventListener('click', () => selectConversation(conv.id));
        if (conv.id === state.currentConversationId) {
            item.classList.add('active');
        }
        list.appendChild(item);
    });
}

function renderSkills() {
    // Skills rendering logic placeholder
}

async function selectConversation(id) {
    state.currentConversationId = id;
    try {
        const conv = await apiFetch(`/api/conversations/${id}`);
        state.messages = conv.messages || [];
        renderMessages();
        renderConversationList();
    } catch (e) {
        console.error('Failed to load conversation:', e);
    }
}

async function newConversation() {
    state.currentConversationId = null;
    state.messages = [];
    renderMessages();
    renderConversationList();
}

function renderMessages() {
    const container = els.messageContainer;
    if (!container) return;
    container.innerHTML = '';
    state.messages.forEach(msg => {
        const div = document.createElement('div');
        div.className = `message message-${msg.role}`;
        div.textContent = msg.content;
        container.appendChild(div);
    });
    container.scrollTop = container.scrollHeight;
}

async function sendMessage() {
    const input = els.composer;
    if (!input || !input.value.trim()) return;
    const content = input.value.trim();
    input.value = '';

    const userMsg = { role: 'user', content };
    state.messages.push(userMsg);
    renderMessages();

    const model = els.defaultModelSelect ? els.defaultModelSelect.value : '';
    const payload = {
        messages: state.messages,
        model: model || undefined,
        stream: true
    };

    state.abortController = new AbortController();
    state.streaming = true;
    if (els.stopBtn) els.stopBtn.style.display = 'inline-block';
    if (els.sendBtn) els.sendBtn.style.display = 'none';

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload),
            signal: state.abortController.signal
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({error: response.statusText}));
            throw new Error(err.error || 'Chat API error');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let assistantMsg = { role: 'assistant', content: '' };
        state.messages.push(assistantMsg);

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        if (data.type === 'chunk') {
                            assistantMsg.content += data.content || '';
                            renderMessages();
                        } else if (data.type === 'done') {
                            // final
                        } else if (data.type === 'error') {
                            throw new Error(data.content);
                        } else if (data.type === 'usage') {
                            // token usage info
                        }
                    } catch (e) {
                        if (e.message !== 'Chat API error') console.error('SSE parse error:', e);
                    }
                }
            }
        }
        renderMessages();
    } catch (e) {
        if (e.name === 'AbortError') {
            // user cancelled
        } else {
            console.error('Chat error:', e);
        }
    } finally {
        state.streaming = false;
        state.abortController = null;
        if (els.stopBtn) els.stopBtn.style.display = 'none';
        if (els.sendBtn) els.sendBtn.style.display = 'inline-block';
    }
}

function stopStreaming() {
    if (state.abortController) {
        state.abortController.abort();
    }
}

async function checkBalance() {
    try {
        const data = await apiFetch('/api/balance');
        if (els.balanceInfo) {
            els.balanceInfo.textContent = `Credits: ${data.credits}, Usage: ${data.usage}, Total: ${data.total}`;
        }
    } catch (e) {
        console.error('Balance check failed:', e);
    }
}

async function handleLogout() {
    try {
        await fetch('/api/logout', { method: 'POST' });
        // Reload page to reset all state
        window.location.reload();
    } catch (e) {
        console.error('Logout failed:', e);
    }
}

function bindEvents() {
    if (els.newChatBtn) els.newChatBtn.addEventListener('click', newConversation);
    if (els.settingsBtn) els.settingsBtn.addEventListener('click', () => {
        if (els.settingsDrawer) els.settingsDrawer.classList.toggle('open');
        checkBalance();
    });
    if (els.closeSettingsBtn) els.closeSettingsBtn.addEventListener('click', () => {
        if (els.settingsDrawer) els.settingsDrawer.classList.remove('open');
    });
    if (els.skillsBtn) els.skillsBtn.addEventListener('click', () => {
        if (els.skillsDrawer) els.skillsDrawer.classList.toggle('open');
    });
    if (els.closeSkillsBtn) els.closeSkillsBtn.addEventListener('click', () => {
        if (els.skillsDrawer) els.skillsDrawer.classList.remove('open');
    });
    if (els.themeToggle) els.themeToggle.addEventListener('click', toggleTheme);
    if (els.apiKeyInput) els.apiKeyInput.addEventListener('change', () => {
        saveConfig({ api_key: els.apiKeyInput.value });
    });
    if (els.defaultModelSelect) els.defaultModelSelect.addEventListener('change', () => {
        saveConfig({ default_model: els.defaultModelSelect.value });
    });
    if (els.sendBtn) els.sendBtn.addEventListener('click', sendMessage);
    if (els.composer) els.composer.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    if (els.stopBtn) els.stopBtn.addEventListener('click', stopStreaming);
    if (els.logoutBtn) els.logoutBtn.addEventListener('click', handleLogout);
    if (els.searchInput) els.searchInput.addEventListener('input', (e) => {
        filterConversations(e.target.value);
    });
}

function filterConversations(query) {
    const items = document.querySelectorAll('.conversation-item');
    const lower = query.toLowerCase();
    items.forEach(item => {
        const match = item.textContent.toLowerCase().includes(lower);
        item.style.display = match ? 'block' : 'none';
    });
}

document.addEventListener('DOMContentLoaded', init);
