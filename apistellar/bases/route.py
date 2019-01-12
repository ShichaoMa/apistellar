# -*- coding:utf-8 -*-
"""
@Created on 2019/1/2
@Modify on 2019/1/2
@author cnaafhvk888@gmail.com
"""
import re
import inspect

from apistar.server import core
from apistar.document import Field, Response as _Response
from apistar.codecs import jsonschema
from apistar import Route as _Route, http

from .. import types
from ..bases.entities import CommentAnnotation
validators = types.validators


__all__ = ["route", "get", "post", "delete", "put", "options"]

# mock掉apistar中的types和validators
jsonschema.validators = core.validators = types.validators
jsonschema.types = core.types = types


class Response(_Response):
    def __init__(self, encoding: str, status_code: int=200, schema=None, description=""):
        super(Response, self).__init__(encoding, status_code, schema)
        self.description=description


class Route(_Route):

    def generate_response(self, handler):
        annotation = inspect.signature(handler).return_annotation
        annotation, description = self._parse_comment_annotation(annotation)

        annotation = self.coerce_generics(annotation)

        if not (issubclass(annotation, types.Type) or
                isinstance(annotation, validators.Validator)):
            return None

        return Response(encoding='application/json', status_code=200,
                        schema=annotation, description=description)

    def _parse_comment_annotation(self, annotation):
        if isinstance(annotation, type) and issubclass(annotation,
                                                       CommentAnnotation):
            description = annotation.comment
            annotation = annotation.type
        else:
            description = ""
        return annotation, description

    def generate_fields(self, url, method, handler):
        fields = []
        path_names = [
            item.strip('{}').lstrip('+') for item in re.findall('{[^}]*}', url)
        ]
        parameters = inspect.signature(handler).parameters
        for name, param in parameters.items():
            annotation = param.annotation
            title = name
            annotation, description = self._parse_comment_annotation(annotation)

            if name in path_names:
                schema = {
                    param.empty: None,
                    int: validators.Integer(),
                    float: validators.Number(),
                    str: validators.String()
                }[annotation]
                field = Field(name=name, location='path', schema=schema,
                              title=title, description=description)
                fields.append(field)

            elif annotation in (
            param.empty, int, float, bool, str, http.QueryParam):
                if param.default is param.empty:
                    kwargs = {}
                elif param.default is None:
                    kwargs = {'default': None, 'allow_null': True}
                else:
                    kwargs = {'default': param.default}
                schema = {
                    param.empty: None,
                    int: validators.Integer(**kwargs),
                    float: validators.Number(**kwargs),
                    bool: validators.Boolean(**kwargs),
                    str: validators.String(**kwargs),
                    http.QueryParam: validators.String(**kwargs),
                }[annotation]
                field = Field(name=name, location='query', schema=schema,
                              title=title, description=description)
                fields.append(field)

            elif issubclass(annotation, types.Type):
                if method in ('GET', 'DELETE'):
                    for name, validator in annotation.validator.properties.items():
                        field = Field(name=name, location='query',
                                      schema=validator)
                        fields.append(field)
                else:
                    field = Field(name=name, location='body',
                                  schema=annotation.validator,
                              title=title, description=description)
                    fields.append(field)

        return fields


def route(prefix, name=None):
    """
    route为Controller指定名称和路径前缀
    :param prefix:
    :param name:
    :return:
    """
    def prefix_wrapper(cls):
        cls.prefix = "" if prefix == "/" else prefix
        cls.name = name or cls.__name__.lower()
        return cls

    return prefix_wrapper


def wrapper_method(method_name):
    """
    生成绑定http method的route方法
    @get()
    async def hello():
        return {"message": "hello world"}
    :param method_name: get
    :return:
    """
    def method(url=None, name=None, documented=True, standalone=False):

        def endpoint_wrapper(handler):
            # 重新声明的变量不能是url, 下同，否则声明提前会覆盖闭包的变量
            u = url or "/" + handler.__name__
            if u[0] != "/":
                u = "/" + u
            routes = getattr(handler, "routes", [])
            # 对于一个handler拥有多个方法装饰器的情况
            # 由于apistar不支持一个名字映射多个路由
            # 所以之后的装饰器生成的名字会使用_连接方法名
            if not routes:
                n = name or handler.__name__
            else:
                n = (name or handler.__name__) + "_" + method_name
            route = Route(
                u, method_name.upper(), handler, n, documented, standalone)

            if isinstance(handler, type):
                handler.routes = [route]
            else:
                handler.__dict__.setdefault("routes", []).append(route)

            return handler

        return endpoint_wrapper

    method.__name__ = method_name
    method.__qualname__ = method_name
    return method


get = wrapper_method("get")
post = wrapper_method("post")
delete = wrapper_method("delete")
options = wrapper_method("options")
put = wrapper_method("put")
websocket = get
