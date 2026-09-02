// app.js — Single-page chat application
// State management, streaming fetch, model picker, skills, conversation management, keyboard shortcuts

const state = {
    conversations: [],
    currentId: null,
    models: [],
    skills: [],
    config: {
        apiKey: '',
        defaultModel: '',
        theme: 'light'
    },
    streaming: false,
    abortController: null
};

// --- Utility functions ---

function $(id) { return document.getElementById(id); }

function qs(sel, ctx) { return (ctx || document).querySelector(sel); }

function qsa(sel, ctx) { return (ctx || document).querySelectorAll(sel); }

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function formatDate(ts) {
    return new Date(ts).toLocaleString();
}

// --- Theme ---

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    state.config.theme = theme;
}

function loadTheme() {
    const saved = localStorage.getItem('theme') || 'light';
    setTheme(saved);
}

// --- API helpers ---

async function apiFetch(path, options = {}) {
    const headers = options.headers || {};
    if (options.body && !(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
    }
    const res = await fetch(path, { ...options, headers });
    if (!res.ok) {
        const text = await res.text();
        throw new Error(`API error ${res.status}: ${text}`);
    }
    return res.json();
}

async function loadConfig() {
    try {
        state.config = await apiFetch('/api/config');
        if (state.config.theme) {
            setTheme(state.config.theme);
        }
    } catch (e) {
        console.warn('Could not load config, using defaults:', e);
    }
}

async function saveConfig() {
    try {
        await apiFetch('/api/config', {
            method: 'PUT',
            body: JSON.stringify(state.config)
        });
    } catch (e) {
        console.error('Failed to save config:', e);
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

async function loadConversations() {
    try {
        state.conversations = await apiFetch('/api/conversations');
        renderSidebar();
    } catch (e) {
        console.error('Failed to load conversations:', e);
    }
}

async function loadSkills() {
    try {
        state.skills = await apiFetch('/api/skills');
    } catch (e) {
        console.error('Failed to load skills:', e);
    }
}

// --- Model picker ---

function populateModelPicker() {
    const select = $('model-picker');
    if (!select) return;
    select.innerHTML = '';
    state.models.forEach(m => {
        const opt = document.createElement('option');
        opt.value = m.id;
        opt.textContent = `${m.name || m.id} (${m.context_length || '?'} ctx)`;
        if (m.id === state.config.defaultModel) opt.selected = true;
        select.appendChild(opt);
    });
}

// --- Sidebar ---

function renderSidebar() {
    const list = $('conversation-list');
    if (!list) return;
    list.innerHTML = '';
    state.conversations.forEach(conv => {
        const item = document.createElement('div');
        item.className = 'conversation-item' + (conv.id === state.currentId ? ' active' : '');
        item.dataset.id = conv.id;
        const title = conv.title || 'New conversation';
        item.innerHTML = `<span class="conv-title">${escapeHtml(title)}</span>`;
        item.addEventListener('click', () => switchConversation(conv.id));
        list.appendChild(item);
    });
}

async function switchConversation(id) {
    state.currentId = id;
    renderSidebar();
    // Load messages for this conversation
    try {
        const conv = await apiFetch(`/api/conversations/${id}`);
        renderMessages(conv.messages || []);
    } catch (e) {
        console.error('Failed to load conversation:', e);
    }
}

async function newConversation() {
    try {
        const conv = await apiFetch('/api/conversations', {
            method: 'POST',
            body: JSON.stringify({ title: 'New conversation' })
        });
        state.conversations.unshift(conv);
        state.currentId = conv.id;
        renderSidebar();
        renderMessages([]);
    } catch (e) {
        console.error('Failed to create conversation:', e);
    }
}

// --- Chat messages ---

function renderMessages(messages) {
    const container = $('message-container');
    if (!container) return;
    container.innerHTML = '';
    messages.forEach(msg => {
        const div = document.createElement('div');
        div.className = 'message ' + (msg.role === 'user' ? 'user-message' : 'assistant-message');
        div.innerHTML = `<div class="message-content">${escapeHtml(msg.content)}</div>`;
        container.appendChild(div);
    });
    container.scrollTop = container.scrollHeight;
}

// --- Settings modal ---

function openSettings() {
    const modal = $('settings-modal');
    if (!modal) return;
    // Populate with current config
    $('settings-api-key').value = state.config.apiKey || '';
    $('settings-default-model').value = state.config.defaultModel || '';
    $('settings-theme').value = state.config.theme || 'light';
    modal.style.display = 'flex';
}

function closeSettings() {
    const modal = $('settings-modal');
    if (modal) modal.style.display = 'none';
}

function saveSettings() {
    const apiKey = $('settings-api-key').value.trim();
    const defaultModel = $('settings-default-model').value;
    const theme = $('settings-theme').value;
    state.config.apiKey = apiKey;
    state.config.defaultModel = defaultModel;
    state.config.theme = theme;
    setTheme(theme);
    saveConfig();
    closeSettings();
    // Update model picker selection
    if ($('model-picker')) {
        $('model-picker').value = defaultModel;
    }
}

// --- Event listeners ---

document.addEventListener('DOMContentLoaded', async () => {
    loadTheme();
    await loadConfig();
    await loadModels();
    await loadConversations();
    await loadSkills();
    
    // Settings modal elements
    const settingsBtn = $('settings-btn');
    const settingsModal = $('settings-modal');
    const settingsClose = $('settings-close');
    const settingsSave = $('settings-save');
    const settingsCancel = $('settings-cancel');
    
    if (settingsBtn) settingsBtn.addEventListener('click', openSettings);
    if (settingsClose) settingsClose.addEventListener('click', closeSettings);
    if (settingsSave) settingsSave.addEventListener('click', saveSettings);
    if (settingsCancel) settingsCancel.addEventListener('click', closeSettings);
    
    // Close on backdrop click
    if (settingsModal) {
        settingsModal.addEventListener('click', (e) => {
            if (e.target === settingsModal) closeSettings();
        });
    }
    
    // New conversation button
    const newBtn = $('new-conversation-btn');
    if (newBtn) newBtn.addEventListener('click', newConversation);
    
    // Model picker change
    const modelPicker = $('model-picker');
    if (modelPicker) {
        modelPicker.addEventListener('change', () => {
            state.config.defaultModel = modelPicker.value;
            saveConfig();
        });
    }
    
    // Keyboard shortcuts
    document.addEventListener('keydown', handleKeyboardShortcuts);
});

function handleKeyboardShortcuts(e) {
    // Don't fire if typing in input/textarea (except for global shortcuts)
    const tag = e.target.tagName;
    const isInput = tag === 'INPUT' || tag === 'TEXTAREA' || e.target.isContentEditable;
    
    // Ctrl+Shift+O: Focus composer (global)
    if (e.ctrlKey && e.shiftKey && e.key === 'O') {
        e.preventDefault();
        const composer = $('composer');
        if (composer) composer.focus();
        return;
    }
    
    // Escape: Close modals or stop generation (global)
    if (e.key === 'Escape') {
        const modal = $('settings-modal');
        if (modal && modal.style.display === 'flex') {
            closeSettings();
            e.preventDefault();
            return;
        }
        // TODO: stop generation if streaming
    }
    
    if (isInput) return;
    
    // Ctrl+Shift+N: New conversation
    if (e.ctrlKey && e.shiftKey && e.key === 'N') {
        e.preventDefault();
        newConversation();
        return;
    }
    
    // Ctrl+Shift+,: Open settings
    if (e.ctrlKey && e.shiftKey && e.key === ',') {
        e.preventDefault();
        openSettings();
        return;
    }
    
    // Ctrl+Shift+E: Open skills
    if (e.ctrlKey && e.shiftKey && e.key === 'E') {
        e.preventDefault();
        // TODO: open skills drawer
        return;
    }
    
    // Ctrl+Shift+Delete: Clear all conversations
    if (e.ctrlKey && e.shiftKey && e.key === 'Delete') {
        e.preventDefault();
        if (confirm('Clear all conversations?')) {
            // TODO: implement clear
        }
        return;
    }
    
    // Ctrl+Shift+ArrowUp: Previous conversation
    if (e.ctrlKey && e.shiftKey && e.key === 'ArrowUp') {
        e.preventDefault();
        // TODO: navigate
        return;
    }
    
    // Ctrl+Shift+ArrowDown: Next conversation
    if (e.ctrlKey && e.shiftKey && e.key === 'ArrowDown') {
        e.preventDefault();
        // TODO: navigate
        return;
    }
    
    // Ctrl+Shift+S: Toggle theme
    if (e.ctrlKey && e.shiftKey && e.key === 'S') {
        e.preventDefault();
        const newTheme = state.config.theme === 'light' ? 'dark' : 'light';
        state.config.theme = newTheme;
        setTheme(newTheme);
        saveConfig();
        return;
    }
}

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { state, openSettings, closeSettings, saveSettings, loadConfig, setTheme };
}
