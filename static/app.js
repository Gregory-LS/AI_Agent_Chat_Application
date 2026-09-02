// app.js — Claude-style chat frontend
// State management, streaming fetch, model picker, skills, conversations, theme toggle

(function () {
  'use strict';

  // ===== State =====
  const state = {
    config: { theme: 'light', defaultModel: '', apiKey: '' },
    conversations: [],
    currentConversationId: null,
    messages: [],
    models: [],
    skills: [],
    activeSkills: [],
    abortController: null,
    streaming: false,
    theme: 'light'
  };

  // ===== DOM refs =====
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => document.querySelectorAll(sel);

  const sidebar = document.getElementById('sidebar');
  const chatArea = document.getElementById('chat-area');
  const composer = document.getElementById('composer');
  const sendBtn = document.getElementById('send-btn');
  const modelPicker = document.getElementById('model-picker');
  const settingsDrawer = document.getElementById('settings-drawer');
  const themeToggle = document.getElementById('theme-toggle');

  // ===== Theme =====
  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    state.theme = theme;
    if (themeToggle) {
      themeToggle.textContent = theme === 'dark' ? '☀️ Light' : '🌙 Dark';
    }
  }

  async function toggleTheme() {
    const newTheme = state.theme === 'dark' ? 'light' : 'dark';
    applyTheme(newTheme);
    state.config.theme = newTheme;
    await saveConfig();
  }

  // ===== Config =====
  async function loadConfig() {
    try {
      const res = await fetch('/api/config');
      if (res.ok) {
        const cfg = await res.json();
        state.config = cfg;
        applyTheme(cfg.theme || 'light');
      }
    } catch (e) {
      console.warn('Failed to load config', e);
    }
  }

  async function saveConfig() {
    try {
      await fetch('/api/config', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(state.config)
      });
    } catch (e) {
      console.warn('Failed to save config', e);
    }
  }

  // ===== Initialization =====
  document.addEventListener('DOMContentLoaded', async () => {
    await loadConfig();
    if (themeToggle) {
      themeToggle.addEventListener('click', toggleTheme);
    }
  });

  // ===== Exports for testing =====
  window.__testState = state;
  window.__testApplyTheme = applyTheme;
  window.__testToggleTheme = toggleTheme;
  window.__testLoadConfig = loadConfig;
  window.__testSaveConfig = saveConfig;
})();
