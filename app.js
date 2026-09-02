// Frontend chat logic using WebSocket
class ChatApp {
    constructor(serverUrl) {
        this.serverUrl = serverUrl || 'ws://localhost:8765';
        this.ws = null;
        this.messageHandlers = [];
        this.joinHandlers = [];
        this.leaveHandlers = [];
    }

    connect() {
        this.ws = new WebSocket(this.serverUrl);

        this.ws.onopen = () => {
            console.log('Connected to chat server');
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            switch (data.type) {
                case 'message':
                    this.messageHandlers.forEach(handler => handler(data));
                    break;
                case 'join':
                    this.joinHandlers.forEach(handler => handler(data));
                    break;
                case 'leave':
                    this.leaveHandlers.forEach(handler => handler(data));
                    break;
                default:
                    console.warn('Unknown message type:', data.type);
            }
        };

        this.ws.onclose = () => {
            console.log('Disconnected from chat server');
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }

    sendMessage(message, user) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            const payload = JSON.stringify({ type: 'message', message, user: user || 'Anonymous' });
            this.ws.send(payload);
        } else {
            console.error('WebSocket is not open');
        }
    }

    disconnect() {
        if (this.ws) {
            this.ws.send(JSON.stringify({ type: 'leave' }));
            this.ws.close();
        }
    }

    onMessage(handler) {
        this.messageHandlers.push(handler);
    }

    onJoin(handler) {
        this.joinHandlers.push(handler);
    }

    onLeave(handler) {
        this.leaveHandlers.push(handler);
    }
}

// Export for Node.js testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ChatApp;
}
