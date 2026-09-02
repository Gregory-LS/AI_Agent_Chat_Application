// app.js - Frontend state management, streaming fetch, UI interactions

const API_BASE = '';

let state = {
    config: {},
    conversations: [],
    currentConversationId: null,
    skills: [],
    models: [],
    theme: 'light',
    streaming: false,
    abortController: null,
};

// DOM references (set after DOM ready)
let dom = {};

function initDOM() {
    dom = {
        sidebar: document.getElementById('sidebar'),
        chatArea: document.getElementById('chat-area'),
        composer: document.getElementById('composer'),
        modelPicker: document.getElementById('model-picker'),
        settingsDrawer: document.getElementById('settings-drawer'),
        skillsDrawer: document.getElementById('skills-drawer'),
        themeToggle: document.getElementById('theme-toggle'),
        logoutBtn: document.getElementById('logout-btn'),
    };
}

async function fetchJSON(url, options = {}) {
    const res = await fetch(url, {
        headers: { 'Content-Type': 'application/json', ...options.headers },
        ...options,
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ error: res.statusText }));
        throw new Error(err.error || 'Request failed');
    }
    return res.json();
}

// --- Config ---
async function loadConfig() {
    const config = await fetchJSON('/api/config');
    state.config = config;
    if (config.theme) {
        setTheme(config.theme);
    }
    return config;
}

async function saveConfig(updates) {
    const config = await fetchJSON('/api/config', {
        method: 'PUT',
        body: JSON.stringify(updates),
    });
    state.config = config;
    return config;
}

// --- Theme ---
function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    state.theme = theme;
    if (dom.themeToggle) {
        dom.themeToggle.textContent = theme === 'dark' ? '☀️' : '🌙';
    }
}

function toggleTheme() {
    const newTheme = state.theme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    saveConfig({ theme: newTheme });
}

// --- Conversations ---
async function loadConversations() {
    const conversations = await fetchJSON('/api/conversations');
    state.conversations = conversations;
    renderConversationList();
}

async function createConversation() {
    const conv = await fetchJSON('/api/conversations', {
        method: 'POST',
        body: JSON.stringify({
            title: 'New conversation',
            messages: [],
            model: state.config.default_model || '',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
        }),
    });
    state.conversations.unshift(conv);
    state.currentConversationId = conv.id;
    renderConversationList();
    loadConversation(conv.id);
}

async function loadConversation(id) {
    const conv = await fetchJSON(`/api/conversations/${id}`);
    state.currentConversationId = id;
    renderChat(conv);
}

async function deleteConversation(id) {
    await fetchJSON(`/api/conversations/${id}`, { method: 'DELETE' });
    state.conversations = state.conversations.filter(c => c.id !== id);
    if (state.currentConversationId === id) {
        state.currentConversationId = null;
        renderChat(null);
    }
    renderConversationList();
}

async function renameConversation(id, newTitle) {
    await fetchJSON(`/api/conversations/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({ title: newTitle }),
    });
    const conv = state.conversations.find(c => c.id === id);
    if (conv) conv.title = newTitle;
    renderConversationList();
}

// --- Skills ---
async function loadSkills() {
    const skills = await fetchJSON('/api/skills');
    state.skills = skills;
    renderSkillsList();
}

async function toggleSkill(id, enabled) {
    await fetchJSON(`/api/skills/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({ enabled }),
    });
    const skill = state.skills.find(s => s.id === id);
    if (skill) skill.enabled = enabled;
    renderSkillsList();
}

// --- Logout ---
async function logout() {
    try {
        await fetchJSON('/api/logout', { method: 'POST' });
        state.config.api_key = '';
        alert('Logged out successfully. API key has been cleared.');
        // Optionally redirect to settings
        openSettings();
    } catch (err) {
        alert('Logout failed: ' + err.message);
    }
}

// --- UI Rendering ---
function renderConversationList() {
    const list = document.getElementById('conversation-list');
    if (!list) return;
    list.innerHTML = state.conversations.map(conv => `
        <div class="conversation-item ${conv.id === state.currentConversationId ? 'active' : ''}" data-id="${conv.id}">
            <span class="conv-title">${escapeHtml(conv.title)}</span>
            <button class="btn-icon delete-conv" title="Delete">🗑️</button>
        </div>
    `).join('');
    // Attach event listeners
    list.querySelectorAll('.conversation-item').forEach(item => {
        item.addEventListener('click', (e) => {
            if (e.target.closest('.delete-conv')) return;
            loadConversation(item.dataset.id);
        });
        item.querySelector('.delete-conv').addEventListener('click', (e) => {
            e.stopPropagation();
            if (confirm('Delete this conversation?')) {
                deleteConversation(item.dataset.id);
            }
        });
    });
}

function renderChat(conv) {
    const chatArea = dom.chatArea;
    if (!chatArea) return;
    if (!conv) {
        chatArea.innerHTML = '<div class="empty-state">Select a conversation or start a new one</div>';
        return;
    }
    chatArea.innerHTML = conv.messages.map(msg => `
        <div class="message ${msg.role}">
            <div class="message-role">${escapeHtml(msg.role)}</div>
            <div class="message-content">${escapeHtml(msg.content)}</div>
        </div>
    `).join('');
    chatArea.scrollTop = chatArea.scrollHeight;
}

function renderSkillsList() {
    const list = document.getElementById('skills-list');
    if (!list) return;
    list.innerHTML = state.skills.map(skill => `
        <div class="skill-item">
            <label>
                <input type="checkbox" ${skill.enabled ? 'checked' : ''} data-id="${skill.id}">
                ${escapeHtml(skill.name)}
            </label>
        </div>
    `).join('');
    list.querySelectorAll('input[type="checkbox"]').forEach(cb => {
        cb.addEventListener('change', () => {
            toggleSkill(cb.dataset.id, cb.checked);
        });
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// --- Drawers ---
function openSettings() {
    const drawer = dom.settingsDrawer;
    if (drawer) {
        drawer.classList.add('open');
        // Populate settings fields
        const apiKeyInput = document.getElementById('api-key-input');
        if (apiKeyInput) apiKeyInput.value = state.config.api_key || '';
        const defaultModelInput = document.getElementById('default-model-input');
        if (defaultModelInput) defaultModelInput.value = state.config.default_model || '';
    }
}

function closeSettings() {
    const drawer = dom.settingsDrawer;
    if (drawer) drawer.classList.remove('open');
}

function openSkills() {
    const drawer = dom.skillsDrawer;
    if (drawer) drawer.classList.add('open');
}

function closeSkills() {
    const drawer = dom.skillsDrawer;
    if (drawer) drawer.classList.remove('open');
}

// --- Streaming Chat ---
async function sendMessage(content) {
    if (!state.currentConversationId) {
        await createConversation();
    }
    const conv = state.conversations.find(c => c.id === state.currentConversationId);
    if (!conv) return;

    // Add user message
    conv.messages.push({ role: 'user', content });
    renderChat(conv);
    saveConversation(conv);

    // Start streaming
    state.abortController = new AbortController();
    state.streaming = true;

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model: conv.model || state.config.default_model,
                messages: conv.messages,
                stream: true,
            }),
            signal: state.abortController.signal,
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let assistantMessage = { role: 'assistant', content: '' };
        conv.messages.push(assistantMessage);

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const event = JSON.parse(line.slice(6));
                        if (event.type === 'chunk') {
                            assistantMessage.content += event.content || '';
                            renderChat(conv);
                        } else if (event.type === 'done') {
                            // Final
                            saveConversation(conv);
                        } else if (event.type === 'error') {
                            console.error('Stream error:', event.error);
                            assistantMessage.content += '\n[Error: ' + event.error + ']';
                            renderChat(conv);
                        }
                    } catch (e) {
                        // Ignore parse errors
                    }
                }
            }
        }
        saveConversation(conv);
    } catch (err) {
        if (err.name === 'AbortError') {
            // User stopped
            saveConversation(conv);
        } else {
            console.error('Chat error:', err);
        }
    } finally {
        state.streaming = false;
        state.abortController = null;
    }
}

function stopStreaming() {
    if (state.abortController) {
        state.abortController.abort();
    }
}

async function saveConversation(conv) {
    await fetchJSON(`/api/conversations/${conv.id}`, {
        method: 'PATCH',
        body: JSON.stringify({
            messages: conv.messages,
            updated_at: new Date().toISOString(),
        }),
    });
}

// --- Event Binding ---
document.addEventListener('DOMContentLoaded', async () => {
    initDOM();

    // Load initial data
    await loadConfig();
    await loadConversations();
    await loadSkills();

    // Theme toggle
    if (dom.themeToggle) {
        dom.themeToggle.addEventListener('click', toggleTheme);
    }

    // Logout button
    if (dom.logoutBtn) {
        dom.logoutBtn.addEventListener('click', logout);
    }

    // New conversation button
    const newConvBtn = document.getElementById('new-conv-btn');
    if (newConvBtn) {
        newConvBtn.addEventListener('click', createConversation);
    }

    // Settings button
    const settingsBtn = document.getElementById('settings-btn');
    if (settingsBtn) {
        settingsBtn.addEventListener('click', openSettings);
    }

    // Skills button
    const skillsBtn = document.getElementById('skills-btn');
    if (skillsBtn) {
        skillsBtn.addEventListener('click', openSkills);
    }

    // Composer form
    const composerForm = document.getElementById('composer-form');
    if (composerForm) {
        composerForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const input = document.getElementById('message-input');
            if (input && input.value.trim()) {
                sendMessage(input.value.trim());
                input.value = '';
            }
        });
    }

    // Stop button
    const stopBtn = document.getElementById('stop-btn');
    if (stopBtn) {
        stopBtn.addEventListener('click', stopStreaming);
    }
});
