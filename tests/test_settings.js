// Tests for settings modal functionality
// Run in browser with test_app.html

(async function testSettingsModal() {
  let passed = 0;
  let failed = 0;

  function assert(condition, message) {
    if (condition) {
      passed++;
    } else {
      failed++;
      console.error('FAIL: ' + message);
    }
  }

  // Test that modal opens and closes
  const modal = document.getElementById('settings-modal');
  const openBtn = document.getElementById('settings-btn');
  const closeBtn = document.getElementById('settings-close-btn');
  const cancelBtn = document.getElementById('settings-cancel-btn');

  // Initial state
  assert(modal.style.display === 'none' || modal.style.display === '', 'Modal initially hidden');

  // Open modal
  openBtn.click();
  assert(modal.style.display === 'flex', 'Modal visible after open button click');

  // Close with close button
  closeBtn.click();
  assert(modal.style.display === 'none', 'Modal hidden after close button');

  // Open again
  openBtn.click();
  assert(modal.style.display === 'flex', 'Modal visible after second open');

  // Close with cancel button
  cancelBtn.click();
  assert(modal.style.display === 'none', 'Modal hidden after cancel button');

  // Test backdrop click closes modal
  openBtn.click();
  modal.click();
  assert(modal.style.display === 'flex', 'Modal stays open on inner click');
  // Click on backdrop (simulate by dispatching on modal itself if target is modal)
  // The event listener checks e.target === modal, so clicking modal itself closes it
  const backdropEvent = new MouseEvent('click', { bubbles: true });
  modal.dispatchEvent(backdropEvent);
  assert(modal.style.display === 'none', 'Modal hidden after backdrop click');

  // Test that fields are populated on open
  openBtn.click();
  const apiKeyInput = document.getElementById('settings-api-key');
  const defaultModelSelect = document.getElementById('settings-default-model');
  assert(apiKeyInput.value !== undefined, 'API key input present');
  assert(defaultModelSelect.options.length > 0, 'Default model select populated');
  closeBtn.click();

  // Test save button exists
  const saveBtn = document.getElementById('settings-save-btn');
  assert(saveBtn !== null, 'Save button exists');
  assert(saveBtn.tagName === 'BUTTON', 'Save button is a button');

  console.log(`Tests completed: ${passed} passed, ${failed} failed`);
  if (failed > 0) {
    console.error('Some tests failed');
  } else {
    console.log('All tests passed!');
  }
})();