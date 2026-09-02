// app.js - Main application logic
// ... existing code ...

// Theme toggle
function toggleTheme() {
    const html = document.documentElement;
    const current = html.getAttribute('data-theme') || 'light';
    const next = current === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
    // Save to server config
    fetch('/api/config', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ theme: next })
    }).catch(() => {});
    // Update toggle button text
    const btn = document.getElementById('theme-toggle');
    if (btn) btn.textContent = next === 'dark' ? '☀️ Light' : '🌙 Dark';
}

// Load theme from config on startup
async function loadTheme() {
    try {
        const resp = await fetch('/api/config');
        const config = await resp.json();
        const theme = config.theme || 'light';
        document.documentElement.setAttribute('data-theme', theme);
        const btn = document.getElementById('theme-toggle');
        if (btn) btn.textContent = theme === 'dark' ? '☀️ Light' : '🌙 Dark';
    } catch (e) {
        // fallback to localStorage or light
        const theme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', theme);
    }
}

// ... rest of existing app.js ...

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    loadTheme();
    // ... other initialization ...
});
