// Unit tests for app.js
// Run with Node.js or in browser via test_app.html

const { state, login, register, logout, checkAuth } = require('../static/app.js');

// Mock fetch for testing
let mockFetchResponses = [];
global.fetch = async (url, options) => {
    const response = mockFetchResponses.shift();
    if (!response) {
        return new Response(JSON.stringify({}), { status: 200 });
    }
    return response;
};

function mockResponse(data, status = 200) {
    return new Response(JSON.stringify(data), {
        status: status,
        headers: { 'Content-Type': 'application/json' }
    });
}

// Tests
async function runTests() {
    let passed = 0;
    let failed = 0;

    function assert(condition, message) {
        if (condition) {
            console.log(`✓ ${message}`);
            passed++;
        } else {
            console.error(`✗ ${message}`);
            failed++;
        }
    }

    // Test 1: checkAuth when not logged in
    mockFetchResponses = [mockResponse({ user: null })];
    await checkAuth();
    assert(state.user === null, 'checkAuth returns null when not logged in');

    // Test 2: checkAuth when logged in
    mockFetchResponses = [mockResponse({ user: 'testuser' })];
    await checkAuth();
    assert(state.user === 'testuser', 'checkAuth returns user when logged in');

    // Test 3: login success
    mockFetchResponses = [mockResponse({ status: 'ok', user: 'testuser' })];
    await login('testuser', 'password123');
    assert(state.user === 'testuser', 'login sets user on success');

    // Test 4: login failure
    mockFetchResponses = [mockResponse({ error: 'Invalid credentials' }, 401)];
    try {
        await login('testuser', 'wrongpassword');
        // Should have thrown or returned without changing state
    } catch (e) {
        // Expected
    }
    // State should still be 'testuser' from previous test since we didn't clear it
    assert(state.user === 'testuser', 'login does not change state on failure');

    // Test 5: register success
    mockFetchResponses = [mockResponse({ status: 'ok', user: 'newuser' }, 201)];
    await register('newuser', 'newpassword');
    assert(state.user === 'newuser', 'register sets user on success');

    // Test 6: logout
    mockFetchResponses = [mockResponse({ status: 'ok' })];
    await logout();
    assert(state.user === null, 'logout clears user');

    console.log(`\nTests: ${passed} passed, ${failed} failed`);
    process.exit(failed > 0 ? 1 : 0);
}

runTests().catch(e => {
    console.error('Test suite error:', e);
    process.exit(1);
});
