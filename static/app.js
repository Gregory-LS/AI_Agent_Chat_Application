// State management
const state = {
    token: localStorage.getItem('auth_token'),
    username: localStorage.getItem('auth_username'),
    authenticated: false,
    conversations: [],
    currentConversation: null,
    skills: [],
    config: {},
    models: [],
    theme: 'light',
    abortController: null
};

// DOM references
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

// --- API helper ---
async function apiFetch(path, options = {}) {
    const headers = { 'Content-Type': 'application/json', ...options.headers };
    if (state.token) {
        headers['Authorization'] = `Bearer ${state.token}`;
    }
    const res = await fetch(path, { ...options, headers });
    if (res.status === 401 && !path.startsWith('/api/auth/')) {
        // Session expired, redirect to login
        logout();
        return null;
    }
    if (options.raw) return res;
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Request failed');
    return data;
}

// --- Auth functions ---
function showLogin() {
    document.getElementById('login-page').style.display = 'flex';
    document.getElementById('app').style.display = 'none';
}

function showApp() {
    document.getElementById('login-page').style.display = 'none';
    document.getElementById('app').style.display = 'flex';
}

async function checkAuth() {
    if (!state.token) {
        showLogin();
        return;
    }
    try {
        const data = await apiFetch('/api/auth/check');
        if (data && data.authenticated) {
            state.authenticated = true;
            state.username = data.username;
            localStorage.setItem('auth_username', data.username);
            showApp();
            initApp();
        } else {
            logout();
        }
    } catch (e) {
        logout();
    }
}

async function login(username, password) {
    const data = await apiFetch('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username, password })
    });
    state.token = data.token;
    state.username = data.username;
    localStorage.setItem('auth_token', data.token);
    localStorage.setItem('auth_username', data.username);
    state.authenticated = true;
    showApp();
    initApp();
}

async function register(username, password) {
    await apiFetch('/api/auth/register', {
        method: 'POST',
        body: JSON.stringify({ username, password })
    });
    // Auto-login after registration
    await login(username, password);
}

function logout() {
    if (state.token) {
        apiFetch('/api/auth/logout', { method: 'POST' }).catch(() => {});
    }
    state.token = null;
    state.username = null;
    state.authenticated = false;
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_username');
    showLogin();
}

// --- Login form handlers ---
document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const showRegister = document.getElementById('show-register');
    const showLoginLink = document.getElementById('show-login');
    const registerSection = document.getElementById('register-section');
    
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('login-username').value;
        const password = document.getElementById('login-password').value;
        try {
            await login(username, password);
        } catch (err) {
            alert('Login failed: ' + err.message);
        }
    });
    
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('reg-username').value;
        const password = document.getElementById('reg-password').value;
        const confirm = document.getElementById('reg-confirm').value;
        if (password !== confirm) {
            alert('Passwords do not match');
            return;
        }
        try {
            await register(username, password);
        } catch (err) {
            alert('Registration failed: ' + err.message);
        }
    });
    
    showRegister.addEventListener('click', (e) => {
        e.preventDefault();
        registerSection.style.display = 'block';
        loginForm.style.display = 'none';
    });
    
    showLoginLink.addEventListener('click', (e) => {
        e.preventDefault();
        registerSection.style.display = 'none';
        loginForm.style.display = 'block';
    });
    
    checkAuth();
});

// --- App initialization ---
let appInitialized = false;
async function initApp() {
    if (appInitialized) return;
    appInitialized = true;
    
    // Load config
    try {
        state.config = await apiFetch('/api/config');
    } catch (e) {
        console.error('Failed to load config:', e);
    }
    
    // Load theme
    const theme = state.config.theme || 'light';
    document.documentElement.setAttribute('data-theme', theme);
    state.theme = theme;
    
    // Load conversations
    loadConversations();
    
    // Load skills
    loadSkills();
    
    // Load models
    loadModels();
    
    // Setup event listeners
    setupEventListeners();
}

function setupEventListeners() {
    // Logout button
    document.getElementById('logout-btn').addEventListener('click', logout);
    
    // New conversation
    document.getElementById('new-chat-btn').addEventListener('click', newConversation);
    
    // Send message
    document.getElementById('send-btn').addEventListener('click', sendMessage);
    document.getElementById('message-input').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Stop button
    document.getElementById('stop-btn').addEventListener('click', stopGeneration);
    
    // Sidebar search
    document.getElementById('search-input').addEventListener('input', filterConversations);
    
    // Settings
    document.getElementById('settings-btn').addEventListener('click', openSettings);
    document.getElementById('settings-close').addEventListener('click', closeSettings);
    document.getElementById('settings-save').addEventListener('click', saveSettings);
    
    // Theme toggle
    document.getElementById('theme-toggle').addEventListener('change', toggleTheme);
    
    // Skills
    document.getElementById('skills-btn').addEventListener('click', openSkillsDrawer);
    document.getElementById('skills-close').addEventListener('click', closeSkillsDrawer);
    document.getElementById('add-skill-btn').addEventListener('click', addSkill);
    
    // Model picker
    document.getElementById('model-picker-btn').addEventListener('click', openModelPicker);
    document.getElementById('model-picker-close').addEventListener('click', closeModelPicker);
    document.getElementById('model-search').addEventListener('input', filterModels);
    
    // Conversation list click delegation
    document.getElementById('conversation-list').addEventListener('click', (e) => {
        const item = e.target.closest('.conversation-item');
        if (!item) return;
        if (e.target.closest('.delete-conv')) {
            deleteConversation(item.dataset.id);
        } else if (e.target.closest('.rename-conv')) {
            renameConversation(item.dataset.id);
        } else {
            selectConversation(item.dataset.id);
        }
    });
}

// --- Conversation functions ---
async function loadConversations() {
    try {
        state.conversations = await apiFetch('/api/conversations');
        renderConversations();
    } catch (e) {
        console.error('Failed to load conversations:', e);
    }
}

function renderConversations() {
    const list = document.getElementById('conversation-list');
    const search = document.getElementById('search-input').value.toLowerCase();
    const filtered = state.conversations.filter(c => 
        c.title.toLowerCase().includes(search)
    );
    list.innerHTML = filtered.map(c => `
        <div class="conversation-item ${state.currentConversation && state.currentConversation.id === c.id ? 'active' : ''}" data-id="${c.id}">
            <span class="conv-title">${escapeHtml(c.title)}</span>
            <div class="conv-actions">
                <button class="rename-conv" title="Rename">✏️</button>
                <button class="delete-conv" title="Delete">🗑️</button>
            </div>
        </div>
    `).join('');
}

async function newConversation() {
    const conv = await apiFetch('/api/conversations', {
        method: 'POST',
        body: JSON.stringify({
            title: 'New conversation',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            model: state.config.default_model || 'openai/gpt-4o'
        })
    });
    state.conversations.unshift(conv);
    state.currentConversation = conv;
    renderConversations();
    renderChat();
    document.getElementById('message-input').focus();
}

async function selectConversation(id) {
    const conv = await apiFetch(`/api/conversations/${id}`);
    state.currentConversation = conv;
    renderConversations();
    renderChat();
}

async function deleteConversation(id) {
    if (!confirm('Delete this conversation?')) return;
    await apiFetch(`/api/conversations/${id}`, { method: 'DELETE' });
    state.conversations = state.conversations.filter(c => c.id !== id);
    if (state.currentConversation && state.currentConversation.id === id) {
        state.currentConversation = null;
        renderChat();
    }
    renderConversations();
}

async function renameConversation(id) {
    const newTitle = prompt('New title:');
    if (!newTitle) return;
    const conv = await apiFetch(`/api/conversations/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({ title: newTitle })
    });
    const idx = state.conversations.findIndex(c => c.id === id);
    if (idx !== -1) state.conversations[idx].title = newTitle;
    if (state.currentConversation && state.currentConversation.id === id) {
        state.currentConversation.title = newTitle;
    }
    renderConversations();
}

function filterConversations() {
    renderConversations();
}

// --- Chat functions ---
function renderChat() {
    const chat = document.getElementById('chat-messages');
    if (!state.currentConversation) {
        chat.innerHTML = '<div class="empty-state">Select or create a conversation to start chatting.</div>';
        return;
    }
    chat.innerHTML = state.currentConversation.messages.map(msg => `
        <div class="message ${msg.role}">
            <div class="message-header">${msg.role === 'user' ? 'You' : 'Assistant'}</div>
            <div class="message-content">${escapeHtml(msg.content)}</div>
            <div class="message-actions">
                <button class="copy-msg" data-content="${escapeHtml(msg.content)}">Copy</button>
            </div>
        </div>
    `).join('');
    chat.scrollTop = chat.scrollHeight;
}

async function sendMessage() {
    const input = document.getElementById('message-input');
    const text = input.value.trim();
    if (!text) return;
    
    if (!state.currentConversation) {
        await newConversation();
    }
    
    // Add user message
    state.currentConversation.messages.push({ role: 'user', content: text });
    input.value = '';
    renderChat();
    
    // Show loading indicator
    const chat = document.getElementById('chat-messages');
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message assistant loading';
    loadingDiv.innerHTML = '<div class="message-header">Assistant</div><div class="message-content">Thinking...</div>';
    chat.appendChild(loadingDiv);
    chat.scrollTop = chat.scrollHeight;
    
    // Enable stop button
    document.getElementById('send-btn').style.display = 'none';
    document.getElementById('stop-btn').style.display = 'inline-block';
    
    // Get enabled skills
    const enabledSkills = state.skills.filter(s => s.enabled);
    const systemMessages = enabledSkills.map(s => ({ role: 'system', content: s.prompt }));
    const messages = [...systemMessages, ...state.currentConversation.messages];
    
    // Create abort controller
    state.abortController = new AbortController();
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify({
                model: state.currentConversation.model || state.config.default_model || 'openai/gpt-4o',
                messages: messages
            }),
            signal: state.abortController.signal
        });
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let assistantContent = '';
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n');
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = line.slice(6);
                    if (data === '[DONE]') continue;
                    try {
                        const parsed = JSON.parse(data);
                        if (parsed.choices && parsed.choices[0] && parsed.choices[0].delta && parsed.choices[0].delta.content) {
                            assistantContent += parsed.choices[0].delta.content;
                            // Update the loading message
                            const loadingMsg = chat.querySelector('.loading .message-content');
                            if (loadingMsg) {
                                loadingMsg.textContent = assistantContent;
                            }
                            chat.scrollTop = chat.scrollHeight;
                        }
                        if (parsed.error) {
                            throw new Error(parsed.error);
                        }
                    } catch (e) {
                        if (e.message !== 'Unexpected end of JSON input') {
                            console.error('Parse error:', e);
                        }
                    }
                }
            }
        }
        
        // Remove loading indicator and add final message
        loadingDiv.remove();
        if (assistantContent) {
            state.currentConversation.messages.push({ role: 'assistant', content: assistantContent });
            renderChat();
        }
        
        // Save conversation
        await apiFetch(`/api/conversations/${state.currentConversation.id}`, {
            method: 'PATCH',
            body: JSON.stringify({
                messages: state.currentConversation.messages,
                updated_at: new Date().toISOString()
            })
        });
        
        // Auto-title if first message
        if (state.currentConversation.messages.length === 2 && state.currentConversation.title === 'New conversation') {
            const title = text.length > 50 ? text.substring(0, 50) + '...' : text;
            state.currentConversation.title = title;
            await apiFetch(`/api/conversations/${state.currentConversation.id}`, {
                method: 'PATCH',
                body: JSON.stringify({ title: title })
            });
            const idx = state.conversations.findIndex(c => c.id === state.currentConversation.id);
            if (idx !== -1) state.conversations[idx].title = title;
            renderConversations();
        }
    } catch (e) {
        if (e.name === 'AbortError') {
            loadingDiv.remove();
            if (assistantContent) {
                state.currentConversation.messages.push({ role: 'assistant', content: assistantContent + ' [stopped]' });
                renderChat();
            }
        } else {
            loadingDiv.innerHTML = '<div class="message-header">Assistant</div><div class="message-content error">Error: ' + escapeHtml(e.message) + '</div>';
        }
    } finally {
        document.getElementById('send-btn').style.display = 'inline-block';
        document.getElementById('stop-btn').style.display = 'none';
        state.abortController = null;
    }
}

function stopGeneration() {
    if (state.abortController) {
        state.abortController.abort();
    }
}

// --- Skills functions ---
async function loadSkills() {
    try {
        state.skills = await apiFetch('/api/skills');
        renderSkills();
    } catch (e) {
        console.error('Failed to load skills:', e);
    }
}

function renderSkills() {
    const container = document.getElementById('skills-list');
    container.innerHTML = state.skills.map(s => `
        <div class="skill-item">
            <label>
                <input type="checkbox" ${s.enabled ? 'checked' : ''} data-id="${s.id}" class="skill-toggle">
                ${escapeHtml(s.name)}
            </label>
            <button class="delete-skill" data-id="${s.id}">🗑️</button>
        </div>
    `).join('');
    
    // Add event listeners for toggles and deletes
    container.querySelectorAll('.skill-toggle').forEach(cb => {
        cb.addEventListener('change', toggleSkill);
    });
    container.querySelectorAll('.delete-skill').forEach(btn => {
        btn.addEventListener('click', deleteSkill);
    });
}

async function addSkill() {
    const name = prompt('Skill name:');
    if (!name) return;
    const prompt = prompt('System prompt for this skill:');
    if (!prompt) return;
    const skill = await apiFetch('/api/skills', {
        method: 'POST',
        body: JSON.stringify({ name, prompt, enabled: true })
    });
    state.skills.push(skill);
    renderSkills();
}

async function toggleSkill(e) {
    const id = e.target.dataset.id;
    const enabled = e.target.checked;
    const skill = state.skills.find(s => s.id === id);
    if (skill) {
        skill.enabled = enabled;
        await apiFetch(`/api/skills/${id}`, {
            method: 'PATCH',
            body: JSON.stringify({ enabled })
        });
    }
}

async function deleteSkill(e) {
    const id = e.target.dataset.id;
    if (!confirm('Delete this skill?')) return;
    await apiFetch(`/api/skills/${id}`, { method: 'DELETE' });
    state.skills = state.skills.filter(s => s.id !== id);
    renderSkills();
}

// --- Model functions ---
async function loadModels() {
    try {
        state.models = await apiFetch('/api/models');
        renderModels();
    } catch (e) {
        console.error('Failed to load models:', e);
    }
}

function renderModels() {
    const container = document.getElementById('model-list');
    const search = document.getElementById('model-search').value.toLowerCase();
    const filtered = state.models.filter(m => 
        m.id.toLowerCase().includes(search) || m.name.toLowerCase().includes(search)
    );
    container.innerHTML = filtered.map(m => `
        <div class="model-item ${state.currentConversation && state.currentConversation.model === m.id ? 'active' : ''}" data-id="${m.id}">
            <div class="model-name">${escapeHtml(m.name || m.id)}</div>
            <div class="model-id">${escapeHtml(m.id)}</div>
            <div class="model-pricing">${m.pricing ? `${m.pricing.prompt}/${m.pricing.completion}` : ''}</div>
        </div>
    `).join('');
    
    container.querySelectorAll('.model-item').forEach(item => {
        item.addEventListener('click', selectModel);
    });
}

function selectModel(e) {
    const id = e.currentTarget.dataset.id;
    if (state.currentConversation) {
        state.currentConversation.model = id;
        apiFetch(`/api/conversations/${state.currentConversation.id}`, {
            method: 'PATCH',
            body: JSON.stringify({ model: id })
        });
    }
    closeModelPicker();
}

function filterModels() {
    renderModels();
}

// --- Settings functions ---
function openSettings() {
    document.getElementById('settings-drawer').classList.add('open');
    document.getElementById('settings-api-key').value = state.config.api_key || '';
    document.getElementById('settings-default-model').value = state.config.default_model || 'openai/gpt-4o';
    document.getElementById('theme-toggle').checked = state.theme === 'dark';
}

function closeSettings() {
    document.getElementById('settings-drawer').classList.remove('open');
}

async function saveSettings() {
    const apiKey = document.getElementById('settings-api-key').value;
    const defaultModel = document.getElementById('settings-default-model').value;
    const config = { api_key: apiKey, default_model: defaultModel };
    state.config = await apiFetch('/api/config', {
        method: 'PUT',
        body: JSON.stringify(config)
    });
    closeSettings();
}

function toggleTheme(e) {
    const theme = e.target.checked ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', theme);
    state.theme = theme;
    state.config.theme = theme;
    apiFetch('/api/config', {
        method: 'PUT',
        body: JSON.stringify({ theme })
    }).catch(() => {});
}

// --- Drawer functions ---
function openSkillsDrawer() {
    document.getElementById('skills-drawer').classList.add('open');
}

function closeSkillsDrawer() {
    document.getElementById('skills-drawer').classList.remove('open');
}

function openModelPicker() {
    document.getElementById('model-picker-drawer').classList.add('open');
    renderModels();
}

function closeModelPicker() {
    document.getElementById('model-picker-drawer').classList.remove('open');
}

// --- Utility functions ---
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}