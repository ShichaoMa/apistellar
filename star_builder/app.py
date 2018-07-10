import os
import sys
import logging
import traceback

from apistar import ASyncApp, App, exceptions
from apistar.http import Response, JSONResponse
from apistar.server.components import ReturnValue

from .bases.controller import Controller
from .bases.components import SettingsComponent
from .bases.hooks import ErrorHook, AccessLogHook, SessionHook, Hook
from .helper import load_packages, routing, print_routing, TypeEncoder, \
    find_children, enhance_response

__all__ = ["Application"]
enhance_response(Response)
JSONResponse.options["default"] = TypeEncoder().default


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


class FixedApp(App):

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


def application(app_name, template_dir=None,
                static_dir=None,
                packages=None,
                schema_url='/schema/',
                docs_url='/docs/',
                static_url='/static/',
                settings_path="settings",
                debug=True,
                async=True,
                current_dir="."):
    """
       参数指定选择使用异步app还是同步app
       可以动态发现当前项目根目录下所有controller中的handler
    """
    logger = logging.getLogger(app_name)
    os.chdir(current_dir)
    sys.path.insert(0, current_dir)
    sys.modules.pop(app_name, None)
    load_packages(".")
    include = routing(Controller)
    SettingsComponent.register_path(settings_path)

    if include:
        routes = [include]
        print_routing(routes, write=logger.debug)
    else:
        logger.info("Noting to route. ")
        routes = []
    custom_hooks = sorted(find_children(Hook), key=lambda x: x.order)
    hooks = [AccessLogHook(), SessionHook(), ErrorHook()] + custom_hooks
    app = (FixedAsyncApp if async else FixedApp)(
        routes,
        template_dir=template_dir,
        static_dir=static_dir,
        packages=packages,
        schema_url=schema_url,
        docs_url=docs_url,
        static_url=static_url,
        components=find_children(),
        event_hooks=hooks)

    app.debug = debug
    return app


Application = application


def show_routes():
    sys.path.insert(0, ".")
    formatter = "{:<40} {:<7} {:<40} {:<}"

    def show_format(method, parttern, name, ca_name):
        return formatter.format(name, method, parttern, ca_name)

    load_packages(".")
    include = routing(Controller)
    if include:
        print(formatter.format(
            "Name", "Method", "URI Pattern", "Controller#Action"))
        print_routing([include], format=show_format)
    else:
        print("Noting to route. ")
