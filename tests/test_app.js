const ChatApp = require('../app.js');

// Simple mock for WebSocket (Node.js environment)
global.WebSocket = require('ws');

describe('ChatApp', () => {
    let chat;
    let server;

    beforeAll(() => {
        // Setup a mock server using ws library or similar; for now we just test constructor
    });

    beforeEach(() => {
        chat = new ChatApp('ws://localhost:12345');
    });

    test('constructor should set serverUrl', () => {
        expect(chat.serverUrl).toBe('ws://localhost:12345');
    });

    test('should have empty handlers on init', () => {
        expect(chat.messageHandlers).toHaveLength(0);
        expect(chat.joinHandlers).toHaveLength(0);
        expect(chat.leaveHandlers).toHaveLength(0);
    });

    test('onMessage should add handler', () => {
        const handler = jest.fn();
        chat.onMessage(handler);
        expect(chat.messageHandlers).toHaveLength(1);
        expect(chat.messageHandlers[0]).toBe(handler);
    });

    test('onJoin should add handler', () => {
        const handler = jest.fn();
        chat.onJoin(handler);
        expect(chat.joinHandlers).toHaveLength(1);
        expect(chat.joinHandlers[0]).toBe(handler);
    });

    test('onLeave should add handler', () => {
        const handler = jest.fn();
        chat.onLeave(handler);
        expect(chat.leaveHandlers).toHaveLength(1);
        expect(chat.leaveHandlers[0]).toBe(handler);
    });

    test('sendMessage should not fail if not connected', () => {
        // Should log error, not throw
        expect(() => chat.sendMessage('test', 'user')).not.toThrow();
    });

    test('disconnect should not fail if not connected', () => {
        expect(() => chat.disconnect()).not.toThrow();
    });
});
