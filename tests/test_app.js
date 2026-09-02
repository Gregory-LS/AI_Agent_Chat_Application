// test_app.js — Unit tests for app.js (state management, streaming, keyboard shortcuts)

// ============================================================
// Mock environment setup (must be called before any app.js imports)
// ============================================================

function setupMockEnvironment() {
    // Mock localStorage
    global.localStorage = {
        _data: {},
        getItem(key) { return this._data[key] || null; },
        setItem(key, value) { this._data[key] = value; },
        removeItem(key) { delete this._data[key]; },
        clear() { this._data = {}; },
    };

    // Mock document
    global.document = {
        documentElement: {
            setAttribute: () => {},
            getAttribute: () => null,
        },
        addEventListener: (event, handler) => {
            if (!global._eventHandlers) global._eventHandlers = {};
            if (!global._eventHandlers[event]) global._eventHandlers[event] = [];
            global._eventHandlers[event].push(handler);
        },
        getElementById: (id) => {
            // Return mock elements
            return {
                id,
                value: '',
                innerHTML: '',
                classList: {
                    add: () => {},
                    remove: () => {},
                    contains: () => false,
                },
                focus: () => {},
                setSelectionRange: () => {},
                scrollTop: 0,
                scrollHeight: 0,
                tagName: 'div',
                isContentEditable: false,
            };
        },
        createElement: (tag) => ({
            tag,
            textContent: '',
            get innerHTML() { return ''; },
            set innerHTML(v) {},
        }),
    };

    // Mock window
    global.window = {
        addEventListener: (event, handler) => {
            if (!global._windowHandlers) global._windowHandlers = {};
            if (!global._windowHandlers[event]) global._windowHandlers[event] = [];
            global._windowHandlers[event].push(handler);
        },
        confirm: () => true,
        prompt: () => '',
    };

    // Mock fetch
    global.fetch = async (url, options) => {
        return {
            ok: true,
            status: 200,
            json: async () => ({}),
            text: async () => '',
            body: {
                getReader: () => ({
                    read: async () => ({ done: true, value: undefined }),
                }),
            },
        };
    };

    // Mock AbortController
    global.AbortController = function() {
        this.signal = {};
        this.abort = () => {};
    };

    // Mock TextDecoder
    global.TextDecoder = function() {
        this.decode = (value, options) => '';
    };
}

setupMockEnvironment();

// ============================================================
// Import app.js (simulate by loading the file content)
// ============================================================

const fs = require('fs');
const path = require('path');
const appCode = fs.readFileSync(path.join(__dirname, '..', 'static', 'app.js'), 'utf8');

// Evaluate the app code in the mock environment
eval(appCode);

// ============================================================
// Test suite
// ============================================================

function assert(condition, message) {
    if (!condition) {
        console.error('FAIL:', message);
        process.exit(1);
    }
    console.log('PASS:', message);
}

function assertEqual(actual, expected, message) {
    if (actual !== expected) {
        console.error(`FAIL: ${message} — expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
        process.exit(1);
    }
    console.log('PASS:', message);
}

// ============================================================
// Test: Keyboard shortcuts registration
// ============================================================

function testKeyboardShortcutsRegistered() {
    assert(
        global._eventHandlers && global._eventHandlers['keydown'],
        'keydown event handler should be registered'
    );
    assert(
        global._eventHandlers['keydown'].length > 0,
        'At least one keydown handler should be registered'
    );
}

// ============================================================
// Test: Ctrl+Shift+O focuses composer
// ============================================================

function testCtrlShiftO() {
    let focused = false;
    const originalFocus = document.getElementById('composer').focus;
    document.getElementById('composer').focus = () => { focused = true; };

    // Simulate keydown event
    const handler = global._eventHandlers['keydown'][0];
    const event = {
        ctrlKey: true,
        shiftKey: true,
        key: 'O',
        preventDefault: () => {},
        target: { tagName: 'DIV', isContentEditable: false },
    };
    handler(event);

    assert(focused, 'Ctrl+Shift+O should focus composer');

    // Restore
    document.getElementById('composer').focus = originalFocus;
}

// ============================================================
// Test: Ctrl+Shift+N creates new conversation
// ============================================================

function testCtrlShiftN() {
    let newConvCalled = false;
    const originalNewConv = window.newConversation;
    window.newConversation = () => { newConvCalled = true; };

    const handler = global._eventHandlers['keydown'][0];
    const event = {
        ctrlKey: true,
        shiftKey: true,
        key: 'N',
        preventDefault: () => {},
        target: { tagName: 'DIV', isContentEditable: false },
    };
    handler(event);

    assert(newConvCalled, 'Ctrl+Shift+N should call newConversation');

    window.newConversation = originalNewConv;
}

// ============================================================
// Test: Ctrl+Shift+, opens settings
// ============================================================

function testCtrlShiftComma() {
    let settingsOpened = false;
    const originalOpen = window.openSettings;
    window.openSettings = () => { settingsOpened = true; };

    const handler = global._eventHandlers['keydown'][0];
    const event = {
        ctrlKey: true,
        shiftKey: true,
        key: ',',
        preventDefault: () => {},
        target: { tagName: 'DIV', isContentEditable: false },
    };
    handler(event);

    assert(settingsOpened, 'Ctrl+Shift+, should open settings');

    window.openSettings = originalOpen;
}

// ============================================================
// Test: Ctrl+Shift+E opens skills
// ============================================================

function testCtrlShiftE() {
    let skillsOpened = false;
    const originalOpen = window.openSkills;
    window.openSkills = () => { skillsOpened = true; };

    const handler = global._eventHandlers['keydown'][0];
    const event = {
        ctrlKey: true,
        shiftKey: true,
        key: 'E',
        preventDefault: () => {},
        target: { tagName: 'DIV', isContentEditable: false },
    };
    handler(event);

    assert(skillsOpened, 'Ctrl+Shift+E should open skills');

    window.openSkills = originalOpen;
}

// ============================================================
// Test: Escape closes modals / stops generation
// ============================================================

function testEscape() {
    let stopCalled = false;
    let closeSettingsCalled = false;
    let closeSkillsCalled = false;

    const originalStop = window.stopGeneration;
    const originalCloseSettings = window.closeSettings;
    const originalCloseSkills = window.closeSkills;

    window.stopGeneration = () => { stopCalled = true; };
    window.closeSettings = () => { closeSettingsCalled = true; };
    window.closeSkills = () => { closeSkillsCalled = true; };

    const handler = global._eventHandlers['keydown'][0];

    // Test stop generation when streaming
    state.streaming = true;
    const event1 = {
        key: 'Escape',
        preventDefault: () => {},
        target: { tagName: 'DIV', isContentEditable: false },
    };
    handler(event1);
    assert(stopCalled, 'Escape should stop generation when streaming');

    // Test close settings when settings open
    state.streaming = false;
    state.isSettingsOpen = true;
    const event2 = {
        key: 'Escape',
        preventDefault: () => {},
        target: { tagName: 'DIV', isContentEditable: false },
    };
    handler(event2);
    assert(closeSettingsCalled, 'Escape should close settings');

    // Test close skills when skills open
    state.isSettingsOpen = false;
    state.isSkillsOpen = true;
    const event3 = {
        key: 'Escape',
        preventDefault: () => {},
        target: { tagName: 'DIV', isContentEditable: false },
    };
    handler(event3);
    assert(closeSkillsCalled, 'Escape should close skills');

    window.stopGeneration = originalStop;
    window.closeSettings = originalCloseSettings;
    window.closeSkills = originalCloseSkills;
}

// ============================================================
// Test: Ctrl+Shift+Delete clears conversations
// ============================================================

function testCtrlShiftDelete() {
    let clearCalled = false;
    const originalClear = window.clearConversations;
    window.clearConversations = () => { clearCalled = true; };

    const handler = global._eventHandlers['keydown'][0];
    const event = {
        ctrlKey: true,
        shiftKey: true,
        key: 'Delete',
        preventDefault: () => {},
        target: { tagName: 'DIV', isContentEditable: false },
    };
    handler(event);

    assert(clearCalled, 'Ctrl+Shift+Delete should clear conversations');

    window.clearConversations = originalClear;
}

// ============================================================
// Test: Ctrl+Shift+ArrowUp/Down navigates conversations
// ============================================================

function testCtrlShiftArrowUpDown() {
    let navUpCalled = false;
    let navDownCalled = false;

    const originalNav = window.navigateConversation;
    window.navigateConversation = (dir) => {
        if (dir === -1) navUpCalled = true;
        if (dir === 1) navDownCalled = true;
    };

    const handler = global._eventHandlers['keydown'][0];

    const eventUp = {
        ctrlKey: true,
        shiftKey: true,
        key: 'ArrowUp',
        preventDefault: () => {},
        target: { tagName: 'DIV', isContentEditable: false },
    };
    handler(eventUp);
    assert(navUpCalled, 'Ctrl+Shift+ArrowUp should navigate to previous conversation');

    const eventDown = {
        ctrlKey: true,
        shiftKey: true,
        key: 'ArrowDown',
        preventDefault: () => {},
        target: { tagName: 'DIV', isContentEditable: false },
    };
    handler(eventDown);
    assert(navDownCalled, 'Ctrl+Shift+ArrowDown should navigate to next conversation');

    window.navigateConversation = originalNav;
}

// ============================================================
// Test: Ctrl+Shift+S toggles theme
// ============================================================

function testCtrlShiftS() {
    let themeToggled = false;
    const originalToggle = window.toggleTheme;
    window.toggleTheme = () => { themeToggled = true; };

    const handler = global._eventHandlers['keydown'][0];
    const event = {
        ctrlKey: true,
        shiftKey: true,
        key: 'S',
        preventDefault: () => {},
        target: { tagName: 'DIV', isContentEditable: false },
    };
    handler(event);

    assert(themeToggled, 'Ctrl+Shift+S should toggle theme');

    window.toggleTheme = originalToggle;
}

// ============================================================
// Test: Shortcuts don't fire when in input/textarea
// ============================================================

function testShortcutsDontFireInInput() {
    let newConvCalled = false;
    const originalNewConv = window.newConversation;
    window.newConversation = () => { newConvCalled = true; };

    const handler = global._eventHandlers['keydown'][0];
    const event = {
        ctrlKey: true,
        shiftKey: true,
        key: 'N',
        preventDefault: () => {},
        target: { tagName: 'INPUT', isContentEditable: false },
    };
    handler(event);

    assert(!newConvCalled, 'Ctrl+Shift+N should NOT fire when in input');

    window.newConversation = originalNewConv;
}

// ============================================================
// Run all tests
// ============================================================

testKeyboardShortcutsRegistered();
testCtrlShiftO();
testCtrlShiftN();
testCtrlShiftComma();
testCtrlShiftE();
testEscape();
testCtrlShiftDelete();
testCtrlShiftArrowUpDown();
testCtrlShiftS();
testShortcutsDontFireInInput();

console.log('\nAll tests passed!');
