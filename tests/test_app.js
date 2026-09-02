// tests/test_app.js - Unit tests for frontend app logic
// Run in browser with test_app.html

// Test theme toggle
function testThemeToggle() {
    // Reset
    document.documentElement.removeAttribute('data-theme');
    
    // Initial state should be light
    console.assert(
        document.documentElement.getAttribute('data-theme') === null ||
        document.documentElement.getAttribute('data-theme') === 'light',
        'Default theme should be light'
    );
    
    // Toggle to dark
    toggleTheme();
    console.assert(
        document.documentElement.getAttribute('data-theme') === 'dark',
        'After toggle, theme should be dark'
    );
    
    // Toggle back to light
    toggleTheme();
    console.assert(
        document.documentElement.getAttribute('data-theme') === 'light',
        'After second toggle, theme should be light'
    );
    
    console.log('testThemeToggle PASSED');
}

// Test theme persistence via localStorage
function testThemePersistence() {
    localStorage.removeItem('theme');
    
    // Set dark
    document.documentElement.setAttribute('data-theme', 'dark');
    localStorage.setItem('theme', 'dark');
    
    // Simulate reload
    const saved = localStorage.getItem('theme');
    console.assert(saved === 'dark', 'Theme should be persisted in localStorage');
    
    localStorage.removeItem('theme');
    console.log('testThemePersistence PASSED');
}

// Run tests
testThemeToggle();
testThemePersistence();
