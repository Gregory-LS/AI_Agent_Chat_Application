// state
let state = {
    apiKey: '',
    defaultModel: '',
    conversations: [],
    currentConversationId: null,
    messages: [],
    skills: [],
    models: [],
    theme: 'light',
    streaming: false,
    abortController: null
};

// DOM references
const els = {};

function init() {
    els.sidebar = document.getElementById('sidebar');
    els.chatArea = document.getElementById('chat-area');
    els.composer = document.getElementById('composer');
    els.modelPicker = document.getElementById('model-picker');
    els.settingsDrawer = document.getElementById('settings-drawer');
    els.skillsDrawer = document.getElementById('skills-drawer');
    els.newChatBtn = document.getElementById('new-chat-btn');
    els.settingsBtn = document.getElementById('settings-btn');
    els.skillsBtn = document.getElementById('skills-btn');
    els.sendBtn = document.getElementById('send-btn');
    els.stopBtn = document.getElementById('stop-btn');
    els.conversationList = document.getElementById('conversation-list');
    els.messageContainer = document.getElementById('message-container');
    els.modelSelect = document.getElementById('model-select');
    els.searchInput = document.getElementById('search-input');
    els.apiKeyInput = document.getElementById('api-key-input');
    els.defaultModelInput = document.getElementById('default-model-input');
    els.themeToggle = document.getElementById('theme-toggle');
    els.attachmentBtn = document.getElementById('attachment-btn');
    els.attachmentInput = document.getElementById('attachment-input');
    els.balanceDisplay = document.getElementById('balance-display');

    loadConfig();
    loadConversations();
    loadSkills();
    fetchModels();
    fetchBalance();

    els.newChatBtn.addEventListener('click', newConversation);
    els.settingsBtn.addEventListener('click', () => toggleDrawer('settings'));
    els.skillsBtn.addEventListener('click', () => toggleDrawer('skills'));
    els.sendBtn.addEventListener('click', sendMessage);
    els.stopBtn.addEventListener('click', stopStreaming);
    els.composer.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    els.searchInput.addEventListener('input', filterConversations);
    els.apiKeyInput.addEventListener('change', saveConfig);
    els.defaultModelInput.addEventListener('change', saveConfig);
    els.themeToggle.addEventListener('click', toggleTheme);
    els.attachmentBtn.addEventListener('click', () => els.attachmentInput.click());
    els.attachmentInput.addEventListener('change', handleAttachment);

    document.addEventListener('click', (e) => {
        const drawer = e.target.closest('.drawer');
        if (!drawer) {
            document.querySelectorAll('.drawer.open').forEach(d => d.classList.remove('open'));
        }
    });

    // Keyboard shortcut: Ctrl+Shift+P to toggle model picker
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.shiftKey && e.key === 'P') {
            e.preventDefault();
            toggleDrawer('model-picker');
        }
    });
}

function fetchBalance() {
    fetch('/api/balance')
        .then(r => r.json())
        .then(data => {
            if (data.credits !== undefined) {
                els.balanceDisplay.textContent = `Balance: ${data.credits.toFixed(4)} credits`;
            } else {
                els.balanceDisplay.textContent = 'Balance unavailable';
            }
        })
        .catch(() => {
            els.balanceDisplay.textContent = 'Balance unavailable';
        });
}

function loadConfig() {
    fetch('/api/config')
        .then(r => r.json())
        .then(config => {
            state.apiKey = config.api_key || '';
            state.defaultModel = config.default_model || '';
            state.theme = config.theme || 'light';
            els.apiKeyInput.value = state.apiKey;
            els.defaultModelInput.value = state.defaultModel;
            document.documentElement.setAttribute('data-theme', state.theme);
        });
}

function saveConfig() {
    state.apiKey = els.apiKeyInput.value;
    state.defaultModel = els.defaultModelInput.value;
    fetch('/api/config', {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({api_key: state.apiKey, default_model: state.defaultModel, theme: state.theme})
    }).then(() => fetchModels());
}

function toggleTheme() {
    state.theme = state.theme === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', state.theme);
    saveConfig();
}

function toggleDrawer(type) {
    const drawers = {
        'settings': els.settingsDrawer,
        'skills': els.skillsDrawer,
        'model-picker': els.modelPicker
    };
    const drawer = drawers[type];
    if (drawer) {
        const isOpen = drawer.classList.contains('open');
        document.querySelectorAll('.drawer.open').forEach(d => d.classList.remove('open'));
        if (!isOpen) drawer.classList.add('open');
    }
}

function fetchModels() {
    if (!state.apiKey) return;
    fetch('/api/models')
        .then(r => r.json())
        .then(models => {
            state.models = models;
            populateModelPicker(models);
        })
        .catch(() => {});
}

function populateModelPicker(models) {
    const container = document.getElementById('model-list');
    container.innerHTML = '';
    // Group by provider
    const grouped = {};
    models.forEach(m => {
        const provider = m.provider?.name || 'Other';
        if (!grouped[provider]) grouped[provider] = [];
        grouped[provider].push(m);
    });
    for (const [provider, mods] of Object.entries(grouped)) {
        const group = document.createElement('div');
        group.className = 'model-group';
        const header = document.createElement('h4');
        header.textContent = provider;
        group.appendChild(header);
        mods.forEach(m => {
            const item = document.createElement('div');
            item.className = 'model-item';
            item.textContent = m.id;
            item.dataset.model = m.id;
            item.addEventListener('click', () => selectModel(m.id));
            group.appendChild(item);
        });
        container.appendChild(group);
    }
}

function selectModel(modelId) {
    state.defaultModel = modelId;
    els.defaultModelInput.value = modelId;
    saveConfig();
    toggleDrawer('model-picker');
}

function loadConversations() {
    fetch('/api/conversations')
        .then(r => r.json())
        .then(convs => {
            state.conversations = convs;
            renderConversationList();
        });
}

function renderConversationList() {
    const list = els.conversationList;
    list.innerHTML = '';
    state.conversations.forEach(conv => {
        const item = document.createElement('div');
        item.className = 'conversation-item';
        item.dataset.id = conv.id;
        const title = document.createElement('span');
        title.className = 'conv-title';
        title.textContent = conv.title || 'Untitled';
        title.addEventListener('click', () => loadConversation(conv.id));
        const actions = document.createElement('div');
        actions.className = 'conv-actions';
        const renameBtn = document.createElement('button');
        renameBtn.textContent = '✏️';
        renameBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const newTitle = prompt('Rename conversation:', conv.title);
            if (newTitle) {
                fetch(`/api/conversations/${conv.id}`, {
                    method: 'PATCH',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({title: newTitle})
                }).then(() => loadConversations());
            }
        });
        const deleteBtn = document.createElement('button');
        deleteBtn.textContent = '🗑️';
        deleteBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            if (confirm('Delete this conversation?')) {
                fetch(`/api/conversations/${conv.id}`, {method: 'DELETE'})
                    .then(() => {
                        if (state.currentConversationId === conv.id) {
                            state.currentConversationId = null;
                            state.messages = [];
                            renderMessages();
                        }
                        loadConversations();
                    });
            }
        });
        actions.appendChild(renameBtn);
        actions.appendChild(deleteBtn);
        item.appendChild(title);
        item.appendChild(actions);
        list.appendChild(item);
    });
}

function filterConversations() {
    const query = els.searchInput.value.toLowerCase();
    document.querySelectorAll('.conversation-item').forEach(item => {
        const title = item.querySelector('.conv-title').textContent.toLowerCase();
        item.style.display = title.includes(query) ? '' : 'none';
    });
}

function newConversation() {
    state.currentConversationId = null;
    state.messages = [];
    renderMessages();
    els.composer.value = '';
    els.composer.focus();
}

function loadConversation(id) {
    state.currentConversationId = id;
    fetch(`/api/conversations/${id}`)
        .then(r => r.json())
        .then(conv => {
            state.messages = conv.messages || [];
            renderMessages();
        });
}

function renderMessages() {
    const container = els.messageContainer;
    container.innerHTML = '';
    state.messages.forEach(msg => {
        const el = document.createElement('div');
        el.className = `message ${msg.role}`;
        el.textContent = msg.content;
        container.appendChild(el);
    });
    container.scrollTop = container.scrollHeight;
}

function sendMessage() {
    const text = els.composer.value.trim();
    if (!text || state.streaming) return;

    const model = state.defaultModel || 'openai/gpt-4o';
    const userMessage = {role: 'user', content: text};
    state.messages.push(userMessage);
    renderMessages();
    els.composer.value = '';

    state.abortController = new AbortController();
    state.streaming = true;
    els.sendBtn.style.display = 'none';
    els.stopBtn.style.display = 'inline-block';

    // Add placeholder for assistant
    const assistantMsg = {role: 'assistant', content: ''};
    state.messages.push(assistantMsg);
    const msgIndex = state.messages.length - 1;
    renderMessages();

    const body = JSON.stringify({model, messages: state.messages.slice(0, -1)});
    fetch('/api/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body,
        signal: state.abortController.signal
    }).then(async response => {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        while (true) {
            const {done, value} = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, {stream: true});
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = line.slice(6);
                    if (data === '[DONE]') {
                        state.streaming = false;
                        els.sendBtn.style.display = 'inline-block';
                        els.stopBtn.style.display = 'none';
                        saveConversation();
                        break;
                    }
                    try {
                        const parsed = JSON.parse(data);
                        const content = parsed.choices?.[0]?.delta?.content || '';
                        state.messages[msgIndex].content += content;
                        // Update the last message element
                        const container = els.messageContainer;
                        const lastMsg = container.lastElementChild;
                        if (lastMsg) lastMsg.textContent = state.messages[msgIndex].content;
                        container.scrollTop = container.scrollHeight;
                    } catch (e) {
                        // ignore parse errors
                    }
                }
            }
        }
    }).catch(err => {
        if (err.name !== 'AbortError') {
            console.error('Stream error:', err);
        }
        state.streaming = false;
        els.sendBtn.style.display = 'inline-block';
        els.stopBtn.style.display = 'none';
    });
}

function stopStreaming() {
    if (state.abortController) {
        state.abortController.abort();
        state.streaming = false;
        els.sendBtn.style.display = 'inline-block';
        els.stopBtn.style.display = 'none';
    }
}

function saveConversation() {
    const title = state.messages[0]?.content?.slice(0, 50) || 'Untitled';
    const data = {
        title,
        messages: state.messages,
        model: state.defaultModel,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
    };
    if (state.currentConversationId) {
        fetch(`/api/conversations/${state.currentConversationId}`, {
            method: 'PATCH',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        }).then(() => loadConversations());
    } else {
        fetch('/api/conversations', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        }).then(r => r.json()).then(conv => {
            state.currentConversationId = conv.id;
            loadConversations();
        });
    }
}

function loadSkills() {
    fetch('/api/skills')
        .then(r => r.json())
        .then(skills => {
            state.skills = skills;
            renderSkills();
        });
}

function renderSkills() {
    const container = document.getElementById('skills-list');
    container.innerHTML = '';
    state.skills.forEach(skill => {
        const item = document.createElement('div');
        item.className = 'skill-item';
        const name = document.createElement('span');
        name.textContent = skill.name;
        const toggle = document.createElement('input');
        toggle.type = 'checkbox';
        toggle.checked = skill.enabled;
        toggle.addEventListener('change', () => {
            fetch(`/api/skills/${skill.id}`, {
                method: 'PATCH',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({enabled: toggle.checked})
            });
        });
        item.appendChild(name);
        item.appendChild(toggle);
        container.appendChild(item);
    });
}

function handleAttachment(e) {
    const file = e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    fetch('/api/attachments', {
        method: 'POST',
        body: formData
    }).then(r => r.json()).then(att => {
        console.log('Attachment uploaded:', att);
        // Append attachment reference to composer
        els.composer.value += ` [Attachment: ${att.filename}]`;
    }).catch(err => console.error('Upload failed:', err));
    e.target.value = '';
}

document.addEventListener('DOMContentLoaded', init);
