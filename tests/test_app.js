// Test file for app.js — theme toggle functionality

(function () {
  'use strict';

  // Mock DOM for testing
  let themeToggleEl;

  function setupDOM() {
    document.body.innerHTML = `
      <div id="sidebar"></div>
      <div id="chat-area"></div>
      <div id="composer"></div>
      <div id="settings-drawer"></div>
      <button id="theme-toggle">🌙 Dark</button>
    `;
    themeToggleEl = document.getElementById('theme-toggle');
  }

  function cleanupDOM() {
    document.body.innerHTML = '';
  }

  // Test suite
  const tests = [
    {
      name: 'applyTheme sets data-theme attribute on html',
      run: () => {
        setupDOM();
        const app = window.__testApplyTheme;
        if (typeof app !== 'function') {
          cleanupDOM();
          return { passed: false, error: 'applyTheme not exported' };
        }
        app('dark');
        const htmlTheme = document.documentElement.getAttribute('data-theme');
        const result = htmlTheme === 'dark';
        cleanupDOM();
        return { passed: result, expected: 'dark', actual: htmlTheme };
      }
    },
    {
      name: 'applyTheme updates state.theme',
      run: () => {
        setupDOM();
        const app = window.__testApplyTheme;
        if (typeof app !== 'function') {
          cleanupDOM();
          return { passed: false, error: 'applyTheme not exported' };
        }
        app('light');
        const result = window.__testState.theme === 'light';
        cleanupDOM();
        return { passed: result, expected: 'light', actual: window.__testState.theme };
      }
    },
    {
      name: 'toggleTheme switches from light to dark',
      run: () => {
        setupDOM();
        const toggle = window.__testToggleTheme;
        if (typeof toggle !== 'function') {
          cleanupDOM();
          return { passed: false, error: 'toggleTheme not exported' };
        }
        // Set initial state to light
        window.__testState.theme = 'light';
        window.__testApplyTheme('light');
        toggle();
        const result = document.documentElement.getAttribute('data-theme') === 'dark';
        cleanupDOM();
        return { passed: result, expected: 'dark', actual: document.documentElement.getAttribute('data-theme') };
      }
    },
    {
      name: 'toggleTheme switches from dark to light',
      run: () => {
        setupDOM();
        const toggle = window.__testToggleTheme;
        if (typeof toggle !== 'function') {
          cleanupDOM();
          return { passed: false, error: 'toggleTheme not exported' };
        }
        window.__testState.theme = 'dark';
        window.__testApplyTheme('dark');
        toggle();
        const result = document.documentElement.getAttribute('data-theme') === 'light';
        cleanupDOM();
        return { passed: result, expected: 'light', actual: document.documentElement.getAttribute('data-theme') };
      }
    },
    {
      name: 'themeToggle button text updates on toggle',
      run: () => {
        setupDOM();
        const toggle = window.__testToggleTheme;
        if (typeof toggle !== 'function') {
          cleanupDOM();
          return { passed: false, error: 'toggleTheme not exported' };
        }
        window.__testState.theme = 'light';
        window.__testApplyTheme('light');
        toggle();
        const btnText = themeToggleEl.textContent;
        const result = btnText === '☀️ Light';
        cleanupDOM();
        return { passed: result, expected: '☀️ Light', actual: btnText };
      }
    }
  ];

  // Run tests
  let passed = 0;
  let failed = 0;
  const results = [];

  for (const test of tests) {
    try {
      const res = test.run();
      if (res.passed) {
        console.log(`✓ ${test.name}`);
        passed++;
        results.push({ name: test.name, status: 'passed' });
      } else {
        console.error(`✗ ${test.name}: expected ${res.expected}, got ${res.actual}`);
        failed++;
        results.push({ name: test.name, status: 'failed', expected: res.expected, actual: res.actual });
      }
    } catch (e) {
      console.error(`✗ ${test.name}: ${e.message}`);
      failed++;
      results.push({ name: test.name, status: 'error', error: e.message });
    }
  }

  console.log(`\n${passed} passed, ${failed} failed`);

  // For test runner
  if (typeof window !== 'undefined') {
    window.__testResults = { passed, failed, results };
  }
})();
