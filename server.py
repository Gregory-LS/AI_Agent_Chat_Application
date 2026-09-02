import asyncio
import json
import websockets

# Store connected clients
connected_clients = set()

async def handler(websocket, path=None):
    # Register client
    connected_clients.add(websocket)
    try:
        # Notify others about new user
        await broadcast(json.dumps({"type": "join", "message": "A new user has joined the chat"}), websocket)
        async for message in websocket:
            data = json.loads(message)
            if data.get("type") == "message":
                await broadcast(json.dumps({"type": "message", "message": data["message"], "user": data.get("user", "Anonymous")}), websocket)
            elif data.get("type") == "leave":
                break
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        # Unregister client and notify others
        connected_clients.remove(websocket)
        await broadcast(json.dumps({"type": "leave", "message": "A user has left the chat"}), websocket)

async def broadcast(message, sender=None):
    if connected_clients:
        await asyncio.wait([client.send(message) for client in connected_clients if client != sender])

def start_server(host="0.0.0.0", port=8765):
    start_server = websockets.serve(handler, host, port)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    start_server()
