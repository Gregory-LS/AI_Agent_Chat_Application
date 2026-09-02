// Tests for settings UI
// Run in browser with test_app.html

async function runSettingsTests() {
  console.log('Running settings tests...');
  
  // Test 1: Settings button exists
  const settingsBtn = document.getElementById('settings-btn');
  if (!settingsBtn) {
    console.error('FAIL: Settings button not found');
    return;
  }
  console.log('PASS: Settings button exists');
  
  // Test 2: Click settings button opens drawer
  settingsBtn.click();
  const drawer = document.getElementById('settings-drawer');
  if (drawer.classList.contains('hidden')) {
    console.error('FAIL: Drawer did not open');
    return;
  }
  console.log('PASS: Drawer opens on settings button click');
  
  // Test 3: Close button hides drawer
  const closeBtn = document.getElementById('settings-close-btn');
  closeBtn.click();
  if (!drawer.classList.contains('hidden')) {
    console.error('FAIL: Drawer did not close');
    return;
  }
  console.log('PASS: Drawer closes on close button click');
  
  // Test 4: Overlay click closes drawer
  settingsBtn.click();
  const overlay = document.getElementById('overlay');
  overlay.click();
  if (!drawer.classList.contains('hidden')) {
    console.error('FAIL: Drawer did not close on overlay click');
    return;
  }
  console.log('PASS: Overlay click closes drawer');
  
  // Test 5: API key input exists
  const apiKeyInput = document.getElementById('api-key-input');
  if (!apiKeyInput) {
    console.error('FAIL: API key input not found');
    return;
  }
  console.log('PASS: API key input exists');
  
  // Test 6: Theme select exists
  const themeSelect = document.getElementById('theme-select');
  if (!themeSelect) {
    console.error('FAIL: Theme select not found');
    return;
  }
  console.log('PASS: Theme select exists');
  
  console.log('All settings tests passed!');
}

// Run tests when page loads
window.addEventListener('load', runSettingsTests);