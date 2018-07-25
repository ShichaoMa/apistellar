import typing
import inspect

from inspect import Parameter
from datetime import timedelta
from collections import namedtuple
from urllib.parse import unquote

from toolkit.singleton import Singleton
from toolkit.frozen import FrozenSettings
from toolkit.settings import SettingsLoader

from werkzeug.datastructures import ImmutableMultiDict
from werkzeug.formparser import FormDataParser
from werkzeug.http import parse_options_header
from flask.sessions import SecureCookieSessionInterface

from apistar.server.asgi import ASGIReceive
from apistar.conneg import negotiate_content_type
from apistar import Route, exceptions, http, Component as _Component, codecs

from .session import Session
from .controller import Controller


class Component(_Component, metaclass=Singleton):

    def identity(self, parameter: inspect.Parameter):
        """
        Each component needs a unique identifier string that we use for lookups
        from the `state` dictionary when we run the dependency injection.
        """
        parameter_name = parameter.name.lower()
        annotation_name = str(parameter.annotation)

        # If `resolve_parameter` includes `Parameter` then we use an identifier
        # that is additionally parameterized by the parameter name.
        args = inspect.signature(self.resolve).parameters.values()
        if inspect.Parameter in [arg.annotation for arg in args]:
            return annotation_name + ':' + parameter_name

        # Standard case is to use the class name, lowercased.
        return annotation_name

    def resolve(self, *args, **kwargs) -> object:
        raise NotImplementedError()

    def can_handle_parameter(self, parameter: inspect.Parameter):
        """重写这个方法是为了增加typing.Union类型的判定"""
        return_annotation = inspect.signature(self.resolve).return_annotation
        if return_annotation is inspect.Signature.empty:
            msg = (
                'Component "%s" must include a return annotation on the '
                '`resolve()` method, or override `can_handle_parameter`'
            )
            raise exceptions.ConfigurationError(msg % self.__class__.__name__)
        return type(return_annotation) == typing._Union and \
               parameter.annotation in return_annotation.__args__ or \
               parameter.annotation is return_annotation


class ServiceComponent(Component):
    """
    注入Service
    """
    def resolve(self, route: Route) -> Controller:
        return route.controller


class SettingsComponent(Component):
    """
    注入Settings
    """
    settings_path = None

    def __init__(self):
        self.settings = SettingsLoader().load(self.settings_path or "settings")

    def resolve(self) -> FrozenSettings:
        return self.settings

    @classmethod
    def register_path(cls, settings_path):
        cls.settings_path = settings_path


Cookie = typing.NewType('Cookie', str)


class CookiesComponent(Component):
    def resolve(self, cookie: http.Header) -> typing.Dict[str, Cookie]:
        cookies = dict()
        if cookie:
            for c in cookie.split(";"):
                key, val = c.strip().split("=", 1)
                cookies[key] = Cookie(val)
        return cookies


class CookieComponent(Component):

    def resolve(self,
                parameter: Parameter,
                cookies: typing.Dict[str, Cookie]) -> Cookie:
        return cookies.get(parameter.name.replace('_', '-'))


DummyFlaskApp = namedtuple(
    "DummyFlaskApp",
    "session_cookie_name,secret_key,permanent_session_lifetime, config")


class DummyFlaskAppComponent(Component):

    def __init__(self):
        self.default_config = {
            'SESSION_COOKIE_NAME': 'session',
            'SESSION_COOKIE_DOMAIN': None,
            'SESSION_COOKIE_PATH': '/',
            'SESSION_COOKIE_HTTPONLY': True,
            'SESSION_COOKIE_SECURE': False,
            'SESSION_COOKIE_SAMESITE': None,
            'SESSION_REFRESH_EACH_REQUEST': True,
            'SERVER_NAME': None,
        }

    def resolve(self, settings: FrozenSettings,
                host: http.Header,
                ip_host: http.Host) -> DummyFlaskApp:
                self.default_config["SERVER_NAME"] = host or ip_host
                return DummyFlaskApp(
                    config=settings.get("SESSION_CONFIG", self.default_config),
                    secret_key=settings.get("SECRET_KEY"),
                    permanent_session_lifetime=timedelta(
                        days=settings.get("PERMANENT_SESSION_LIFETIME", 31)),
                    session_cookie_name=settings.get(
                        "SESSION_COOKIE_NAME", "session"))


class SessionComponent(Component):

    def __init__(self):
        self.dummy_request = namedtuple("Request", "cookies")
        self.session_interface = SecureCookieSessionInterface()

    def resolve(self,
                app: DummyFlaskApp,
                cookies: typing.Dict[str, Cookie]) -> Session:
            request = self.dummy_request(cookies=cookies)
            return self.session_interface.open_session(app, request)


class File(object):

    def __init__(self, stream, receive, boundary, name, filename):
        self.receive = receive
        self.filename = filename
        self.name = name
        self.stream = stream
        self.tmpboundary = b"\r\n--" + boundary
        self.last = b"\r\n--" + boundary + b"--\r\n"

    def __aiter__(self):
        return self.iter_content()

    async def iter_content(self):
        body = self.stream.body
        while True:
            index = body.find(self.tmpboundary)
            if index != -1:
                read, self.stream.body = body[:index], body[index:]
                yield read
                break
            else:
                if self.stream.closed:
                    raise RuntimeError("Uncomplete content!")
                read, body = body[:-len(self.tmpboundary)], body[-len(self.tmpboundary):]
                yield read
                message = await self.get_message(self.receive)
                body += message.get('body', b'')
                if not message.get('more_body', False):
                    self.stream.closed = True

    async def read(self, size=10240):
        assert size > 0, (999, "Read size must > 0")
        _size = size
        body = self.stream.body
        while True:
            if len(body) < size + len(self.tmpboundary):
                if not self.stream.closed:
                    message = await self.get_message(self.receive)
                    body += message.get('body', b'')
                    if not message.get('more_body', False):
                        self.stream.closed = True
                    continue
                else:
                    _size = len(body) - len(self.last)
            break
        index = body.find(self.tmpboundary)
        if index != -1:
            _size = index

        read, self.stream.body = body[:_size], body[_size:]
        return read

    @staticmethod
    async def get_message(receive):
        message = await receive()
        if not message['type'] == 'http.request':
            error = "'Unexpected ASGI message type '%s'."
            raise Exception(error % message['type'])

        return message

    @classmethod
    async def from_boundary(cls, stream, receive, boundary):
        tmp_boundary = b"--" + boundary
        end_boundary = b"--" + boundary + b"--"
        while not stream.closed:
            message = await cls.get_message(receive)
            stream.body += message.get('body', b'')
            if b"\r\n\r\n" in stream.body and tmp_boundary in stream.body or \
                    not message.get('more_body', False):
                break

            if not message.get('more_body', False):
                stream.closed = True
            else:
                stream.closed = False

        stream.body, name, filename = cls.parse_headers(
            stream.body, tmp_boundary, end_boundary)
        return cls(stream, receive, boundary, name, filename)

    @staticmethod
    def parse_headers(body, tmp_boundary, end_boundary):
        index = body.find(tmp_boundary)
        if index == body.find(end_boundary):
            raise StopAsyncIteration

        body = body[index + len(tmp_boundary):]
        header_str = body[:body.find(b"\r\n\r\n")]
        body = body[body.find(b"\r\n\r\n") + 4:]
        filename = ""
        name = ''
        for header in header_str.split(b"\r\n"):
            if header.startswith(b"Content-Disposition"):
                for d in header.split(b";"):
                    d = d.strip()
                    if b"=" in d:
                        k, v = d.split(b'=')
                        if k == b'name':
                            name = v.strip(b"\"")
                        elif k == b'filename':
                            filename = v.strip(b"\"")
                        elif k == b"filename*":
                            # 用来处理带编码的文件名，返回unicode
                            enc, lang, fn = v.split(b"'")
                            filename = unquote(fn).decode(enc)
        return body, name, filename


class FileStream(object):

    def __init__(self, receive, boundary):
        self.receive = receive
        self.boundary = boundary
        self.body = b""
        self.closed = False

    def __aiter__(self):
        return self

    async def __anext__(self):
        return await File.from_boundary(self, self.receive, self.boundary)


class FileStreamComponent(Component):
    media_type = 'multipart/form-data'

    async def decode(self, receive, headers):
        try:
            mime_type, mime_options = parse_options_header(
                headers['content-type'])
        except KeyError:
            mime_type, mime_options = '', {}

        boundary = mime_options.get('boundary', "").encode()
        if boundary is None:
            raise ValueError('Missing boundary')

        return FileStream(receive, boundary)

    async def resolve(self,
                      receive: ASGIReceive,
                      headers: http.Headers,
                      content_type: http.Header) -> FileStream:
        try:
            negotiate_content_type([self], content_type)
        except exceptions.NoCodecAvailable:
            raise exceptions.UnsupportedMediaType()

        return await self.decode(receive, headers)
