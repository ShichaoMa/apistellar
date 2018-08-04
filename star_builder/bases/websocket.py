import json
import asyncio
import logging

from abc import ABCMeta
from apistar import http
from functools import partial
from _collections_abc import _check_methods

from ..helper import TypeEncoder


logger = logging.getLogger("websocket")


class WebSocketHandler(metaclass=ABCMeta):
    async def websocket_connect(self, message, path: http.Path):
        logger.debug(f"Websocket of {path} connect. ")
        return ""

    async def websocket_disconnect(self, message, path: http.Path):
        logger.debug(f"Websocket of {path} disconnect. ")

    @classmethod
    def __subclasshook__(cls, C):
        if cls is WebSocketHandler:
            try:
                return _check_methods(
                    C, "websocket_connect", "websocket_disconnect", "websocket_receive")
            except AttributeError:
                return False
        return NotImplemented


class WebSocketApp:

    persist = True
    handler = None
    state = None
    send = None

    reverse_type = {
        "websocket.disconnect": "websocket.close",
        "websocket.receive": "websocket.send",
        "websocket.connect": "websocket.accept"
    }

    def __init__(self, scope, app):
        self.scope = scope
        self.app = app

    async def __call__(self, receive, send):
        state = {
            'scope': self.scope,
            'receive': receive,
            'send': send,
            'exc': None,
            'app': self,
            'path_params': None,
            'route': None
        }
        method = self.scope['method']
        path = self.scope['path']
        self.send = send

        try:
            route, path_params = self.app.router.lookup(path, method)
            state['route'] = route
            state['path_params'] = path_params
            self.state = state
            self.send = send
            self.handler = route.handler
            if issubclass(self.handler, WebSocketHandler):
                self.handler = self.handler()

            while self.persist:
                await self.handle(await receive())
        except Exception as exc:
            self.state["exc"] = exc
            await self.exception_handler(exc)

    async def exception_handler(self, exc: Exception):
        await self.send({"type": "websocket.close", "text": str(exc)})
        raise exc

    async def handle(self, message):
        message_type = message["type"].replace(".", "_")
        if isinstance(self.handler, WebSocketHandler):
            handler = getattr(self.handler, message_type)
        else:
            handler = getattr(WebSocketHandler(), message_type, self.handler)

        wrapped = partial(handler, message)
        if asyncio.iscoroutinefunction(handler):
            wrapped._is_coroutine = asyncio.coroutines._is_coroutine
        if message_type == "websocket_disconnect":
            self.persist = False
        buf = await self.app.injector.run_async([wrapped], self.state)
        message = {"type": self.reverse_type[message["type"]]}

        if isinstance(buf, bytes):
            message["bytes"] = buf
        elif buf is None:
            message["type"] = "websocket.close"
        elif not isinstance(buf, str):
            buf = json.dumps(buf, cls=TypeEncoder)
        if isinstance(buf, str):
            message["text"] = buf

        await self.send(message)
