import pytest
import websockets

from apistar import http
from apistellar import websocket, Controller, route


class WebsocketController(Controller):

    @websocket("/test/websocket1")
    class Handler(object):
        def __init__(self, send):
            self.send = send
            self.message = ""

        async def websocket_connect(self, message, path: http.Path):
            print(f"Websocket of {path} connect. ")
            return {"success": "ok"}

        async def websocket_disconnect(self, message, path: http.Path):
            print("Got total data: %s" % self.message)
            print(f"Websocket of {path} disconnect. ")

        async def websocket_receive(self, message):
            text = message.get("text")
            self.message += text
            await self.send(f"got piece: {text}")
            return {"success": "ok"}

    @websocket("/test/websocket")
    async def receive(message, path: http.Path):
        _text = message.get("text")
        return {"success": "ok"}


@pytest.mark.asyncio
async def test_websocket(server_port):
    async with websockets.connect(
            f"ws://127.0.0.1:{server_port}/test/websocket") as ws:
            await ws.send("hello,")
            assert await ws.recv() == '{"success": "ok"}'


@pytest.mark.asyncio
async def test_websocket1(server_port):
    async with websockets.connect(
            f"ws://127.0.0.1:{server_port}/test/websocket1") as ws:
        assert await ws.recv() == '{"success": "ok"}'
        await ws.send("hello,")
        assert await ws.recv() == 'got piece: hello,'
        assert await ws.recv() == '{"success": "ok"}'
        await ws.send("world")
        assert await ws.recv() == 'got piece: world'
        assert await ws.recv() == '{"success": "ok"}'


if __name__ == "__main__":
    pytest.main(["test_websocket.py"])
