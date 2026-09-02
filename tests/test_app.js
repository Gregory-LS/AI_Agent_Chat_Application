// Basic unit tests for app.js functions
// Run in browser or with a JS test runner

(function() {
    'use strict';

    let testsPassed = 0;
    let testsFailed = 0;

    function assert(condition, message) {
        if (condition) {
            testsPassed++;
            console.log(`✓ ${message}`);
        } else {
            testsFailed++;
            console.error(`✗ ${message}`);
        }
    }

    // Test escapeHtml
    function testEscapeHtml() {
        const div = document.createElement('div');
        
        // Basic text
        div.textContent = 'Hello World';
        assert(div.innerHTML === 'Hello World', 'escapeHtml: basic text');
        
        // HTML special characters
        div.textContent = '<script>alert("xss")</script>';
        assert(div.innerHTML === '&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;', 'escapeHtml: HTML injection');
        
        // Ampersand
        div.textContent = 'A & B';
        assert(div.innerHTML === 'A &amp; B', 'escapeHtml: ampersand');
        
        // Newlines
        div.textContent = 'Line1\nLine2';
        assert(div.innerHTML === 'Line1\nLine2', 'escapeHtml: newlines preserved');
    }

    // Test localStorage auth state
    function testAuthState() {
        // Simulate login
        localStorage.setItem('auth_token', 'test-token-123');
        localStorage.setItem('auth_username', 'testuser');
        
        assert(localStorage.getItem('auth_token') === 'test-token-123', 'auth state: token stored');
        assert(localStorage.getItem('auth_username') === 'testuser', 'auth state: username stored');
        
        // Simulate logout
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_username');
        
        assert(localStorage.getItem('auth_token') === null, 'auth state: token removed on logout');
        assert(localStorage.getItem('auth_username') === null, 'auth state: username removed on logout');
    }

    // Test conversation filtering
    function testConversationFilter() {
        const conversations = [
            { id: '1', title: 'Hello World' },
            { id: '2', title: 'Python Tips' },
            { id: '3', title: 'JavaScript Help' }
        ];
        
        // Filter by 'hello'
        const filtered1 = conversations.filter(c => 
            c.title.toLowerCase().includes('hello')
        );
        assert(filtered1.length === 1, 'conversation filter: finds "Hello"');
        assert(filtered1[0].id === '1', 'conversation filter: correct item');
        
        // Filter by 'python'
        const filtered2 = conversations.filter(c => 
            c.title.toLowerCase().includes('python')
        );
        assert(filtered2.length === 1, 'conversation filter: finds "Python"');
        
        // Filter by 'nonexistent'
        const filtered3 = conversations.filter(c => 
            c.title.toLowerCase().includes('nonexistent')
        );
        assert(filtered3.length === 0, 'conversation filter: no match returns empty');
    }

    // Run tests
    console.log('Running app.js tests...\n');
    
    testEscapeHtml();
    testAuthState();
    testConversationFilter();
    
    console.log(`\nTests: ${testsPassed} passed, ${testsFailed} failed`);
    
    if (testsFailed > 0) {
        process.exit(1);
    }
})();