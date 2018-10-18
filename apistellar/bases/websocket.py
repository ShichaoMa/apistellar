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
    """
    每个websocket链接都是独立实例
    """
    persist = True
    handler = None
    state = None
    _send = None

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
        self._send = send
        try:
            route, path_params = self.app.router.lookup(path, method)
            state['route'] = route
            state['path_params'] = path_params
            self.state = state
            self.handler = route.handler

            if issubclass(self.handler, WebSocketHandler):
                self.handler = self.handler(self.send)
            # websocket建立之后持续处理收到的消息
            while self.persist:
                await self.handle(await receive())
        except Exception as exc:
            state["exc"] = exc
            await self.exception_handler(exc)

    async def exception_handler(self, exc: Exception):
        await self.send(str(exc), "websocket.close")
        raise exc

    async def send(self, buf, type="websocket.send"):
        message = {"type": type}

        if isinstance(buf, bytes):
            message["bytes"] = buf
        elif buf is None:
            message["type"] = "websocket.close"
        elif not isinstance(buf, str):
            buf = json.dumps(buf, cls=TypeEncoder)

        if isinstance(buf, str):
            message["text"] = buf
        await self._send(message)

    async def handle(self, message):
        """
        消息处理方法
        :param message:
        :return:
        """
        message_type = message["type"].replace(".", "_")
        # 如果handler是WebSocketHandler的子类实例或者duck type实例，
        # 则从中获取信息类型的处理方法。
        if isinstance(self.handler, WebSocketHandler):
            handler = getattr(self.handler, message_type)
        # 否则从WebSocketHandler获取处理方法，
        # WebSocketHandler未定义websocket.receive的处理器，
        # 因此直接使用handler来处理。
        else:
            handler = getattr(WebSocketHandler(), message_type, self.handler)

        wrapped = partial(handler, message)
        if asyncio.iscoroutinefunction(handler):
            wrapped._is_coroutine = asyncio.coroutines._is_coroutine
        if message_type == "websocket_disconnect":
            self.persist = False
        buf = await self.app.injector.run_async([wrapped], self.state)
        await self.send(buf, self.reverse_type[message["type"]])
