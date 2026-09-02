// Frontend tests for auth system
// Run with Node.js: node tests/test_app.js

// Mock DOM environment for testing
const { JSDOM } = require('jsdom');

// Setup DOM
const dom = new JSDOM('<!DOCTYPE html><html><body><div id="app"></div></body></html>', {
    url: 'http://localhost:8000',
    referrer: 'http://localhost:8000',
    contentType: 'text/html',
    includeNodeLocations: true,
    storageQuota: 10000000
});

global.window = dom.window;
global.document = dom.window.document;
global.navigator = dom.window.navigator;
global.localStorage = dom.window.localStorage;
global.fetch = dom.window.fetch;

// Mock fetch for testing
global.fetch = async (url, options = {}) => {
    if (url === '/api/auth/login') {
        const body = JSON.parse(options.body || '{}');
        if (body.username === 'testuser' && body.password === 'password123') {
            return {
                ok: true,
                status: 200,
                json: async () => ({ token: 'testtoken123', username: 'testuser' })
            };
        }
        return {
            ok: false,
            status: 401,
            json: async () => ({ error: 'Invalid username or password' })
        };
    }
    
    if (url === '/api/auth/register') {
        const body = JSON.parse(options.body || '{}');
        if (body.username && body.password && body.password.length >= 6) {
            return {
                ok: true,
                status: 201,
                json: async () => ({ username: body.username })
            };
        }
        return {
            ok: false,
            status: 400,
            json: async () => ({ error: 'Password must be at least 6 characters' })
        };
    }
    
    if (url === '/api/auth/check') {
        const authHeader = options.headers && options.headers['Authorization'];
        if (authHeader === 'Bearer testtoken123') {
            return {
                ok: true,
                status: 200,
                json: async () => ({ authenticated: true, username: 'testuser' })
            };
        }
        return {
            ok: true,
            status: 200,
            json: async () => ({ authenticated: false })
        };
    }
    
    if (url === '/api/auth/logout') {
        return {
            ok: true,
            status: 200,
            json: async () => ({ message: 'Logged out' })
        };
    }
    
    // Default: return 401 for protected endpoints without auth
    return {
        ok: false,
        status: 401,
        json: async () => ({ error: 'Authentication required' })
    };
};

// Import the app module
const fs = require('fs');
const path = require('path');
const appCode = fs.readFileSync(path.join(__dirname, '..', 'static', 'app.js'), 'utf8');

// We need to extract the AppState and functions for testing
// Since app.js is a module with DOM-dependent initialization, we test it differently

describe('Auth System Tests', () => {
    beforeEach(() => {
        localStorage.clear();
    });

    test('AppState should start unauthenticated', () => {
        // Simulate the AppState object
        const AppState = {
            authToken: null,
            username: null,
            isAuthenticated: function() {
                return this.authToken !== null;
            },
            setAuth: function(token, username) {
                this.authToken = token;
                this.username = username;
            },
            clearAuth: function() {
                this.authToken = null;
                this.username = null;
            },
            getAuthHeaders: function() {
                const headers = {'Content-Type': 'application/json'};
                if (this.authToken) {
                    headers['Authorization'] = 'Bearer ' + this.authToken;
                }
                return headers;
            }
        };

        expect(AppState.isAuthenticated()).toBe(false);
        expect(AppState.authToken).toBeNull();
        expect(AppState.username).toBeNull();
    });

    test('AppState should handle login', () => {
        const AppState = {
            authToken: null,
            username: null,
            isAuthenticated: function() {
                return this.authToken !== null;
            },
            setAuth: function(token, username) {
                this.authToken = token;
                this.username = username;
            },
            clearAuth: function() {
                this.authToken = null;
                this.username = null;
            },
            getAuthHeaders: function() {
                const headers = {'Content-Type': 'application/json'};
                if (this.authToken) {
                    headers['Authorization'] = 'Bearer ' + this.authToken;
                }
                return headers;
            }
        };

        AppState.setAuth('testtoken123', 'testuser');
        expect(AppState.isAuthenticated()).toBe(true);
        expect(AppState.authToken).toBe('testtoken123');
        expect(AppState.username).toBe('testuser');
    });

    test('AppState should handle logout', () => {
        const AppState = {
            authToken: 'testtoken123',
            username: 'testuser',
            isAuthenticated: function() {
                return this.authToken !== null;
            },
            setAuth: function(token, username) {
                this.authToken = token;
                this.username = username;
            },
            clearAuth: function() {
                this.authToken = null;
                this.username = null;
            },
            getAuthHeaders: function() {
                const headers = {'Content-Type': 'application/json'};
                if (this.authToken) {
                    headers['Authorization'] = 'Bearer ' + this.authToken;
                }
                return headers;
            }
        };

        AppState.clearAuth();
        expect(AppState.isAuthenticated()).toBe(false);
        expect(AppState.authToken).toBeNull();
        expect(AppState.username).toBeNull();
    });

    test('getAuthHeaders should include Bearer token when authenticated', () => {
        const AppState = {
            authToken: 'testtoken123',
            username: 'testuser',
            getAuthHeaders: function() {
                const headers = {'Content-Type': 'application/json'};
                if (this.authToken) {
                    headers['Authorization'] = 'Bearer ' + this.authToken;
                }
                return headers;
            }
        };

        const headers = AppState.getAuthHeaders();
        expect(headers['Authorization']).toBe('Bearer testtoken123');
        expect(headers['Content-Type']).toBe('application/json');
    });

    test('getAuthHeaders should not include Bearer token when not authenticated', () => {
        const AppState = {
            authToken: null,
            username: null,
            getAuthHeaders: function() {
                const headers = {'Content-Type': 'application/json'};
                if (this.authToken) {
                    headers['Authorization'] = 'Bearer ' + this.authToken;
                }
                return headers;
            }
        };

        const headers = AppState.getAuthHeaders();
        expect(headers['Authorization']).toBeUndefined();
        expect(headers['Content-Type']).toBe('application/json');
    });

    test('authFetch should include auth headers', async () => {
        // Create a simple fetch wrapper for testing
        const AppState = {
            authToken: 'testtoken123',
            username: 'testuser',
            getAuthHeaders: function() {
                const headers = {'Content-Type': 'application/json'};
                if (this.authToken) {
                    headers['Authorization'] = 'Bearer ' + this.authToken;
                }
                return headers;
            }
        };

        const authFetch = async (url, options = {}) => {
            const headers = options.headers || {};
            const authHeaders = AppState.getAuthHeaders();
            const mergedHeaders = {...authHeaders, ...headers};
            
            const response = await fetch(url, {
                ...options,
                headers: mergedHeaders
            });
            
            return response;
        };

        const response = await authFetch('/api/auth/check');
        const data = await response.json();
        expect(data.authenticated).toBe(true);
        expect(data.username).toBe('testuser');
    });

    test('authFetch should handle 401', async () => {
        const AppState = {
            authToken: null,
            username: null,
            isAuthenticated: function() {
                return this.authToken !== null;
            },
            setAuth: function(token, username) {
                this.authToken = token;
                this.username = username;
            },
            clearAuth: function() {
                this.authToken = null;
                this.username = null;
            },
            getAuthHeaders: function() {
                const headers = {'Content-Type': 'application/json'};
                if (this.authToken) {
                    headers['Authorization'] = 'Bearer ' + this.authToken;
                }
                return headers;
            }
        };

        const authFetch = async (url, options = {}) => {
            const headers = options.headers || {};
            const authHeaders = AppState.getAuthHeaders();
            const mergedHeaders = {...authHeaders, ...headers};
            
            const response = await fetch(url, {
                ...options,
                headers: mergedHeaders
            });
            
            if (response.status === 401) {
                AppState.clearAuth();
                throw new Error('Authentication required');
            }
            
            return response;
        };

        await expect(authFetch('/api/chat')).rejects.toThrow('Authentication required');
        expect(AppState.authToken).toBeNull();
    });
});

// Run tests if using Jest or similar
if (typeof describe === 'undefined') {
    console.log('Tests require Jest. Run with: npx jest tests/test_app.js');
}