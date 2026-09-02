// static/app.js - Frontend JavaScript for Agentic Chat

const App = {
  state: {
    conversations: [],
    currentConversationId: null,
    models: [],
    skills: [],
    config: { apiKey: '', defaultModel: '', theme: 'light' },
    streaming: false,
    abortController: null,
    attachments: [],
  },

  DOM: {},

  async init() {
    this.cacheDOM();
    this.bindEvents();
    await this.loadConfig();
    await this.loadModels();
    await this.loadSkills();
    await this.loadConversations();
    this.applyTheme();
    if (this.state.conversations.length === 0) {
      this.createConversation();
    } else {
      this.switchConversation(this.state.conversations[0].id);
    }
  },

  cacheDOM() {
    this.DOM = {
      sidebar: document.getElementById('sidebar'),
      conversationList: document.getElementById('conversation-list'),
      chatArea: document.getElementById('chat-area'),
      messages: document.getElementById('messages'),
      composer: document.getElementById('composer'),
      textarea: document.getElementById('message-input'),
      sendBtn: document.getElementById('send-btn'),
      modelPicker: document.getElementById('model-picker'),
      modelSearch: document.getElementById('model-search'),
      skillsPanel: document.getElementById('skills-panel'),
      skillsList: document.getElementById('skills-list'),
      settingsModal: document.getElementById('settings-modal'),
      settingsForm: document.getElementById('settings-form'),
      apiKeyInput: document.getElementById('api-key'),
      defaultModelInput: document.getElementById('default-model'),
      themeSelect: document.getElementById('theme-select'),
      attachmentBtn: document.getElementById('attachment-btn'),
      attachmentInput: document.getElementById('attachment-input'),
      attachmentPreview: document.getElementById('attachment-preview'),
      exportBtn: document.getElementById('export-btn'),
      importBtn: document.getElementById('import-btn'),
      importInput: document.getElementById('import-input'),
      stopBtn: document.getElementById('stop-btn'),
      newChatBtn: document.getElementById('new-chat-btn'),
      sidebarToggle: document.getElementById('sidebar-toggle'),
      searchConversations: document.getElementById('search-conversations'),
    };
  },

  bindEvents() {
    // Composer
    this.DOM.sendBtn.addEventListener('click', () => this.sendMessage());
    this.DOM.textarea.addEventListener('keydown', (e) => {
      if (e.ctrlKey && e.key === 'Enter') {
        e.preventDefault();
        this.sendMessage();
      }
    });
    // Stop streaming
    this.DOM.stopBtn.addEventListener('click', () => this.stopStreaming());
    // Model picker search
    this.DOM.modelSearch.addEventListener('input', () => this.renderModelPicker());
    // New conversation
    this.DOM.newChatBtn.addEventListener('click', () => this.createConversation());
    // Sidebar toggle
    this.DOM.sidebarToggle.addEventListener('click', () => this.toggleSidebar());
    // Search conversations
    this.DOM.searchConversations.addEventListener('input', () => this.renderConversationList());
    // Attachments
    this.DOM.attachmentBtn.addEventListener('click', () => this.DOM.attachmentInput.click());
    this.DOM.attachmentInput.addEventListener('change', (e) => this.handleAttachments(e.target.files));
    this.DOM.attachmentPreview.addEventListener('click', (e) => {
      if (e.target.classList.contains('remove-attachment')) {
        const index = parseInt(e.target.dataset.index);
        this.removeAttachment(index);
      }
    });
    // Drag and drop
    document.addEventListener('dragover', (e) => e.preventDefault());
    document.addEventListener('drop', (e) => {
      e.preventDefault();
      if (e.dataTransfer.files.length) {
        this.handleAttachments(e.dataTransfer.files);
      }
    });
    // Settings modal
    document.getElementById('settings-btn').addEventListener('click', () => this.openSettings());
    document.querySelector('.close-modal').addEventListener('click', () => this.closeSettings());
    this.DOM.settingsForm.addEventListener('submit', (e) => {
      e.preventDefault();
      this.saveSettings();
    });
    // Escape to close modals
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        this.closeSettings();
        this.closeSkills();
      }
    });
    // Skills
    document.getElementById('skills-btn').addEventListener('click', () => this.toggleSkills());
    document.getElementById('add-skill-btn').addEventListener('click', () => this.addSkill());
    // Export/Import
    this.DOM.exportBtn.addEventListener('click', () => this.exportConversation());
    this.DOM.importBtn.addEventListener('click', () => this.DOM.importInput.click());
    this.DOM.importInput.addEventListener('change', (e) => this.importConversation(e.target.files[0]));
  },

  /*========== API Helpers ==========*/

  async api(method, path, body) {
    const options = {
      method,
      headers: { 'Content-Type': 'application/json' },
    };
    if (body && method !== 'GET') options.body = JSON.stringify(body);
    const res = await fetch(path, options);
    if (!res.ok) {
      const err = await res.text();
      throw new Error(`API error ${res.status}: ${err}`);
    }
    return res.json();
  },

  /*========== Config ==========*/

  async loadConfig() {
    try {
      const config = await this.api('GET', '/api/config');
      this.state.config = { ...this.state.config, ...config };
      this.DOM.apiKeyInput.value = this.state.config.apiKey || '';
      this.DOM.themeSelect.value = this.state.config.theme || 'light';
    } catch (e) {
      console.warn('Failed to load config:', e);
    }
  },

  async saveSettings() {
    const newConfig = {
      apiKey: this.DOM.apiKeyInput.value.trim(),
      defaultModel: this.DOM.defaultModelInput.value.trim(),
      theme: this.DOM.themeSelect.value,
    };
    await this.api('PUT', '/api/config', newConfig);
    this.state.config = newConfig;
    this.applyTheme();
    this.closeSettings();
    this.renderModelPicker();
  },

  openSettings() {
    this.DOM.settingsModal.style.display = 'block';
  },

  closeSettings() {
    this.DOM.settingsModal.style.display = 'none';
  },

  /*========== Theme ==========*/

  applyTheme() {
    document.documentElement.setAttribute('data-theme', this.state.config.theme || 'light');
  },

  toggleSidebar() {
    this.DOM.sidebar.classList.toggle('collapsed');
  },

  /*========== Models ==========*/

  async loadModels() {
    try {
      const data = await this.api('GET', '/api/models');
      this.state.models = data.data || [];
      this.renderModelPicker();
    } catch (e) {
      console.error('Failed to load models:', e);
    }
  },

  renderModelPicker() {
    const search = this.DOM.modelSearch.value.toLowerCase();
    const container = this.DOM.modelPicker;
    container.innerHTML = '';
    const filtered = this.state.models.filter(m =>
      m.id.toLowerCase().includes(search) ||
      (m.provider && m.provider.name && m.provider.name.toLowerCase().includes(search))
    );
    // Group by provider
    const groups = {};
    filtered.forEach(m => {
      const provider = m.provider ? m.provider.name : 'Other';
      if (!groups[provider]) groups[provider] = [];
      groups[provider].push(m);
    });
    Object.keys(groups).sort().forEach(provider => {
      const groupDiv = document.createElement('div');
      groupDiv.className = 'model-group';
      groupDiv.innerHTML = `<div class="model-group-label">${provider}</div>`;
      groups[provider].forEach(m => {
        const item = document.createElement('div');
        item.className = 'model-item';
        const isSelected = m.id === (this.state.config.defaultModel || this.state.models[0]?.id);
        item.dataset.modelId = m.id;
        item.innerHTML = `
          <span class="model-name">${m.name || m.id}</span>
          <span class="model-id">${m.id}</span>
          <span class="model-pricing">${m.pricing ? \`$${m.pricing.prompt}/$${m.pricing.completion}\` : ''}</span>
        `;
        item.addEventListener('click', () => {
          this.state.config.defaultModel = m.id;
          this.renderModelPicker();
          this.DOM.defaultModelInput.value = m.id;
        });
        if (isSelected) item.classList.add('selected');
        groupDiv.appendChild(item);
      });
      container.appendChild(groupDiv);
    });
  },

  /*========== Conversations ==========*/

  async loadConversations() {
    try {
      this.state.conversations = await this.api('GET', '/api/conversations');
      this.renderConversationList();
    } catch (e) {
      console.error('Failed to load conversations:', e);
    }
  },

  renderConversationList() {
    const query = this.DOM.searchConversations.value.toLowerCase();
    const filtered = this.state.conversations.filter(c =>
      c.title.toLowerCase().includes(query) ||
      c.id.toLowerCase().includes(query)
    );
    this.DOM.conversationList.innerHTML = filtered.map(c => `
      <div class="conversation-item ${c.id === this.state.currentConversationId ? 'active' : ''}" data-id="${c.id}">
        <div class="conversation-title">${c.title || 'New Chat'}</div>
        <div class="conversation-actions">
          <button class="rename-btn" data-id="${c.id}">✎</button>
          <button class="delete-btn" data-id="${c.id}">✕</button>
        </div>
      </div>
    `).join('');
    // Attach events
    this.DOM.conversationList.querySelectorAll('.conversation-item').forEach(el => {
      el.addEventListener('click', (e) => {
        if (!e.target.closest('.conversation-actions')) {
          this.switchConversation(el.dataset.id);
        }
      });
    });
    this.DOM.conversationList.querySelectorAll('.rename-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const id = btn.dataset.id;
        const newTitle = prompt('Rename conversation:', this.getConversation(id).title);
        if (newTitle) this.renameConversation(id, newTitle);
      });
    });
    this.DOM.conversationList.querySelectorAll('.delete-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        if (confirm('Delete this conversation?')) {
          this.deleteConversation(btn.dataset.id);
        }
      });
    });
  },

  getConversation(id) {
    return this.state.conversations.find(c => c.id === id);
  },

  async createConversation() {
    const newConv = await this.api('POST', '/api/conversations', {});
    this.state.conversations.unshift(newConv);
    this.renderConversationList();
    this.switchConversation(newConv.id);
  },

  async switchConversation(id) {
    if (this.state.currentConversationId === id) return;
    this.stopStreaming();
    this.state.currentConversationId = id;
    this.renderConversationList();
    const conv = await this.api('GET', \`/api/conversations/${id}\`);
    this.renderMessages(conv.messages);
  },

  async renameConversation(id, title) {
    await this.api('PATCH', \`/api/conversations/${id}\`, { title });
    const conv = this.getConversation(id);
    if (conv) conv.title = title;
    this.renderConversationList();
  },

  async deleteConversation(id) {
    await this.api('DELETE', \`/api/conversations/${id}\`);
    this.state.conversations = this.state.conversations.filter(c => c.id !== id);
    if (this.state.currentConversationId === id) {
      this.state.currentConversationId = null;
      this.renderMessages([]);
      if (this.state.conversations.length > 0) {
        this.switchConversation(this.state.conversations[0].id);
      } else {
        this.createConversation();
      }
    }
    this.renderConversationList();
  },

  /*========== Messages ==========*/

  renderMessages(messages) {
    this.DOM.messages.innerHTML = messages.map((msg, i) => `
      <div class="message ${msg.role}" data-index="${i}">
        <div class="message-role">${msg.role === 'user' ? 'You' : 'Assistant'}</div>
        <div class="message-content">${this.formatContent(msg.content)}</div>
        ${msg.role === 'assistant' ? `<div class="message-actions"><button class="copy-btn" data-text="${msg.content.replace(/"/g, '&quot;')}">Copy</button></div>` : ''}
      </div>
    `).join('');
    this.DOM.messages.scrollTop = this.DOM.messages.scrollHeight;
    // Attach copy events
    this.DOM.messages.querySelectorAll('.copy-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        navigator.clipboard.writeText(btn.dataset.text);
        btn.textContent = 'Copied!';
        setTimeout(() => (btn.textContent = 'Copy'), 1500);
      });
    });
  },

  formatContent(content) {
    // Simple markdown-like formatting: code blocks, inline code, line breaks
    return content
      .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .split('\n').join('<br>');
  },

  /*========== Send Message & Stream ==========*/

  async sendMessage() {
    const text = this.DOM.textarea.value.trim();
    if (!text && this.state.attachments.length === 0) return;
    if (this.state.streaming) return;
    if (!this.state.currentConversationId) await this.createConversation();

    const message = { role: 'user', content: text };
    // Add attachments as content parts
    if (this.state.attachments.length > 0) {
      message.attachments = this.state.attachments;
    }
    await this.api('POST', \`/api/conversations/${this.state.currentConversationId}/messages\`, message);
    this.DOM.textarea.value = '';
    this.clearAttachments();
    this.showThinking();

    // Auto title if first user message
    const conv = this.getConversation(this.state.currentConversationId);
    if (conv && conv.messages.length === 0 && text) {
      this.autoTitle(text);
    }

    // Start SSE stream
    this.state.streaming = true;
    this.state.abortController = new AbortController();
    this.DOM.stopBtn.style.display = 'inline-block';
    this.DOM.sendBtn.disabled = true;

    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        conversationId: this.state.currentConversationId,
        model: this.state.config.defaultModel || undefined,
      }),
      signal: this.state.abortController.signal,
    });

    if (!response.ok) {
      this.state.streaming = false;
      this.DOM.stopBtn.style.display = 'none';
      this.DOM.sendBtn.disabled = false;
      this.renderMessages(this.getConversation(this.state.currentConversationId)?.messages || []);
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let assistantMessage = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop();
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data === '[DONE]') continue;
          try {
            const parsed = JSON.parse(data);
            const delta = parsed.choices?.[0]?.delta?.content || '';
            assistantMessage += delta;
            this.updateAssistantMessage(assistantMessage);
          } catch (e) {
            console.warn('SSE parse error:', e, line);
          }
        }
      }
    }
    // Finished streaming
    this.state.streaming = false;
    this.DOM.stopBtn.style.display = 'none';
    this.DOM.sendBtn.disabled = false;
    this.hideThinking();
    // Save assistant message
    if (assistantMessage) {
      await this.api('POST', \`/api/conversations/${this.state.currentConversationId}/messages\`, {
        role: 'assistant',
        content: assistantMessage,
      });
      // Reload conversation
      const conv = await this.api('GET', \`/api/conversations/${this.state.currentConversationId}\`);
      this.renderMessages(conv.messages);
    }
  },

  showThinking() {
    const el = document.createElement('div');
    el.className = 'thinking';
    el.id = 'thinking-indicator';
    el.innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span>';
    this.DOM.messages.appendChild(el);
    this.DOM.messages.scrollTop = this.DOM.messages.scrollHeight;
  },

  hideThinking() {
    const el = document.getElementById('thinking-indicator');
    if (el) el.remove();
  },

  updateAssistantMessage(text) {
    let el = document.getElementById('streaming-message');
    if (!el) {
      el = document.createElement('div');
      el.id = 'streaming-message';
      el.className = 'message assistant streaming';
      el.innerHTML = '<div class="message-role">Assistant</div><div class="message-content"></div>';
      this.DOM.messages.appendChild(el);
    }
    el.querySelector('.message-content').innerHTML = this.formatContent(text);
    this.DOM.messages.scrollTop = this.DOM.messages.scrollHeight;
  },

  stopStreaming() {
    if (this.state.abortController) {
      this.state.abortController.abort();
      this.state.streaming = false;
      this.DOM.stopBtn.style.display = 'none';
      this.DOM.sendBtn.disabled = false;
      this.hideThinking();
      const el = document.getElementById('streaming-message');
      if (el) el.classList.remove('streaming');
    }
  },

  async autoTitle(text) {
    // Just use first few words
    const title = text.split(' ').slice(0, 6).join(' ') + (text.split(' ').length > 6 ? '...' : '');
    await this.renameConversation(this.state.currentConversationId, title);
  },

  /*========== Attachments ==========*/

  async handleAttachments(files) {
    for (const file of files) {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch('/api/attachments', { method: 'POST', body: formData });
      if (res.ok) {
        const data = await res.json();
        this.state.attachments.push({ id: data.id, filename: file.name, type: file.type });
        this.renderAttachmentPreview();
      }
    }
  },

  removeAttachment(index) {
    this.state.attachments.splice(index, 1);
    this.renderAttachmentPreview();
  },

  clearAttachments() {
    this.state.attachments = [];
    this.renderAttachmentPreview();
  },

  renderAttachmentPreview() {
    this.DOM.attachmentPreview.innerHTML = this.state.attachments.map((a, i) => `
      <span class="attachment-tag">${a.filename} <button class="remove-attachment" data-index="${i}">✕</button></span>
    `).join('');
  },

  /*========== Skills ==========*/

  async loadSkills() {
    try {
      this.state.skills = await this.api('GET', '/api/skills');
      this.renderSkills();
    } catch (e) {
      console.error('Failed to load skills:', e);
    }
  },

  toggleSkills() {
    this.DOM.skillsPanel.classList.toggle('open');
  },

  closeSkills() {
    this.DOM.skillsPanel.classList.remove('open');
  },

  renderSkills() {
    this.DOM.skillsList.innerHTML = this.state.skills.map(s => `
      <div class="skill-item">
        <label><input type="checkbox" ${s.enabled ? 'checked' : ''} data-id="${s.id}" class="skill-toggle"> ${s.name}</label>
        <div class="skill-prompt">${s.prompt || ''}</div>
        <button class="delete-skill" data-id="${s.id}">✕</button>
      </div>
    `).join('');
    this.DOM.skillsList.querySelectorAll('.skill-toggle').forEach(cb => {
      cb.addEventListener('change', () => this.toggleSkill(cb.dataset.id, cb.checked));
    });
    this.DOM.skillsList.querySelectorAll('.delete-skill').forEach(btn => {
      btn.addEventListener('click', () => this.deleteSkill(btn.dataset.id));
    });
  },

  async toggleSkill(id, enabled) {
    await this.api('PATCH', \`/api/skills/${id}\`, { enabled });
    const skill = this.state.skills.find(s => s.id === id);
    if (skill) skill.enabled = enabled;
  },

  async addSkill() {
    const name = prompt('Skill name:');
    if (!name) return;
    const prompt = prompt('System prompt (optional):');
    const newSkill = await this.api('POST', '/api/skills', { name, prompt, enabled: true });
    this.state.skills.push(newSkill);
    this.renderSkills();
  },

  async deleteSkill(id) {
    await this.api('DELETE', \`/api/skills/${id}\`);
    this.state.skills = this.state.skills.filter(s => s.id !== id);
    this.renderSkills();
  },

  /*========== Export/Import ==========*/

  async exportConversation() {
    if (!this.state.currentConversationId) return;
    const format = confirm('Export as Markdown? Click OK for Markdown, Cancel for JSON.') ? 'markdown' : 'json';
    const res = await fetch(\`/api/conversations/${this.state.currentConversationId}/export?format=${format}\`);
    if (res.ok) {
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = \`conversation.${format === 'markdown' ? 'md' : 'json'}\`;
      a.click();
      URL.revokeObjectURL(url);
    }
  },

  async importConversation(file) {
    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const data = JSON.parse(e.target.result);
        await this.api('POST', '/api/conversations/import', data);
        await this.loadConversations();
      } catch (err) {
        alert('Invalid import file');
      }
    };
    reader.readAsText(file);
  },
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => App.init());
