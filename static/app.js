// app.js - Frontend logic for Agentic Chat

let state = {
    conversations: [],
    currentConversationId: null,
    skills: [],
    models: [],
    config: {},
    streaming: false,
    abortController: null,
    theme: 'light',
};

// DOM references
const elements = {};

function init() {
    // Cache DOM elements
    elements.sidebar = document.getElementById('sidebar');
    elements.chatArea = document.getElementById('chat-area');
    elements.composer = document.getElementById('composer');
    elements.modelPicker = document.getElementById('model-picker');
    elements.settingsDrawer = document.getElementById('settings-drawer');
    elements.skillsDrawer = document.getElementById('skills-drawer');
    elements.logoutBtn = document.getElementById('logout-btn');

    // Load config and initial data
    loadConfig();
    loadConversations();
    loadSkills();
    loadModels();

    // Event listeners
    if (elements.logoutBtn) {
        elements.logoutBtn.addEventListener('click', handleLogout);
    }
}

async function handleLogout() {
    try {
        const resp = await fetch('/api/logout', { method: 'POST' });
        if (!resp.ok) throw new Error('Logout failed');
        // Clear any cached API key in the UI
        const apiKeyInput = document.getElementById('api-key-input');
        if (apiKeyInput) apiKeyInput.value = '';
        // Reload config to reflect cleared key
        await loadConfig();
        // Optionally show a message or redirect to settings
        showNotification('Logged out successfully');
    } catch (err) {
        showNotification('Logout failed: ' + err.message, 'error');
    }
}

async function loadConfig() {
    try {
        const resp = await fetch('/api/config');
        state.config = await resp.json();
        // Apply theme
        if (state.config.theme) {
            state.theme = state.config.theme;
            document.documentElement.setAttribute('data-theme', state.theme);
        }
    } catch (e) {
        console.error('Failed to load config', e);
    }
}

async function loadConversations() {
    try {
        const resp = await fetch('/api/conversations');
        state.conversations = await resp.json();
        renderSidebar();
    } catch (e) {
        console.error('Failed to load conversations', e);
    }
}

async function loadSkills() {
    try {
        const resp = await fetch('/api/skills');
        state.skills = await resp.json();
        renderSkills();
    } catch (e) {
        console.error('Failed to load skills', e);
    }
}

async function loadModels() {
    try {
        const resp = await fetch('/api/models');
        const data = await resp.json();
        state.models = data.data || [];
        renderModelPicker();
    } catch (e) {
        console.error('Failed to load models', e);
    }
}

function renderSidebar() {
    // Placeholder - actual implementation would update the conversation list
    console.log('Sidebar rendered with', state.conversations.length, 'conversations');
}

function renderSkills() {
    // Placeholder
    console.log('Skills rendered');
}

function renderModelPicker() {
    // Placeholder
    console.log('Model picker rendered');
}

function showNotification(message, type = 'info') {
    // Simple notification - could be enhanced
    alert(message);
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', init);
