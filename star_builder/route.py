# -*- coding:utf-8 -*-
from apistar import Route


__all__ = ["route", "get", "post", "delete", "put", "options"]


def route(prefix, name=None):
    """
    route为service指定名称和路径前缀
    :param prefix:
    :param name:
    :return:
    """
    def prefix_wrapper(cls):
        cls.prefix = prefix
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
    def method(url=None, name=None, documented=True, standalone=False, link=None):

        def endpoint_wrapper(handler):
            handler.route = Route(
                url or "/" + handler.__name__, method_name.upper(), handler, name,
                documented, standalone, link)
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
