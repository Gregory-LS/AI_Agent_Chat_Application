// app.js — Main application logic for Agentic Chat

const App = {
  state: {
    conversations: [],
    currentConversationId: null,
    models: [],
    skills: [],
    config: { apiKey: '', defaultModel: '', theme: 'light' },
    balance: null,
    streaming: false,
    abortController: null,
    sidebarOpen: true,
    settingsOpen: false,
    skillsDrawerOpen: false
  },

  init() {
    this.loadConfig();
    this.loadModels();
    this.loadConversations();
    this.loadSkills();
    this.loadBalance();
    this.bindEvents();
    this.applyTheme();
  },

  // ===== API Helpers =====
  async api(method, path, body = null) {
    const opts = {
      method,
      headers: { 'Content-Type': 'application/json' }
    };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(path, opts);
    if (!res.ok) {
      const err = await res.text();
      throw new Error(`API error ${res.status}: ${err}`);
    }
    return res.json();
  },

  // ===== Config =====
  async loadConfig() {
    try {
      const data = await this.api('GET', '/api/config');
      this.state.config = data;
      this.applyTheme();
      document.getElementById('api-key-input').value = data.apiKey || '';
      document.getElementById('default-model-input').value = data.defaultModel || '';
    } catch (e) {
      console.warn('Failed to load config:', e);
    }
  },

  async saveConfig() {
    try {
      const data = await this.api('PUT', '/api/config', this.state.config);
      this.state.config = data;
      this.applyTheme();
    } catch (e) {
      console.error('Failed to save config:', e);
    }
  },

  // ===== Models =====
  async loadModels() {
    try {
      const data = await this.api('GET', '/api/models');
      this.state.models = data;
      this.renderModelPicker();
    } catch (e) {
      console.warn('Failed to load models:', e);
    }
  },

  renderModelPicker() {
    const select = document.getElementById('model-select');
    select.innerHTML = '';
    const groups = {};
    for (const m of this.state.models) {
      const provider = m.id.split('/')[0] || 'Other';
      if (!groups[provider]) groups[provider] = [];
      groups[provider].push(m);
    }
    for (const [provider, models] of Object.entries(groups).sort()) {
      const optgroup = document.createElement('optgroup');
      optgroup.label = provider;
      for (const m of models) {
        const opt = document.createElement('option');
        opt.value = m.id;
        opt.textContent = m.name || m.id;
        if (m.context_length) opt.textContent += ` (${m.context_length} ctx)`;
        optgroup.appendChild(opt);
      }
      select.appendChild(optgroup);
    }
    if (this.state.config.defaultModel) {
      select.value = this.state.config.defaultModel;
    }
  },

  // ===== Balance =====
  async loadBalance() {
    try {
      const data = await this.api('GET', '/api/balance');
      this.state.balance = data;
      const el = document.getElementById('balance-display');
      if (el) el.textContent = `Balance: $${data.total_credits?.toFixed(2) || 'N/A'}`;
    } catch (e) {
      console.warn('Failed to load balance:', e);
    }
  },

  // ===== Conversations =====
  async loadConversations() {
    try {
      const data = await this.api('GET', '/api/conversations');
      this.state.conversations = data;
      this.renderSidebar();
    } catch (e) {
      console.warn('Failed to load conversations:', e);
    }
  },

  renderSidebar() {
    const list = document.getElementById('conversation-list');
    list.innerHTML = '';
    for (const conv of this.state.conversations) {
      const item = document.createElement('div');
      item.className = 'conversation-item';
      if (conv.id === this.state.currentConversationId) {
        item.classList.add('active');
      }
      item.textContent = conv.title || 'New conversation';
      item.dataset.id = conv.id;
      item.addEventListener('click', () => this.selectConversation(conv.id));
      // Delete button
      const delBtn = document.createElement('button');
      delBtn.className = 'delete-btn';
      delBtn.textContent = '×';
      delBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.deleteConversation(conv.id);
      });
      item.appendChild(delBtn);
      list.appendChild(item);
    }
  },

  async selectConversation(id) {
    this.state.currentConversationId = id;
    this.renderSidebar();
    try {
      const conv = await this.api('GET', `/api/conversations/${id}`);
      this.renderChat(conv.messages || []);
    } catch (e) {
      console.error('Failed to load conversation:', e);
    }
  },

  async newConversation() {
    try {
      const conv = await this.api('POST', '/api/conversations', { title: 'New conversation' });
      this.state.conversations.unshift(conv);
      this.state.currentConversationId = conv.id;
      this.renderSidebar();
      this.renderChat([]);
    } catch (e) {
      console.error('Failed to create conversation:', e);
    }
  },

  async deleteConversation(id) {
    try {
      await this.api('DELETE', `/api/conversations/${id}`);
      this.state.conversations = this.state.conversations.filter(c => c.id !== id);
      if (this.state.currentConversationId === id) {
        this.state.currentConversationId = null;
        this.renderChat([]);
      }
      this.renderSidebar();
    } catch (e) {
      console.error('Failed to delete conversation:', e);
    }
  },

  async renameConversation(id, newTitle) {
    try {
      await this.api('PATCH', `/api/conversations/${id}`, { title: newTitle });
      const conv = this.state.conversations.find(c => c.id === id);
      if (conv) conv.title = newTitle;
      this.renderSidebar();
    } catch (e) {
      console.error('Failed to rename conversation:', e);
    }
  },

  async exportConversation(id, format = 'json') {
    try {
      const res = await fetch(`/api/conversations/${id}/export?format=${format}`);
      if (!res.ok) throw new Error('Export failed');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `conversation-${id}.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error('Export failed:', e);
    }
  },

  // ===== Chat / Messages =====
  renderChat(messages) {
    const container = document.getElementById('chat-messages');
    container.innerHTML = '';
    for (const msg of messages) {
      this.appendMessage(msg);
    }
    container.scrollTop = container.scrollHeight;
  },

  appendMessage(msg) {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = `message ${msg.role}`;
    div.textContent = msg.content || '';
    // Copy button
    const copyBtn = document.createElement('button');
    copyBtn.className = 'copy-btn';
    copyBtn.textContent = 'Copy';
    copyBtn.addEventListener('click', () => {
      navigator.clipboard.writeText(msg.content || '');
    });
    div.appendChild(copyBtn);
    container.appendChild(div);
  },

  async sendMessage() {
    const input = document.getElementById('message-input');
    const text = input.value.trim();
    if (!text || this.state.streaming) return;

    if (!this.state.currentConversationId) {
      await this.newConversation();
    }

    // Add user message to chat
    const userMsg = { role: 'user', content: text };
    this.appendMessage(userMsg);
    input.value = '';

    // Prepare assistant message placeholder
    const assistantDiv = document.createElement('div');
    assistantDiv.className = 'message assistant';
    assistantDiv.textContent = '';
    const copyBtn = document.createElement('button');
    copyBtn.className = 'copy-btn';
    copyBtn.textContent = 'Copy';
    copyBtn.addEventListener('click', () => {
      navigator.clipboard.writeText(assistantDiv.textContent || '');
    });
    assistantDiv.appendChild(copyBtn);
    document.getElementById('chat-messages').appendChild(assistantDiv);

    // Start streaming
    this.state.streaming = true;
    this.state.abortController = new AbortController();

    try {
      const model = document.getElementById('model-select').value || this.state.config.defaultModel;
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conversation_id: this.state.currentConversationId,
          message: text,
          model: model
        }),
        signal: this.state.abortController.signal
      });

      if (!response.ok) {
        throw new Error(`Chat API error: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // keep incomplete line
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim();
            if (!data) continue;
            try {
              const parsed = JSON.parse(data);
              if (parsed.type === 'chunk') {
                assistantDiv.textContent += parsed.content || '';
                document.getElementById('chat-messages').scrollTop = document.getElementById('chat-messages').scrollHeight;
              } else if (parsed.type === 'done') {
                // done
              } else if (parsed.type === 'error') {
                assistantDiv.textContent = `Error: ${parsed.content}`;
              } else if (parsed.type === 'usage') {
                // could display usage
              }
            } catch (e) {
              console.warn('Failed to parse SSE chunk:', line, e);
            }
          }
        }
      }
    } catch (e) {
      if (e.name !== 'AbortError') {
        assistantDiv.textContent = `Error: ${e.message}`;
      }
    } finally {
      this.state.streaming = false;
      this.state.abortController = null;
      // Reload conversations to get updated messages
      this.loadConversations();
    }
  },

  stopStreaming() {
    if (this.state.abortController) {
      this.state.abortController.abort();
      this.state.streaming = false;
    }
  },

  // ===== Skills =====
  async loadSkills() {
    try {
      const data = await this.api('GET', '/api/skills');
      this.state.skills = data;
      this.renderSkills();
    } catch (e) {
      console.warn('Failed to load skills:', e);
    }
  },

  renderSkills() {
    const container = document.getElementById('skills-list');
    if (!container) return;
    container.innerHTML = '';
    for (const skill of this.state.skills) {
      const div = document.createElement('div');
      div.className = 'skill-item';
      const toggle = document.createElement('input');
      toggle.type = 'checkbox';
      toggle.checked = skill.enabled !== false;
      toggle.addEventListener('change', () => this.toggleSkill(skill.id, toggle.checked));
      div.appendChild(toggle);
      const label = document.createElement('span');
      label.textContent = skill.name || skill.id;
      div.appendChild(label);
      const delBtn = document.createElement('button');
      delBtn.className = 'delete-btn';
      delBtn.textContent = '×';
      delBtn.addEventListener('click', () => this.deleteSkill(skill.id));
      div.appendChild(delBtn);
      container.appendChild(div);
    }
  },

  async toggleSkill(id, enabled) {
    try {
      await this.api('PATCH', `/api/skills/${id}`, { enabled });
    } catch (e) {
      console.error('Failed to toggle skill:', e);
    }
  },

  async deleteSkill(id) {
    try {
      await this.api('DELETE', `/api/skills/${id}`);
      this.state.skills = this.state.skills.filter(s => s.id !== id);
      this.renderSkills();
    } catch (e) {
      console.error('Failed to delete skill:', e);
    }
  },

  async createSkill() {
    const name = prompt('Skill name:');
    if (!name) return;
    const prompt_text = prompt('System prompt:');
    if (!prompt_text) return;
    try {
      const skill = await this.api('POST', '/api/skills', { name, prompt: prompt_text });
      this.state.skills.push(skill);
      this.renderSkills();
    } catch (e) {
      console.error('Failed to create skill:', e);
    }
  },

  // ===== Theme =====
  applyTheme() {
    document.documentElement.setAttribute('data-theme', this.state.config.theme || 'light');
  },

  toggleTheme() {
    this.state.config.theme = this.state.config.theme === 'dark' ? 'light' : 'dark';
    this.saveConfig();
  },

  // ===== Settings =====
  openSettings() {
    this.state.settingsOpen = true;
    document.getElementById('settings-drawer').classList.add('open');
  },

  closeSettings() {
    this.state.settingsOpen = false;
    document.getElementById('settings-drawer').classList.remove('open');
  },

  saveSettings() {
    const apiKey = document.getElementById('api-key-input').value.trim();
    const defaultModel = document.getElementById('default-model-input').value.trim();
    this.state.config.apiKey = apiKey;
    this.state.config.defaultModel = defaultModel;
    this.saveConfig();
    this.closeSettings();
  },

  // ===== Attachments =====
  async uploadAttachment(file) {
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await fetch('/api/attachments', {
        method: 'POST',
        body: formData
      });
      if (!res.ok) throw new Error('Upload failed');
      const data = await res.json();
      return data;
    } catch (e) {
      console.error('Upload failed:', e);
      return null;
    }
  },

  // ===== Keyboard Shortcuts =====
  bindEvents() {
    // Send message on Enter (Shift+Enter for newline)
    document.getElementById('message-input').addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });

    // Send button
    document.getElementById('send-btn').addEventListener('click', () => this.sendMessage());

    // Stop button
    document.getElementById('stop-btn').addEventListener('click', () => this.stopStreaming());

    // New conversation
    document.getElementById('new-chat-btn').addEventListener('click', () => this.newConversation());

    // Sidebar toggle
    document.getElementById('sidebar-toggle').addEventListener('click', () => {
      this.state.sidebarOpen = !this.state.sidebarOpen;
      document.getElementById('sidebar').classList.toggle('closed');
    });

    // Settings
    document.getElementById('settings-btn').addEventListener('click', () => this.openSettings());
    document.getElementById('settings-close').addEventListener('click', () => this.closeSettings());
    document.getElementById('settings-save').addEventListener('click', () => this.saveSettings());

    // Theme toggle
    document.getElementById('theme-toggle').addEventListener('click', () => this.toggleTheme());

    // Skills drawer
    document.getElementById('skills-btn').addEventListener('click', () => {
      this.state.skillsDrawerOpen = !this.state.skillsDrawerOpen;
      document.getElementById('skills-drawer').classList.toggle('open');
      if (this.state.skillsDrawerOpen) this.loadSkills();
    });
    document.getElementById('skills-close').addEventListener('click', () => {
      this.state.skillsDrawerOpen = false;
      document.getElementById('skills-drawer').classList.remove('open');
    });
    document.getElementById('create-skill-btn').addEventListener('click', () => this.createSkill());

    // Export buttons (assumes buttons with data-export-id or similar)
    document.addEventListener('click', (e) => {
      const exportBtn = e.target.closest('[data-export-id]');
      if (exportBtn) {
        const id = exportBtn.dataset.exportId;
        const format = exportBtn.dataset.exportFormat || 'json';
        this.exportConversation(id, format);
      }
    });

    // Keyboard shortcut: Ctrl+Shift+N new conversation
    document.addEventListener('keydown', (e) => {
      if (e.ctrlKey && e.shiftKey && e.key === 'N') {
        e.preventDefault();
        this.newConversation();
      }
    });
  }
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => App.init());
