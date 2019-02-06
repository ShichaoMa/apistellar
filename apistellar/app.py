import os
import asyncio
import logging
import traceback

from toolkit import cache_classproperty
from toolkit.settings import Settings, FrozenSettings
from apistar import ASyncApp, exceptions
from apistar.http import Response, JSONResponse
from apistar.server.components import ReturnValue
from apistar.server.asgi import ASGIScope, ASGISend
from apistellar.document import ShowLogPainter, AppLogPainter

from .bases.websocket import WebSocketApp
from .bases.entities import SettingsMixin
from .bases.components import Component, ValidateRequestDataComponent
from .bases.hooks import ErrorHook, AccessLogHook, SessionHook, Hook
from .helper import TypeEncoder, find_children, enhance_response

__all__ = ["Application"]
enhance_response(Response)
# 可以序列化Type子类
JSONResponse.options["default"] = TypeEncoder().default

del JSONResponse.charset

settings = FrozenSettings(Settings())


class FixedAsyncApp(ASyncApp):

    def exception_handler(self, exc: Exception) -> Response:
        if isinstance(exc, exceptions.HTTPException):
            payload = {
                "type": "http",
                "code": exc.status_code,
                "errcode": exc.status_code,
                "message": exc.detail,
            }
            if self.debug:
                payload["detail"] = "".join(traceback.format_exc())
            return JSONResponse(payload, exc.status_code, exc.get_headers())
        raise exc

    def error_handler(self, return_value: ReturnValue) -> Response:
        if isinstance(return_value, Response):
            return return_value
        return super().error_handler()

    async def read(self, response):
        coroutine = response.content.read(1024000)
        if asyncio.iscoroutine(coroutine) or asyncio.isfuture(coroutine):
            return await coroutine
        else:
            return coroutine

    async def finalize_asgi(self,
                            response: Response,
                            send: ASGISend,
                            scope: ASGIScope):
        if response.exc_info is not None:
            if self.debug or scope.get('raise_exceptions', False):
                exc_info = response.exc_info
                raise exc_info[0].with_traceback(exc_info[1], exc_info[2])

        await send({
            'type': 'http.response.start',
            'status': response.status_code,
            'headers': [
                [key.encode(), value.encode()]
                for key, value in response.headers
            ]
        })
        if hasattr(response.content, "read"):
            body = await self.read(response)
            while body:
                await send({
                    'type': 'http.response.body',
                    'body': body,
                    "more_body": True,
                })
                body = await self.read(response)
        else:
            body = response.content
        await send({
            'type': 'http.response.body',
            'body': body
        })

    def __call__(self, scope):
        if scope["type"] != "websocket":
            return super(FixedAsyncApp, self).__call__(scope)
        else:
            return WebSocketApp(scope, self)

    @cache_classproperty
    def settings(cls):  # type: str
        settings = SettingsMixin.settings
        settings._json["PROJECT_PATH"] = os.path.abspath(os.getcwd())
        return settings


def application(app_name,
                template_dir=None,
                static_dir=None,
                packages=None,
                schema_url='/schema/',
                docs_url='/docs/',
                static_url='/static/',
                settings_path="settings",
                debug=True,
                current_dir="."):
    """
       可以动态发现当前项目根目录下所有controller中的handler
    """
    logger = logging.getLogger(app_name)
    os.chdir(current_dir)
    SettingsMixin.register_path(settings_path)
    settings._json.update(FixedAsyncApp.settings._json)

    with AppLogPainter(logger.debug, current_dir).paint() as routes:
        components = find_children(Component)
        # ValidateRequestDataComponent是用来兜底的，所以要放到最后
        components.append(ValidateRequestDataComponent())
        custom_hooks = sorted(find_children(Hook), key=lambda x: x.order)
        hooks = [AccessLogHook(), SessionHook(), ErrorHook()] + custom_hooks
        app = FixedAsyncApp(
            routes,
            template_dir=template_dir,
            static_dir=static_dir,
            packages=packages,
            schema_url=schema_url,
            docs_url=docs_url,
            static_url=static_url,
            components=components,
            event_hooks=hooks)
        app.debug = debug
        return app


Application = application


def show_routes():
    formatter = "{:<40} {:<7} {:<40} {:<}"

    def show_format(method, parttern, name, ca_name):
        return formatter.format(name, method, parttern, ca_name)

    with ShowLogPainter(show_format).paint() as routes:
        if routes:
            print(formatter.format(
                "Name", "Method", "URI Pattern", "Controller#Action"))
