// Agentic Chat - Frontend Application
// State management with authentication support

const AppState = {
    authToken: localStorage.getItem('auth_token') || null,
    username: localStorage.getItem('username') || null,
    isAuthenticated: function() {
        return this.authToken !== null;
    },
    setAuth: function(token, username) {
        this.authToken = token;
        this.username = username;
        localStorage.setItem('auth_token', token);
        localStorage.setItem('username', username);
    },
    clearAuth: function() {
        this.authToken = null;
        this.username = null;
        localStorage.removeItem('auth_token');
        localStorage.removeItem('username');
    },
    getAuthHeaders: function() {
        const headers = {'Content-Type': 'application/json'};
        if (this.authToken) {
            headers['Authorization'] = 'Bearer ' + this.authToken;
        }
        return headers;
    }
};

// Fetch wrapper with auth
async function authFetch(url, options = {}) {
    const headers = options.headers || {};
    const authHeaders = AppState.getAuthHeaders();
    const mergedHeaders = {...authHeaders, ...headers};
    
    const response = await fetch(url, {
        ...options,
        headers: mergedHeaders
    });
    
    if (response.status === 401) {
        // Session expired or invalid
        AppState.clearAuth();
        showAuthModal();
        throw new Error('Authentication required');
    }
    
    return response;
}

// Auth UI functions
function showAuthModal() {
    const modal = document.getElementById('auth-modal');
    if (modal) {
        modal.style.display = 'block';
    }
    updateAuthUI();
}

function hideAuthModal() {
    const modal = document.getElementById('auth-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function showLoginForm() {
    document.getElementById('login-form').style.display = 'block';
    document.getElementById('register-form').style.display = 'none';
}

function showRegisterForm() {
    document.getElementById('login-form').style.display = 'none';
    document.getElementById('register-form').style.display = 'block';
}

async function handleLogin(event) {
    event.preventDefault();
    const form = event.target;
    const username = form.querySelector('[name="username"]').value;
    const password = form.querySelector('[name="password"]').value;
    
    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username, password})
        });
        const data = await response.json();
        
        if (response.ok) {
            AppState.setAuth(data.token, data.username);
            hideAuthModal();
            updateAuthUI();
            loadAppData();
        } else {
            alert(data.error || 'Login failed');
        }
    } catch (error) {
        console.error('Login error:', error);
        alert('Login failed: ' + error.message);
    }
}

async function handleRegister(event) {
    event.preventDefault();
    const form = event.target;
    const username = form.querySelector('[name="username"]').value;
    const password = form.querySelector('[name="password"]').value;
    
    try {
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username, password})
        });
        const data = await response.json();
        
        if (response.ok) {
            alert('Registration successful! Please log in.');
            showLoginForm();
        } else {
            alert(data.error || 'Registration failed');
        }
    } catch (error) {
        console.error('Registration error:', error);
        alert('Registration failed: ' + error.message);
    }
}

async function handleLogout() {
    try {
        await fetch('/api/auth/logout', {
            method: 'POST',
            headers: AppState.getAuthHeaders()
        });
    } catch (error) {
        console.error('Logout error:', error);
    }
    AppState.clearAuth();
    updateAuthUI();
    // Reload page to reset state
    location.reload();
}

function updateAuthUI() {
    const loginBtn = document.getElementById('login-btn');
    const logoutBtn = document.getElementById('logout-btn');
    const userInfo = document.getElementById('user-info');
    
    if (AppState.isAuthenticated()) {
        if (loginBtn) loginBtn.style.display = 'none';
        if (logoutBtn) logoutBtn.style.display = 'block';
        if (userInfo) {
            userInfo.textContent = 'Logged in as: ' + AppState.username;
            userInfo.style.display = 'block';
        }
    } else {
        if (loginBtn) loginBtn.style.display = 'block';
        if (logoutBtn) logoutBtn.style.display = 'none';
        if (userInfo) userInfo.style.display = 'none';
    }
}

async function checkAuth() {
    if (!AppState.authToken) {
        return false;
    }
    
    try {
        const response = await fetch('/api/auth/check', {
            headers: AppState.getAuthHeaders()
        });
        const data = await response.json();
        
        if (data.authenticated) {
            AppState.username = data.username;
            localStorage.setItem('username', data.username);
            return true;
        } else {
            AppState.clearAuth();
            return false;
        }
    } catch (error) {
        console.error('Auth check error:', error);
        return false;
    }
}

function loadAppData() {
    // Load conversations, models, etc. after authentication
    if (typeof loadConversations === 'function') {
        loadConversations();
    }
    if (typeof loadModels === 'function') {
        loadModels();
    }
    if (typeof loadSkills === 'function') {
        loadSkills();
    }
}

// Original streamFetch function (from existing code)
// This is a placeholder - the real implementation would be here
async function streamFetch(url, options = {}) {
    const authOptions = {
        ...options,
        headers: {
            ...AppState.getAuthHeaders(),
            ...(options.headers || {})
        }
    };
    
    const response = await fetch(url, authOptions);
    
    if (response.status === 401) {
        AppState.clearAuth();
        showAuthModal();
        throw new Error('Authentication required');
    }
    
    return response;
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', async function() {
    // Check if user has an existing session
    const authenticated = await checkAuth();
    updateAuthUI();
    
    if (authenticated) {
        loadAppData();
    } else {
        // Show auth modal on first load if not authenticated
        // (Optional: can be removed if you want to allow anonymous usage)
        // showAuthModal();
    }
    
    // Bind auth form handlers
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }
    
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }
    
    const loginBtn = document.getElementById('login-btn');
    if (loginBtn) {
        loginBtn.addEventListener('click', showAuthModal);
    }
    
    // Close modal on backdrop click
    const authModal = document.getElementById('auth-modal');
    if (authModal) {
        authModal.addEventListener('click', function(event) {
            if (event.target === authModal) {
                hideAuthModal();
            }
        });
    }
});

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { AppState, authFetch, streamFetch, handleLogin, handleRegister, handleLogout, checkAuth };
}