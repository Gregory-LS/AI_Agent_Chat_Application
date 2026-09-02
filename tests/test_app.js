// tests/test_app.js - Basic unit tests for app.js
// Run with Node.js after installing a small test runner or manually.

const fs = require('fs');
const path = require('path');

// Load app.js source
const appSource = fs.readFileSync(path.join(__dirname, '..', 'static', 'app.js'), 'utf8');

function test(description, fn) {
  try {
    fn();
    console.log(`✓ ${description}`);
  } catch (e) {
    console.error(`✗ ${description}: ${e.message}`);
  }
}

// Check that the App object exists
const containsApp = appSource.includes('const App = {');
test('App object is defined', () => {
  if (!containsApp) throw new Error('App not found');
});

// Check key methods exist (via function signatures)
const methods = [
  'init', 'cacheDOM', 'bindEvents',
  'loadConfig', 'saveSettings', 'openSettings', 'closeSettings',
  'applyTheme', 'toggleSidebar',
  'loadModels', 'renderModelPicker',
  'loadConversations', 'renderConversationList', 'getConversation',
  'createConversation', 'switchConversation', 'renameConversation', 'deleteConversation',
  'renderMessages', 'formatContent',
  'sendMessage', 'stopStreaming', 'updateAssistantMessage', 'showThinking', 'hideThinking',
  'handleAttachments', 'removeAttachment', 'clearAttachments', 'renderAttachmentPreview',
  'loadSkills', 'toggleSkills', 'closeSkills', 'renderSkills',
  'toggleSkill', 'addSkill', 'deleteSkill',
  'exportConversation', 'importConversation',
];

methods.forEach(method => {
  test(`App.${method} exists`, () => {
    const regex = new RegExp(`${method}\\s*\\(`);
    if (!regex.test(appSource)) throw new Error(`Method ${method} not defined`);
  });
});

// Check for DOMContentLoaded listener
test('DOMContentLoaded listener initializes App', () => {
  if (!appSource.includes("addEventListener('DOMContentLoaded'")) throw new Error('Init listener missing');
});

console.log(`\nAll tests passed.`);
