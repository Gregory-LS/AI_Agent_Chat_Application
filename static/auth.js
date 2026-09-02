// Authentication module
const Auth = {
    currentUser: null,

    async init() {
        try {
            const resp = await fetch('/api/auth/me', { credentials: 'include' });
            if (resp.ok) {
                const data = await resp.json();
                this.currentUser = data.username;
            }
        } catch (e) {
            // Not logged in
        }
        this.render();
    },

    async login(username, password) {
        const resp = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ username, password })
        });
        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.error || 'Login failed');
        }
        const data = await resp.json();
        this.currentUser = data.username;
        this.render();
    },

    async register(username, password) {
        const resp = await fetch('/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ username, password })
        });
        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.error || 'Registration failed');
        }
        const data = await resp.json();
        this.currentUser = data.username;
        this.render();
    },

    async logout() {
        await fetch('/api/auth/logout', {
            method: 'POST',
            credentials: 'include'
        });
        this.currentUser = null;
        this.render();
    },

    render() {
        const authContainer = document.getElementById('auth-container');
        if (!authContainer) return;
        if (this.currentUser) {
            authContainer.innerHTML = `
                <div class="auth-status">
                    <span>Logged in as <strong>${this.currentUser}</strong></span>
                    <button onclick="Auth.logout()" class="btn-logout">Logout</button>
                </div>
            `;
        } else {
            authContainer.innerHTML = `
                <div class="auth-forms">
                    <div class="auth-form login-form">
                        <h3>Login</h3>
                        <input type="text" id="login-username" placeholder="Username" />
                        <input type="password" id="login-password" placeholder="Password" />
                        <button onclick="Auth.handleLogin()">Login</button>
                        <p class="auth-error" id="login-error"></p>
                    </div>
                    <div class="auth-form register-form">
                        <h3>Register</h3>
                        <input type="text" id="register-username" placeholder="Username" />
                        <input type="password" id="register-password" placeholder="Password" />
                        <button onclick="Auth.handleRegister()">Register</button>
                        <p class="auth-error" id="register-error"></p>
                    </div>
                </div>
            `;
        }
    },

    async handleLogin() {
        const username = document.getElementById('login-username').value;
        const password = document.getElementById('login-password').value;
        const errorEl = document.getElementById('login-error');
        try {
            await this.login(username, password);
        } catch (e) {
            errorEl.textContent = e.message;
        }
    },

    async handleRegister() {
        const username = document.getElementById('register-username').value;
        const password = document.getElementById('register-password').value;
        const errorEl = document.getElementById('register-error');
        try {
            await this.register(username, password);
        } catch (e) {
            errorEl.textContent = e.message;
        }
    }
};

document.addEventListener('DOMContentLoaded', () => Auth.init());
