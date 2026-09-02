// app.js — Claude-style AI chat frontend
// State management, streaming fetch, model picker, skills, conversation management, keyboard shortcuts

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
// Keyboard shortcuts
// ============================================================

document.addEventListener('keydown', function(e) {
    const tag = e.target.tagName.toLowerCase();
    const isInput = tag === 'input' || tag === 'textarea' || tag === 'select' || e.target.isContentEditable;

    if (e.ctrlKey && e.shiftKey && e.key === 'O') {
        e.preventDefault();
        focusComposer();
        return;
    }

    if (e.key === 'Escape') {
        e.preventDefault();
        if (state.streaming) {
            stopGeneration();
        } else if (state.isSettingsOpen) {
            closeSettingsModal();
        } else if (state.isSkillsOpen) {
            closeSkills();
        } else if (state.isModelPickerOpen) {
            closeModelPicker();
        }
        return;
    }

    if (isInput) return;

    if (e.ctrlKey && e.shiftKey && e.key === 'N') {
        e.preventDefault();
        newConversation();
        return;
    }

    if (e.ctrlKey && e.shiftKey && e.key === ',') {
        e.preventDefault();
        openSettingsModal();
        return;
    }

    if (e.ctrlKey && e.shiftKey && e.key === 'E') {
        e.preventDefault();
        openSkills();
        return;
    }

    if (e.ctrlKey && e.shiftKey && e.key === 'Delete') {
        e.preventDefault();
        clearConversations();
        return;
    }

    if (e.ctrlKey && e.shiftKey && e.key === 'ArrowUp') {
        e.preventDefault();
        navigateConversation(-1);
        return;
    }

    if (e.ctrlKey && e.shiftKey && e.key === 'ArrowDown') {
        e.preventDefault();
        navigateConversation(1);
        return;
    }

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

function closeSkills() {
    setState({ isSkillsOpen: false });
}

function closeModelPicker() {
    setState({ isModelPickerOpen: false });
}

function newConversation() {
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

function openSettingsModal() {
    setState({ isSettingsOpen: true });
    const modal = document.getElementById('settings-modal');
    const overlay = document.getElementById('overlay');
    modal.classList.remove('hidden');
    overlay.classList.remove('hidden');
    fetchBalance();
    populateDefaultModelSelect();
    const apiKeyInput = document.getElementById('api-key-input');
    if (apiKeyInput) {
        apiKeyInput.value = state.apiKey || '';
    }
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.textContent = state.theme === 'light' ? 'Switch to Dark' : 'Switch to Light';
    }
}

function closeSettingsModal() {
    setState({ isSettingsOpen: false });
    const modal = document.getElementById('settings-modal');
    const overlay = document.getElementById('overlay');
    modal.classList.add('hidden');
    overlay.classList.add('hidden');
}

function saveSettingsModal() {
    const apiKeyInput = document.getElementById('api-key-input');
    const defaultModelSelect = document.getElementById('default-model-select');
    const newApiKey = apiKeyInput ? apiKeyInput.value.trim() : state.apiKey;
    const newDefaultModel = defaultModelSelect ? defaultModelSelect.value : state.defaultModel;

    localStorage.setItem('openrouter_api_key', newApiKey);
    localStorage.setItem('default_model', newDefaultModel);

    fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: newApiKey, default_model: newDefaultModel })
    }).then(resp => {
        if (!resp.ok) throw new Error('Failed to save config');
        setState({ apiKey: newApiKey, defaultModel: newDefaultModel });
        closeSettingsModal();
    }).catch(err => {
        console.error('Error saving settings:', err);
        alert('Failed to save settings. Please try again.');
    });
}

function populateDefaultModelSelect() {
    const select = document.getElementById('default-model-select');
    if (!select) return;
    const currentValue = state.defaultModel;
    select.innerHTML = '<option value="">— Select a model —</option>' +
        state.models.map(m => `<option value="${m.id}" ${m.id === currentValue ? 'selected' : ''}>${m.name || m.id}</option>`).join('');
}

function toggleTheme() {
    const newTheme = state.theme === 'light' ? 'dark' : 'light';
    localStorage.setItem('theme', newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
    setState({ theme: newTheme });
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.textContent = newTheme === 'light' ? 'Switch to Dark' : 'Switch to Light';
    }
}

function clearConversations() {
    if (confirm('Are you sure you want to delete all conversations? This cannot be undone.')) {
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
        const balanceInfo = document.getElementById('balance-info');
        if (balanceInfo) {
            balanceInfo.textContent = `Balance: $${balance.credits?.toFixed(2) || '0.00'}`;
        }
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
// Event listeners
// ============================================================

document.addEventListener('DOMContentLoaded', function() {
    // Theme initialization
    document.documentElement.setAttribute('data-theme', state.theme);

    // Settings button
    document.getElementById('settings-btn').addEventListener('click', openSettingsModal);

    // Settings modal close button
    document.getElementById('settings-close-btn').addEventListener('click', closeSettingsModal);

    // Overlay click closes modal
    document.getElementById('overlay').addEventListener('click', closeSettingsModal);

    // Theme toggle in modal
    document.getElementById('theme-toggle').addEventListener('click', function() {
        toggleTheme();
    });

    // Logout button
    document.getElementById('logout-btn').addEventListener('click', function() {
        fetch('/api/logout', { method: 'POST' }).then(() => {
            localStorage.removeItem('openrouter_api_key');
            setState({ apiKey: '' });
            closeSettingsModal();
        }).catch(err => console.error('Logout failed:', err));
    });

    // Save settings on Enter in API key input
    document.getElementById('api-key-input').addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            saveSettingsModal();
        }
    });

    // Initial data fetch
    fetchModels();
    fetchConversations();
});

// ============================================================
// Render function (stub — will be expanded)
// ============================================================

function render() {
    // Placeholder for future rendering logic
}

// ============================================================
// Streaming fetch (stub — will be expanded)
// ============================================================

async function streamFetch(url, options, onChunk, onDone, onError) {
    try {
        const response = await fetch(url, options);
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop();
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = line.slice(6);
                    if (data === '[DONE]') {
                        if (onDone) onDone();
                        return;
                    }
                    try {
                        const parsed = JSON.parse(data);
                        if (parsed.type === 'chunk' && onChunk) {
                            onChunk(parsed.content);
                        } else if (parsed.type === 'error' && onError) {
                            onError(parsed.message || 'Unknown error');
                            return;
                        } else if (parsed.type === 'done' && onDone) {
                            onDone();
                            return;
                        }
                    } catch (e) {
                        // ignore parse errors for incomplete lines
                    }
                }
            }
        }
        if (onDone) onDone();
    } catch (err) {
        if (onError) onError(err.message);
    }
}

// ============================================================
// Model picker (stub)
// ============================================================

function openModelPicker() {
    // Placeholder
}

function closeModelPicker() {
    // Placeholder
}

// ============================================================
// Skills (stub)
// ============================================================

function openSkills() {
    setState({ isSkillsOpen: true });
    fetchSkills();
}

function closeSkills() {
    setState({ isSkillsOpen: false });
}

// ============================================================
// Conversation loading (stub)
// ============================================================

function loadConversation(id) {
    fetchConversation(id);
}

// ============================================================
// Export
// ============================================================

function exportConversation(id, format) {
    window.open(`/api/conversations/${id}/export?format=${format}`, '_blank');
}
