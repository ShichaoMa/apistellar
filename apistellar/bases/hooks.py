import sys
import json
import typing
import logging
import traceback

from apistar import App, http
from flask.sessions import SecureCookieSessionInterface

from ..helper import HookReturn
from .entities import Session, DummyFlaskApp


class SessionHook(object):

    def __init__(self):
        self.session_interface = SecureCookieSessionInterface()

    def on_response(self,
                    app: DummyFlaskApp,
                    resp: http.Response,
                    session: Session):
        if session is not None:
            self.session_interface.save_session(app, session, resp)


class ErrorHook(object):
    """
    处理异常增加响应码
    """
    errors = {999: "Unknown error"}
    fmt = '[{asctime}] {name} {levelname}: {message}'

    def __init__(self):
        self.logger = logging.getLogger("ErrorHook")
        self.logger.propagate = False
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(10)
        handler.setFormatter(logging.Formatter(self.fmt, style="{"))
        self.logger.addHandler(handler)

    def on_error(self, error: Exception, app: App) -> http.Response:
        """
        Handle error
        """
        args = list()
        if error.args:
            data = error.args[0]
            if not isinstance(data, (tuple, list)):
                if isinstance(data, int):
                    args.append(data)
                    args.append(None)
                else:
                    args.append(999)
                    args.append(data)
            else:
                args.extend(data)
        else:
            args.append(None)

        if not isinstance(args[0], int):
            args.insert(0, 999)

        args.extend([None, None, None])
        code, message, extra, *_ = args
        # apistar不支持在on_request时打断后续执行直接返回response
        # 所以在只能通过raise异常来通过异常参数传递响应。
        if isinstance(message, http.Response):
            return message

        if message is None:
            message = self.errors.get(code, "Not configured error")

        payload = {
            "type": "normal",
            "code": code,
            "errcode": getattr(message, "code", code),
            "message": message,
            "extra": extra,
        }
        detail = "".join(traceback.format_exc())
        if app.debug:
            payload["detail"] = detail
        self.logger.error(
            "Error happened: %s extra: %s trace:\n%s. ", message, extra, detail)
        return http.JSONResponse(payload)

    @classmethod
    def register(cls,
                 errors: typing.Union[typing.List[typing.Tuple[int, str]],
                                      typing.Mapping[int, str]]):
        cls.errors.update(errors)


class AccessLogHook(object):
    fmt = '{host} - - [{asctime}] {method} {path} {protocol}' \
          ' {status} {content_length} {agent}'

    def __init__(self):
        self.logger = logging.getLogger("access")
        self.logger.propagate = False
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(10)
        handler.setFormatter(logging.Formatter(self.fmt, style="{"))
        self.logger.addHandler(handler)

    def on_response(self,
                    host: http.Host,
                    path: http.Path,
                    protocol: http.Scheme,
                    method: http.Method,
                    resp: http.Response,
                    user_agent: http.Header,
                    string: http.QueryString):
        if string:
            path = path + "?" + string
        self.log(host, path, protocol, method, resp.status_code,
                 resp.headers["Content-Length"], user_agent)
        return resp

    on_error = on_response

    def log(self, host, path, protocol, method, status, content_length, agent):
        self.logger.info("", extra={"host": host,
                                    "path": path,
                                    "protocol": protocol,
                                    "method": method,
                                    "status": status,
                                    "content_length": content_length,
                                    "agent": agent})


class Hook(object):
    """
    Hook基类，继承自此基类的hook可以自动发现。
    """
    order = 1


def Return(return_value):
    if isinstance(return_value, str):
        return_value = http.HTMLResponse(return_value)
    elif not isinstance(return_value, http.Response):
        return_value = http.JSONResponse(return_value)
    raise HookReturn(return_value)