# Chat Application

A simple real-time chat application using WebSockets.

## Features

- WebSocket-based messaging
- User join/leave notifications
- Broadcast messages to all connected clients

## Backend (Python)

### Prerequisites

- Python 3.7+
- `websockets` library: `pip install websockets`

### Running

```bash
python server.py
```

The server will start on `ws://0.0.0.0:8765`.

### Testing

```bash
pytest tests/test_server.py -v
```

## Frontend (JavaScript)

### Files

- `app.js`: Contains the `ChatApp` class for WebSocket communication.

### Usage

```html
<script src="app.js"></script>
<script>
    const chat = new ChatApp('ws://localhost:8765');
    chat.connect();

    chat.onMessage((data) => {
        console.log(`${data.user}: ${data.message}`);
    });

    chat.onJoin((data) => {
        console.log(data.message);
    });

    chat.onLeave((data) => {
        console.log(data.message);
    });

    // Send a message
    chat.sendMessage('Hello!', 'Alice');
</script>
```

### Running Tests

```bash
npm install
npm test
```

## License

MIT
