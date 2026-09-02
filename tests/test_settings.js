// Tests for settings modal
// Run in browser with test_app.html

async function runSettingsModalTests() {
  console.log('Running settings modal tests...');

  // Test 1: Settings modal exists
  const modal = document.getElementById('settings-modal');
  if (!modal) {
    console.error('FAIL: Settings modal not found');
    return;
  }
  console.log('PASS: Settings modal exists');

  // Test 2: Modal is initially hidden
  if (!modal.classList.contains('hidden')) {
    console.error('FAIL: Settings modal should be hidden initially');
    return;
  }
  console.log('PASS: Settings modal is initially hidden');

  // Test 3: Open settings modal function exists
  if (typeof openSettingsModal !== 'function') {
    console.error('FAIL: openSettingsModal function not found');
    return;
  }
  console.log('PASS: openSettingsModal function exists');

  // Test 4: Close settings modal function exists
  if (typeof closeSettingsModal !== 'function') {
    console.error('FAIL: closeSettingsModal function not found');
    return;
  }
  console.log('PASS: closeSettingsModal function exists');

  // Test 5: Save settings modal function exists
  if (typeof saveSettingsModal !== 'function') {
    console.error('FAIL: saveSettingsModal function not found');
    return;
  }
  console.log('PASS: saveSettingsModal function exists');

  // Test 6: Modal contains required fields
  const apiKeyInput = document.getElementById('modal-api-key');
  const defaultModelInput = document.getElementById('modal-default-model');
  const themeSelect = document.getElementById('modal-theme');
  const saveBtn = document.getElementById('modal-save-settings');
  const closeBtn = document.getElementById('settings-modal-close');

  if (!apiKeyInput) {
    console.error('FAIL: modal-api-key input not found');
    return;
  }
  if (!defaultModelInput) {
    console.error('FAIL: modal-default-model input not found');
    return;
  }
  if (!themeSelect) {
    console.error('FAIL: modal-theme select not found');
    return;
  }
  if (!saveBtn) {
    console.error('FAIL: modal-save-settings button not found');
    return;
  }
  if (!closeBtn) {
    console.error('FAIL: settings-modal-close button not found');
    return;
  }
  console.log('PASS: All modal fields exist');

  // Test 7: Theme select has light and dark options
  if (themeSelect.options.length < 2) {
    console.error('FAIL: Theme select should have at least 2 options');
    return;
  }
  const hasLight = Array.from(themeSelect.options).some(o => o.value === 'light');
  const hasDark = Array.from(themeSelect.options).some(o => o.value === 'dark');
  if (!hasLight || !hasDark) {
    console.error('FAIL: Theme select missing light or dark option');
    return;
  }
  console.log('PASS: Theme select has light and dark options');

  // Test 8: Close button hides modal
  modal.classList.remove('hidden');
  closeBtn.click();
  if (!modal.classList.contains('hidden')) {
    console.error('FAIL: Modal did not close on close button click');
    return;
  }
  console.log('PASS: Modal closes on close button click');

  // Test 9: Overlay click closes modal
  modal.classList.remove('hidden');
  const overlay = document.getElementById('overlay');
  overlay.click();
  if (!modal.classList.contains('hidden')) {
    console.error('FAIL: Modal did not close on overlay click');
    return;
  }
  console.log('PASS: Modal closes on overlay click');

  console.log('All settings modal tests passed!');
}

// Run tests when page loads
window.addEventListener('load', runSettingsModalTests);
