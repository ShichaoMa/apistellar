import os
import typing
import inspect

from inspect import Parameter
from datetime import timedelta
from collections import namedtuple

from toolkit.singleton import Singleton
from toolkit.frozen import FrozenSettings

from werkzeug.http import parse_options_header
from werkzeug.datastructures import ImmutableMultiDict
from flask.sessions import SecureCookieSessionInterface

from apistar.server.asgi import ASGIReceive
from apistar.conneg import negotiate_content_type
from apistar.server.asgi import ASGI_COMPONENTS
from apistar.server.validation import RequestDataComponent
from apistar import Route, exceptions, http, Component as _Component

from apistellar.types import Type

from .controller import Controller
from .entities import Session, Cookie, FormParam, FileStream, DummyFlaskApp, \
    SettingsMixin, MultiPartForm, UrlEncodeForm


class Component(_Component):

    def identity(self, parameter: inspect.Parameter):
        """
        修复annotation_name重名的Bug
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


class ServiceComponent(Component, metaclass=Singleton):
    """
    注入Service
    """
    def resolve(self, route: Route) -> Controller:
        return route.controller


class SettingsComponent(Component, SettingsMixin):
    """
    注入Settings
    """
    def resolve(self) -> FrozenSettings:
        return self.settings


class CookiesComponent(Component):
    def resolve(self, cookie: http.Header = None) -> typing.Dict[str, Cookie]:
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
        name = parameter.name.replace('_', '-')
        assert name in cookies or parameter.default != inspect._empty, \
            f"Cookie: {name} not found!"
        return Cookie(cookies.get(name, parameter.default))


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
        self.default_key = os.urandom(24)

    def resolve(self, settings: FrozenSettings,
        host: http.Header,
        ip_host: http.Host) -> DummyFlaskApp:
        config = self.default_config.copy()
        config["SERVER_NAME"] = host or ip_host
        return DummyFlaskApp(
            config=settings.get("SESSION_CONFIG", config),
            secret_key=settings.get("SECRET_KEY", self.default_key),
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
        session = self.session_interface.open_session(app, request)
        return session


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


class FormParamComponent(Component):

    def resolve(self, parameter: inspect.Parameter,
                form: UrlEncodeForm) -> FormParam:
        name = parameter.name
        assert name in (form or {}) or parameter.default != inspect._empty, \
            f"Form Param: {name} not found!"
        return FormParam(form.get(name, parameter.default))


class ValidateRequestDataComponent(_Component):
    """
    当不存在可以处理model的factory时，使用这个类来接管，将request data生成model对象
    """
    def identity(self, parameter: inspect.Parameter):
        """
        修复annotation_name重名的Bug
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

    def can_handle_parameter(self, parameter: inspect.Parameter):
        return issubclass(parameter.annotation, Type)

    def resolve(self,
                route: Route,
                data: http.RequestData):
        body_field = route.link.get_body_field()
        if not body_field or not body_field.schema:
            return data

        if isinstance(data, ImmutableMultiDict):
            data = self._change_to_dict(data)
        validator = body_field.schema
        return validator.model(data)

    @staticmethod
    def _change_to_dict(data):
        """
        由于form表单使用`werkzeug.datastructures.ImmutableMultiDict`来保存form中的
        key-val, 当key只对应一个val时，我们希望得到key-val1这种形式，如果key对应多个val
        我们希望得到key-[val1, val2...]这种形式。
        :param data:
        :return:
        """
        return {k: v if len(v) > 1 else v[0] or None for k, v in dict(data).items()}


class MultiPartComponent(RequestDataComponent, Component):

    def can_handle_parameter(self, parameter: inspect.Parameter):
        return parameter.annotation is MultiPartForm


class UrlEncodeComponent(RequestDataComponent, Component):

    def can_handle_parameter(self, parameter: inspect.Parameter):
        return parameter.annotation is UrlEncodeForm


class HeaderComponent(_Component):
    def resolve(self,
                parameter: Parameter,
                headers: http.Headers) -> http.Header:
        name = parameter.name.replace('_', '-')
        assert name in headers or parameter.default != inspect._empty, \
            f"Header: {name} not found!"
        return http.Header(headers.get(name, parameter.default))


class QueryParamComponent(_Component):
    def resolve(self,
                parameter: Parameter,
                query_params: http.QueryParams) -> http.QueryParam:
        name = parameter.name
        assert name in query_params or parameter.default != inspect._empty, \
            f"Query Param: {name} not found!"
        return http.QueryParam(query_params.get(name, parameter.default))


# apistar自带的component会在找不query param或header的时候，返回None。
# 现在改成如果有默认值存在，使用默认值，否则报错。
ASGI_COMPONENTS[8].resolve = QueryParamComponent().resolve
ASGI_COMPONENTS[10].resolve = HeaderComponent().resolve
