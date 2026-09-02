// Tests for settings modal UI
// Run in browser with test_app.html

async function runSettingsTests() {
  console.log('Running settings modal tests...');
  
  // Test 1: Settings button exists
  const settingsBtn = document.getElementById('settings-btn');
  if (!settingsBtn) {
    console.error('FAIL: Settings button not found');
    return;
  }
  console.log('PASS: Settings button exists');
  
  // Test 2: Click settings button opens modal
  settingsBtn.click();
  const modal = document.getElementById('settings-modal');
  if (modal.classList.contains('hidden')) {
    console.error('FAIL: Modal did not open');
    return;
  }
  console.log('PASS: Modal opens on settings button click');
  
  // Test 3: Close button hides modal
  const closeBtn = document.getElementById('settings-close-btn');
  closeBtn.click();
  if (!modal.classList.contains('hidden')) {
    console.error('FAIL: Modal did not close');
    return;
  }
  console.log('PASS: Modal closes on close button click');
  
  // Test 4: Overlay click closes modal
  settingsBtn.click();
  const overlay = document.getElementById('overlay');
  overlay.click();
  if (!modal.classList.contains('hidden')) {
    console.error('FAIL: Modal did not close on overlay click');
    return;
  }
  console.log('PASS: Overlay click closes modal');
  
  // Test 5: API key input exists
  settingsBtn.click();
  const apiKeyInput = document.getElementById('api-key-input');
  if (!apiKeyInput) {
    console.error('FAIL: API key input not found');
    return;
  }
  console.log('PASS: API key input exists');
  
  // Test 6: Default model select exists
  const defaultModelSelect = document.getElementById('default-model-select');
  if (!defaultModelSelect) {
    console.error('FAIL: Default model select not found');
    return;
  }
  console.log('PASS: Default model select exists');
  
  // Test 7: Theme toggle button exists
  const themeToggle = document.getElementById('theme-toggle');
  if (!themeToggle) {
    console.error('FAIL: Theme toggle button not found');
    return;
  }
  console.log('PASS: Theme toggle button exists');
  
  // Test 8: Balance info exists
  const balanceInfo = document.getElementById('balance-info');
  if (!balanceInfo) {
    console.error('FAIL: Balance info not found');
    return;
  }
  console.log('PASS: Balance info exists');
  
  // Test 9: Logout button exists
  const logoutBtn = document.getElementById('logout-btn');
  if (!logoutBtn) {
    console.error('FAIL: Logout button not found');
    return;
  }
  console.log('PASS: Logout button exists');
  
  // Cleanup: close modal
  closeBtn.click();
  
  console.log('All settings modal tests passed!');
}

// Run tests when page loads
window.addEventListener('load', runSettingsTests);
