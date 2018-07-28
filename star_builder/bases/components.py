import typing
import inspect

from inspect import Parameter
from datetime import timedelta
from collections import namedtuple

from toolkit.singleton import Singleton
from toolkit.frozen import FrozenSettings
from toolkit.settings import SettingsLoader

from werkzeug.http import parse_options_header
from flask.sessions import SecureCookieSessionInterface

from apistar.server.asgi import ASGIReceive
from apistar.conneg import negotiate_content_type
from apistar import Route, exceptions, http, Component as _Component

from .controller import Controller
from .entities import Session, Cookie, FileStream, DummyFlaskApp


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
