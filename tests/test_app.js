// tests/test_app.js — Unit tests for app.js keyboard shortcuts
// Run in browser or with headless runner

suite('Keyboard shortcuts', function() {
  setup(function() {
    // Reset state
    state.messageHistory = [];
    state.historyIndex = -1;
    state.pendingMessage = '';
    state.currentConversationId = null;
    state.streaming = false;
    document.getElementById('composer').value = '';
  });

  test('Ctrl+Enter sends message', function() {
    let sent = false;
    const originalSend = sendMessage;
    sendMessage = function() { sent = true; };
    const event = new KeyboardEvent('keydown', { ctrlKey: true, key: 'Enter' });
    document.dispatchEvent(event);
    assert.isTrue(sent);
    sendMessage = originalSend;
  });

  test('Ctrl+Shift+C copies last assistant message', function() {
    let copied = false;
    const originalCopy = copyLastAssistantMessage;
    copyLastAssistantMessage = function() { copied = true; };
    const event = new KeyboardEvent('keydown', { ctrlKey: true, shiftKey: true, key: 'C' });
    document.dispatchEvent(event);
    assert.isTrue(copied);
    copyLastAssistantMessage = originalCopy;
  });

  test('Ctrl+Shift+Delete clears conversation', function() {
    let cleared = false;
    const originalClear = clearConversation;
    clearConversation = function() { cleared = true; };
    const event = new KeyboardEvent('keydown', { ctrlKey: true, shiftKey: true, key: 'Delete' });
    document.dispatchEvent(event);
    assert.isTrue(cleared);
    clearConversation = originalClear;
  });

  test('Ctrl+Shift+N creates new conversation', function() {
    let created = false;
    const originalNew = newConversation;
    newConversation = function() { created = true; };
    const event = new KeyboardEvent('keydown', { ctrlKey: true, shiftKey: true, key: 'N' });
    document.dispatchEvent(event);
    assert.isTrue(created);
    newConversation = originalNew;
  });

  test('Ctrl+Shift+, opens settings', function() {
    let opened = false;
    const originalSettings = openSettings;
    openSettings = function() { opened = true; };
    const event = new KeyboardEvent('keydown', { ctrlKey: true, shiftKey: true, key: ',' });
    document.dispatchEvent(event);
    assert.isTrue(opened);
    openSettings = originalSettings;
  });

  test('Ctrl+Shift+B toggles sidebar', function() {
    let toggled = false;
    const originalToggle = toggleSidebar;
    toggleSidebar = function() { toggled = true; };
    const event = new KeyboardEvent('keydown', { ctrlKey: true, shiftKey: true, key: 'B' });
    document.dispatchEvent(event);
    assert.isTrue(toggled);
    toggleSidebar = originalToggle;
  });

  test('Ctrl+Shift+M opens model picker', function() {
    let opened = false;
    const originalPicker = openModelPicker;
    openModelPicker = function() { opened = true; };
    const event = new KeyboardEvent('keydown', { ctrlKey: true, shiftKey: true, key: 'M' });
    document.dispatchEvent(event);
    assert.isTrue(opened);
    openModelPicker = originalPicker;
  });

  test('Escape closes drawers', function() {
    document.getElementById('settings-drawer').classList.add('open');
    const event = new KeyboardEvent('keydown', { key: 'Escape' });
    document.dispatchEvent(event);
    assert.isFalse(document.getElementById('settings-drawer').classList.contains('open'));
  });

  test('ArrowUp navigates history', function() {
    state.messageHistory = ['Hello', 'How are you?'];
    state.historyIndex = -1;
    document.getElementById('composer').value = '';
    const event = new KeyboardEvent('keydown', { key: 'ArrowUp' });
    document.getElementById('composer').dispatchEvent(event);
    assert.equal(state.historyIndex, 0);
    assert.equal(document.getElementById('composer').value, 'Hello');
  });

  test('ArrowDown navigates history forward', function() {
    state.messageHistory = ['Hello', 'How are you?'];
    state.historyIndex = 0;
    document.getElementById('composer').value = 'Hello';
    const event = new KeyboardEvent('keydown', { key: 'ArrowDown' });
    document.getElementById('composer').dispatchEvent(event);
    assert.equal(state.historyIndex, 1);
    assert.equal(document.getElementById('composer').value, 'How are you?');
  });
});
