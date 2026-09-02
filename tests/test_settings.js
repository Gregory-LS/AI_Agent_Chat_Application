// Tests for settings modal functionality (app.js)

const assert = require('assert');

// Mock DOM for testing
function setupDOM() {
    document.body.innerHTML = `
        <div id="settings-modal" style="display:none;">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Settings</h2>
                    <button id="settings-close" class="close-btn">&times;</button>
                </div>
                <div class="modal-body">
                    <label for="settings-api-key">OpenRouter API Key</label>
                    <input type="password" id="settings-api-key" placeholder="sk-or-...">
                    
                    <label for="settings-default-model">Default Model</label>
                    <select id="settings-default-model">
                        <option value="">None (use first available)</option>
                    </select>
                    
                    <label for="settings-theme">Theme</label>
                    <select id="settings-theme">
                        <option value="light">Light</option>
                        <option value="dark">Dark</option>
                    </select>
                </div>
                <div class="modal-footer">
                    <button id="settings-cancel">Cancel</button>
                    <button id="settings-save" class="primary">Save</button>
                </div>
            </div>
        </div>
        <button id="settings-btn">Settings</button>
        <select id="model-picker"></select>
    `;
}

// Mock localStorage
const localStorageMock = (function() {
    let store = {};
    return {
        getItem: function(key) { return store[key] || null; },
        setItem: function(key, value) { store[key] = String(value); },
        removeItem: function(key) { delete store[key]; },
        clear: function() { store = {}; }
    };
})();
Object.defineProperty(global, 'localStorage', { value: localStorageMock });

// Mock fetch
const fetchMock = (function() {
    let responses = {};
    return {
        __setResponse: function(url, response) {
            responses[url] = response;
        },
        __reset: function() {
            responses = {};
        },
        fetch: async function(url, options) {
            const resp = responses[url];
            if (resp) {
                return {
                    ok: true,
                    json: async () => resp
                };
            }
            return {
                ok: true,
                json: async () => ({})
            };
        }
    };
})();
global.fetch = fetchMock.fetch;

// Load the module (assuming it exports)
const app = require('./app.js');

describe('Settings Modal', function() {
    beforeEach(function() {
        setupDOM();
        fetchMock.__reset();
        localStorageMock.clear();
        // Reset state
        app.state.config = {
            apiKey: '',
            defaultModel: '',
            theme: 'light'
        };
    });

    it('should open settings modal', function() {
        const modal = document.getElementById('settings-modal');
        assert.equal(modal.style.display, 'none');
        app.openSettings();
        assert.equal(modal.style.display, 'flex');
    });

    it('should close settings modal', function() {
        const modal = document.getElementById('settings-modal');
        app.openSettings();
        assert.equal(modal.style.display, 'flex');
        app.closeSettings();
        assert.equal(modal.style.display, 'none');
    });

    it('should populate settings fields from config on open', function() {
        app.state.config.apiKey = 'sk-or-test123';
        app.state.config.defaultModel = 'openai/gpt-4o';
        app.state.config.theme = 'dark';
        app.openSettings();
        assert.equal(document.getElementById('settings-api-key').value, 'sk-or-test123');
        assert.equal(document.getElementById('settings-default-model').value, 'openai/gpt-4o');
        assert.equal(document.getElementById('settings-theme').value, 'dark');
    });

    it('should save settings and close modal', function() {
        document.getElementById('settings-api-key').value = 'sk-or-newkey';
        document.getElementById('settings-default-model').value = 'anthropic/claude-3-opus';
        document.getElementById('settings-theme').value = 'dark';
        
        app.saveSettings();
        
        assert.equal(app.state.config.apiKey, 'sk-or-newkey');
        assert.equal(app.state.config.defaultModel, 'anthropic/claude-3-opus');
        assert.equal(app.state.config.theme, 'dark');
        assert.equal(document.getElementById('settings-modal').style.display, 'none');
    });

    it('should persist theme to localStorage', function() {
        app.state.config.theme = 'dark';
        app.setTheme('dark');
        assert.equal(localStorage.getItem('theme'), 'dark');
        assert.equal(document.documentElement.getAttribute('data-theme'), 'dark');
    });

    it('should load theme from localStorage', function() {
        localStorage.setItem('theme', 'dark');
        app.loadTheme();
        assert.equal(document.documentElement.getAttribute('data-theme'), 'dark');
    });

    it('should load config from API', async function() {
        fetchMock.__setResponse('/api/config', {
            apiKey: 'sk-or-api',
            defaultModel: 'gpt-4',
            theme: 'light'
        });
        await app.loadConfig();
        assert.equal(app.state.config.apiKey, 'sk-or-api');
        assert.equal(app.state.config.defaultModel, 'gpt-4');
        assert.equal(app.state.config.theme, 'light');
    });

    it('should handle keyboard shortcut Ctrl+Shift+, to open settings', function() {
        // Simulate keydown event
        const event = new KeyboardEvent('keydown', {
            ctrlKey: true,
            shiftKey: true,
            key: ','
        });
        document.dispatchEvent(event);
        const modal = document.getElementById('settings-modal');
        assert.equal(modal.style.display, 'flex');
    });

    it('should close settings on Escape', function() {
        app.openSettings();
        const event = new KeyboardEvent('keydown', {
            key: 'Escape'
        });
        document.dispatchEvent(event);
        const modal = document.getElementById('settings-modal');
        assert.equal(modal.style.display, 'none');
    });
});
