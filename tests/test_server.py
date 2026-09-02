import pytest
import asyncio
import websockets
import json
from server import start_server, handler, connected_clients, broadcast

@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

@pytest.mark.asyncio
async def test_handler_join_and_message():
    # Start server in background
    server = await websockets.serve(handler, "localhost", 8765)
    async with websockets.connect("ws://localhost:8765") as ws:
        # Wait for join message
        join_msg = await ws.recv()
        data = json.loads(join_msg)
        assert data["type"] == "join"
        # Send a message
        await ws.send(json.dumps({"type": "message", "message": "Hello", "user": "TestUser"}))
        # Receive echo (broadcast)
        echo_msg = await ws.recv()
        echo_data = json.loads(echo_msg)
        assert echo_data["type"] == "message"
        assert echo_data["message"] == "Hello"
        assert echo_data["user"] == "TestUser"
    # Cleanup
    server.close()
    await server.wait_closed()

@pytest.mark.asyncio
async def test_broadcast_excludes_sender():
    connected_clients.clear()
    async with websockets.serve(handler, "localhost", 8766):
        async with websockets.connect("ws://localhost:8766") as ws1:
            # Wait for join message
            await ws1.recv()
            async with websockets.connect("ws://localhost:8766") as ws2:
                # Each client gets join message for the other
                await ws2.recv()  # join of ws2? Actually ws1 gets ws2's join, ws2 gets ws1? Order matters but we skip test for simplicity
                # Send from ws1
                await ws1.send(json.dumps({"type": "message", "message": "Hi", "user": "User1"}))
                # ws2 should receive it
                msg = await ws2.recv()
                data = json.loads(msg)
                assert data["type"] == "message"
                assert data["message"] == "Hi"
                # ws1 should not receive its own message (broadcast excludes sender)
                # We'll set a short timeout to ensure no message
                with pytest.raises(asyncio.TimeoutError):
                    await asyncio.wait_for(ws1.recv(), timeout=0.5)
