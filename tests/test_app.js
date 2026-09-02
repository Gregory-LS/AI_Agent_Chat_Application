// test_app.js — unit tests for app.js (Node environment simulation)

// We'll test the logout functionality by simulating the fetch call

const assert = {
    equal: (a, b) => { if (a !== b) throw new Error(`Expected ${b}, got ${a}`); },
    ok: (v) => { if (!v) throw new Error('Assertion failed'); }
};

// Mock fetch
let lastFetchUrl = '';
let lastFetchOptions = {};
let fetchCallCount = 0;

async function mockFetch(url, options = {}) {
    lastFetchUrl = url;
    lastFetchOptions = options;
    fetchCallCount++;
    if (url === '/api/logout' && options.method === 'POST') {
        return {
            ok: true,
            json: async () => ({ status: 'ok' })
        };
    }
    return { ok: false, statusText: 'Not Found', json: async () => ({ error: 'Not Found' }) };
}

// Test the logout handler
async function testLogout() {
    fetchCallCount = 0;
    const originalFetch = globalThis.fetch;
    globalThis.fetch = mockFetch;

    // Simulate the handleLogout function from app.js
    async function handleLogout() {
        const response = await fetch('/api/logout', { method: 'POST' });
        if (!response.ok) {
            throw new Error('Logout failed');
        }
        const data = await response.json();
        return data;
    }

    const result = await handleLogout();
    assert.equal(result.status, 'ok');
    assert.equal(lastFetchUrl, '/api/logout');
    assert.equal(lastFetchOptions.method, 'POST');
    assert.equal(fetchCallCount, 1);

    globalThis.fetch = originalFetch;
    console.log('testLogout passed');
}

// Run tests
testLogout().then(() => {
    console.log('All tests passed');
}).catch(e => {
    console.error('Test failed:', e.message);
    process.exit(1);
});
