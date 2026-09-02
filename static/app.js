// app.js — Claude-style AI chat frontend
// State management, streaming fetch, model picker, skills, conversation management, keyboard shortcuts

import { state, setState, getState } from './state.js';

// ============================================================
// State management
// ============================================================

const state = {
    apiKey: localStorage.getItem('openrouter_api_key') || '',
    defaultModel: localStorage.getItem('default_model') || '',
    conversations: [],
    currentConversationId: null,
    messages: [],
    skills: [],
    activeSkills: [],
    models: [],
    theme: localStorage.getItem('theme') || 'light',
    streaming: false,
    abortController: null,
    composerText: '',
    composerAttachments: [],
    isSettingsOpen: false,
    isSkillsOpen: false,
    isModelPickerOpen: false,
    balance: null,
    conversationSearchQuery: '',
    modelSearchQuery: '',
    selectedProvider: 'all',
    showAllModels: false,
};

function setState(updates) {
    Object.assign(state, updates);
    render();
}

function getState() {
    return state;
}

// ============================================================
// Keyboard shortcuts (FIX #264)
// ============================================================

document.addEventListener('keydown', function(e) {
    // Ignore if user is typing in an input/textarea (except for shortcuts that should work globally)
    const tag = e.target.tagName.toLowerCase();
    const isInput = tag === 'input' || tag === 'textarea' || tag === 'select' || e.target.isContentEditable;

    // Ctrl+Shift+O — Focus composer (works even in inputs)
    if (e.ctrlKey && e.shiftKey && e.key === 'O') {
        e.preventDefault();
        focusComposer();
        return;
    }

    // Escape — Close modals/drawers or stop generation (works everywhere)
    if (e.key === 'Escape') {
        e.preventDefault();
        if (state.streaming) {
            stopGeneration();
        } else if (state.isSettingsOpen) {
            closeSettings();
        } else if (state.isSkillsOpen) {
            closeSkills();
        } else if (state.isModelPickerOpen) {
            closeModelPicker();
        }
        return;
    }

    // If inside an input, don't handle other shortcuts
    if (isInput) return;

    // Ctrl+Shift+N — New conversation
    if (e.ctrlKey && e.shiftKey && e.key === 'N') {
        e.preventDefault();
        newConversation();
        return;
    }

    // Ctrl+Shift+, — Open settings
    if (e.ctrlKey && e.shiftKey && e.key === ',') {
        e.preventDefault();
        openSettings();
        return;
    }

    // Ctrl+Shift+E — Open skills
    if (e.ctrlKey && e.shiftKey && e.key === 'E') {
        e.preventDefault();
        openSkills();
        return;
    }

    // Ctrl+Shift+Delete — Clear conversations
    if (e.ctrlKey && e.shiftKey && e.key === 'Delete') {
        e.preventDefault();
        clearConversations();
        return;
    }

    // Ctrl+Shift+ArrowUp — Previous conversation
    if (e.ctrlKey && e.shiftKey && e.key === 'ArrowUp') {
        e.preventDefault();
        navigateConversation(-1);
        return;
    }

    // Ctrl+Shift+ArrowDown — Next conversation
    if (e.ctrlKey && e.shiftKey && e.key === 'ArrowDown') {
        e.preventDefault();
        navigateConversation(1);
        return;
    }

    // Ctrl+Shift+S — Toggle theme
    if (e.ctrlKey && e.shiftKey && e.key === 'S') {
        e.preventDefault();
        toggleTheme();
        return;
    }
});

function focusComposer() {
    const composer = document.getElementById('composer');
    if (composer) {
        composer.focus();
        // Move cursor to end
        const len = composer.value.length;
        composer.setSelectionRange(len, len);
    }
}

function stopGeneration() {
    if (state.abortController) {
        state.abortController.abort();
        setState({ streaming: false, abortController: null });
    }
}

function closeSettings() {
    setState({ isSettingsOpen: false });
}

function closeSkills() {
    setState({ isSkillsOpen: false });
}

function closeModelPicker() {
    setState({ isModelPickerOpen: false });
}

function newConversation() {
    // Save current conversation if any
    if (state.currentConversationId) {
        saveConversation();
    }
    setState({
        currentConversationId: null,
        messages: [],
        composerText: '',
        composerAttachments: [],
    });
    focusComposer();
}

function openSettings() {
    setState({ isSettingsOpen: true });
    fetchBalance();
}

function openSkills() {
    setState({ isSkillsOpen: true });
    fetchSkills();
}

function clearConversations() {
    if (confirm('Are you sure you want to delete all conversations? This cannot be undone.')) {
        // Delete all conversations via API
        const promises = state.conversations.map(conv =>
            fetch(`/api/conversations/${conv.id}`, { method: 'DELETE' })
        );
        Promise.all(promises).then(() => {
            setState({
                conversations: [],
                currentConversationId: null,
                messages: [],
            });
        }).catch(err => console.error('Failed to clear conversations:', err));
    }
}

function navigateConversation(direction) {
    const convs = state.conversations;
    if (convs.length === 0) return;
    const currentIndex = convs.findIndex(c => c.id === state.currentConversationId);
    let newIndex;
    if (currentIndex === -1) {
        newIndex = direction > 0 ? 0 : convs.length - 1;
    } else {
        newIndex = (currentIndex + direction + convs.length) % convs.length;
    }
    const conv = convs[newIndex];
    if (conv) {
        loadConversation(conv.id);
    }
}

function toggleTheme() {
    const newTheme = state.theme === 'light' ? 'dark' : 'light';
    localStorage.setItem('theme', newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
    setState({ theme: newTheme });
}

// ============================================================
// API helpers
// ============================================================

async function fetchModels() {
    try {
        const response = await fetch('/api/models');
        const models = await response.json();
        setState({ models });
    } catch (err) {
        console.error('Failed to fetch models:', err);
    }
}

async function fetchBalance() {
    try {
        const response = await fetch('/api/balance');
        const balance = await response.json();
        setState({ balance });
    } catch (err) {
        console.error('Failed to fetch balance:', err);
    }
}

async function fetchConversations() {
    try {
        const response = await fetch('/api/conversations');
        const conversations = await response.json();
        setState({ conversations });
    } catch (err) {
        console.error('Failed to fetch conversations:', err);
    }
}

async function fetchConversation(id) {
    try {
        const response = await fetch(`/api/conversations/${id}`);
        const data = await response.json();
        setState({ currentConversationId: id, messages: data.messages || [] });
    } catch (err) {
        console.error('Failed to fetch conversation:', err);
    }
}

async function saveConversation() {
    if (!state.currentConversationId || state.messages.length === 0) return;
    try {
        await fetch(`/api/conversations/${state.currentConversationId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ messages: state.messages }),
        });
    } catch (err) {
        console.error('Failed to save conversation:', err);
    }
}

async function fetchSkills() {
    try {
        const response = await fetch('/api/skills');
        const skills = await response.json();
        setState({ skills });
    } catch (err) {
        console.error('Failed to fetch skills:', err);
    }
}

// ============================================================
// Chat streaming
// ============================================================

async function sendMessage() {
    const text = state.composerText.trim();
    if (!text && state.composerAttachments.length === 0) return;

    // Build messages array
    const userMessage = {
        role: 'user',
        content: text,
        attachments: state.composerAttachments,
    };

    const messages = [...state.messages, userMessage];
    setState({ messages, composerText: '', composerAttachments: [], streaming: true });

    // Create conversation if needed
    if (!state.currentConversationId) {
        try {
            const response = await fetch('/api/conversations', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ messages: [userMessage] }),
            });
            const conv = await response.json();
            setState({ currentConversationId: conv.id });
            fetchConversations();
        } catch (err) {
            console.error('Failed to create conversation:', err);
            setState({ streaming: false });
            return;
        }
    }

    // Stream response
    const abortController = new AbortController();
    setState({ abortController });

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model: state.defaultModel,
                messages: messages,
                skills: state.activeSkills,
            }),
            signal: abortController.signal,
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let assistantMessage = { role: 'assistant', content: '' };

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop(); // Keep incomplete line in buffer

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = line.slice(6);
                    try {
                        const event = JSON.parse(data);
                        if (event.type === 'chunk') {
                            assistantMessage.content += event.content;
                            // Update the last message in state
                            const msgs = [...state.messages];
                            if (msgs[msgs.length - 1]?.role === 'assistant') {
                                msgs[msgs.length - 1] = { ...assistantMessage };
                            } else {
                                msgs.push({ ...assistantMessage });
                            }
                            setState({ messages: msgs });
                        } else if (event.type === 'done') {
                            // Final update
                            const msgs = [...state.messages];
                            if (msgs[msgs.length - 1]?.role === 'assistant') {
                                msgs[msgs.length - 1] = { ...assistantMessage };
                            } else {
                                msgs.push({ ...assistantMessage });
                            }
                            setState({ messages: msgs, streaming: false, abortController: null });
                            saveConversation();
                        } else if (event.type === 'error') {
                            console.error('Stream error:', event.message);
                            setState({ streaming: false, abortController: null });
                        } else if (event.type === 'usage') {
                            // Handle usage info if needed
                        }
                    } catch (e) {
                        // Ignore parse errors for incomplete chunks
                    }
                }
            }
        }
    } catch (err) {
        if (err.name === 'AbortError') {
            // User cancelled
        } else {
            console.error('Stream failed:', err);
        }
        setState({ streaming: false, abortController: null });
    }
}

// ============================================================
// Rendering
// ============================================================

function render() {
    renderSidebar();
    renderChat();
    renderComposer();
    renderSettings();
    renderSkills();
    renderModelPicker();
}

function renderSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (!sidebar) return;

    let html = '<div class="sidebar-header">';
    html += '<h2>Conversations</h2>';
    html += '<button onclick="newConversation()" title="New conversation">+</button>';
    html += '</div>';

    // Search
    html += '<div class="sidebar-search">';
    html += `<input type="text" placeholder="Search conversations..." value="${escapeHtml(state.conversationSearchQuery)}" oninput="setState({ conversationSearchQuery: this.value })">`;
    html += '</div>';

    // Conversation list
    html += '<div class="conversation-list">';
    const filtered = state.conversations.filter(c =>
        c.title.toLowerCase().includes(state.conversationSearchQuery.toLowerCase())
    );
    for (const conv of filtered) {
        const active = conv.id === state.currentConversationId ? ' active' : '';
        html += `<div class="conversation-item${active}" onclick="loadConversation('${conv.id}')">`;
        html += `<span class="conversation-title">${escapeHtml(conv.title || 'Untitled')}</span>`;
        html += `<button class="delete-btn" onclick="event.stopPropagation(); deleteConversation('${conv.id}')">&times;</button>`;
        html += '</div>';
    }
    html += '</div>';

    sidebar.innerHTML = html;
}

function renderChat() {
    const chat = document.getElementById('chat');
    if (!chat) return;

    if (state.messages.length === 0) {
        chat.innerHTML = '<div class="empty-state"><p>Start a conversation</p></div>';
        return;
    }

    let html = '';
    for (const msg of state.messages) {
        const roleClass = msg.role === 'user' ? 'user-message' : 'assistant-message';
        html += `<div class="message ${roleClass}">`;
        html += `<div class="message-content">${escapeHtml(msg.content)}</div>`;
        html += '</div>';
    }

    if (state.streaming) {
        html += '<div class="message assistant-message streaming"><div class="message-content">...</div></div>';
    }

    chat.innerHTML = html;
    chat.scrollTop = chat.scrollHeight;
}

function renderComposer() {
    const composer = document.getElementById('composer');
    if (!composer) return;
    composer.value = state.composerText;
}

function renderSettings() {
    const settings = document.getElementById('settings-drawer');
    if (!settings) return;

    if (!state.isSettingsOpen) {
        settings.classList.add('hidden');
        return;
    }
    settings.classList.remove('hidden');

    let html = '<div class="drawer-header"><h2>Settings</h2><button onclick="closeSettings()">&times;</button></div>';
    html += '<div class="drawer-body">';

    // API Key
    html += '<label>API Key</label>';
    html += `<input type="password" value="${escapeHtml(state.apiKey)}" onchange="updateApiKey(this.value)">`;

    // Default model
    html += '<label>Default Model</label>';
    html += `<select onchange="updateDefaultModel(this.value)">`;
    html += '<option value="">Select a model...</option>';
    for (const model of state.models) {
        const selected = model.id === state.defaultModel ? ' selected' : '';
        html += `<option value="${escapeHtml(model.id)}"${selected}>${escapeHtml(model.name)}</option>`;
    }
    html += '</select>';

    // Theme
    html += '<label>Theme</label>';
    html += `<select onchange="updateTheme(this.value)">`;
    html += `<option value="light"${state.theme === 'light' ? ' selected' : ''}>Light</option>`;
    html += `<option value="dark"${state.theme === 'dark' ? ' selected' : ''}>Dark</option>`;
    html += '</select>';

    // Balance
    if (state.balance) {
        html += '<h3>Balance</h3>';
        html += `<p>Credits: ${state.balance.credits}</p>`;
        html += `<p>Usage: ${state.balance.usage}</p>`;
        html += `<p>Total: ${state.balance.total}</p>`;
    }

    html += '</div>';
    settings.innerHTML = html;
}

function renderSkills() {
    const skills = document.getElementById('skills-drawer');
    if (!skills) return;

    if (!state.isSkillsOpen) {
        skills.classList.add('hidden');
        return;
    }
    skills.classList.remove('hidden');

    let html = '<div class="drawer-header"><h2>Skills</h2><button onclick="closeSkills()">&times;</button></div>';
    html += '<div class="drawer-body">';

    for (const skill of state.skills) {
        const active = state.activeSkills.includes(skill.id);
        html += `<div class="skill-item">`;
        html += `<label><input type="checkbox" ${active ? 'checked' : ''} onchange="toggleSkill('${skill.id}', this.checked)"> ${escapeHtml(skill.name)}</label>`;
        html += '</div>';
    }

    html += '</div>';
    skills.innerHTML = html;
}

function renderModelPicker() {
    const picker = document.getElementById('model-picker');
    if (!picker) return;

    if (!state.isModelPickerOpen) {
        picker.classList.add('hidden');
        return;
    }
    picker.classList.remove('hidden');

    let html = '<div class="drawer-header"><h2>Select Model</h2><button onclick="closeModelPicker()">&times;</button></div>';
    html += '<div class="drawer-body">';

    // Search
    html += `<input type="text" placeholder="Search models..." value="${escapeHtml(state.modelSearchQuery)}" oninput="setState({ modelSearchQuery: this.value })">`;

    // Provider filter
    html += '<select onchange="setState({ selectedProvider: this.value })">';
    html += '<option value="all">All Providers</option>';
    const providers = [...new Set(state.models.map(m => m.provider))];
    for (const provider of providers) {
        const selected = provider === state.selectedProvider ? ' selected' : '';
        html += `<option value="${escapeHtml(provider)}"${selected}>${escapeHtml(provider)}</option>`;
    }
    html += '</select>';

    // Model list
    const filtered = state.models.filter(m => {
        if (state.selectedProvider !== 'all' && m.provider !== state.selectedProvider) return false;
        if (!m.name.toLowerCase().includes(state.modelSearchQuery.toLowerCase())) return false;
        return true;
    });

    for (const model of filtered) {
        const selected = model.id === state.defaultModel ? ' selected' : '';
        html += `<div class="model-item${selected}" onclick="selectModel('${escapeHtml(model.id)}')">`;
        html += `<strong>${escapeHtml(model.name)}</strong>`;
        html += `<span class="model-provider">${escapeHtml(model.provider)}</span>`;
        html += `<span class="model-context">${model.context_length || 'N/A'} tokens</span>`;
        html += '</div>';
    }

    html += '</div>';
    picker.innerHTML = html;
}

// ============================================================
// Utility functions
// ============================================================

function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// ============================================================
// Event handlers (called from inline onclick)
// ============================================================

window.newConversation = newConversation;
window.loadConversation = loadConversation;
window.deleteConversation = deleteConversation;
window.closeSettings = closeSettings;
window.closeSkills = closeSkills;
window.closeModelPicker = closeModelPicker;
window.toggleSkill = toggleSkill;
window.selectModel = selectModel;
window.updateApiKey = updateApiKey;
window.updateDefaultModel = updateDefaultModel;
window.updateTheme = updateTheme;

async function loadConversation(id) {
    if (state.currentConversationId) {
        await saveConversation();
    }
    await fetchConversation(id);
}

async function deleteConversation(id) {
    try {
        await fetch(`/api/conversations/${id}`, { method: 'DELETE' });
        if (state.currentConversationId === id) {
            setState({ currentConversationId: null, messages: [] });
        }
        fetchConversations();
    } catch (err) {
        console.error('Failed to delete conversation:', err);
    }
}

function toggleSkill(id, active) {
    let activeSkills = [...state.activeSkills];
    if (active) {
        if (!activeSkills.includes(id)) activeSkills.push(id);
    } else {
        activeSkills = activeSkills.filter(s => s !== id);
    }
    setState({ activeSkills });
}

function selectModel(id) {
    setState({ defaultModel: id, isModelPickerOpen: false });
    localStorage.setItem('default_model', id);
}

function updateApiKey(value) {
    setState({ apiKey: value });
    localStorage.setItem('openrouter_api_key', value);
}

function updateDefaultModel(value) {
    setState({ defaultModel: value });
    localStorage.setItem('default_model', value);
}

function updateTheme(value) {
    setState({ theme: value });
    localStorage.setItem('theme', value);
    document.documentElement.setAttribute('data-theme', value);
}

// ============================================================
// Initialization
// ============================================================

// Set initial theme from localStorage
const savedTheme = localStorage.getItem('theme') || 'light';
document.documentElement.setAttribute('data-theme', savedTheme);

// Fetch initial data
fetchModels();
fetchConversations();

// Focus composer on load
window.addEventListener('load', () => {
    focusComposer();
});
