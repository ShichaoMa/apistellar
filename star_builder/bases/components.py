import typing
import inspect

from inspect import Parameter
from datetime import timedelta
from collections import namedtuple
from toolkit.singleton import Singleton
from toolkit.frozen import FrozenSettings
from toolkit.settings import SettingsLoader
from apistar import Route, exceptions, http, Component as _Component

from .service import Service


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
    def resolve(self, route: Route) -> Service:
        return route.service


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

    def resolve(self, settings: FrozenSettings, host: http.Host) -> DummyFlaskApp:
                self.default_config["SERVER_NAME"] = host
                return DummyFlaskApp(
                    config=settings.get("SESSION_CONFIG", self.default_config),
                    secret_key=settings.get("SECRET_KEY"),
                    permanent_session_lifetime=timedelta(
                        days=settings.get("PERMANENT_SESSION_LIFETIME", 31)),
                    session_cookie_name=settings.get(
                        "SESSION_COOKIE_NAME", "session"))