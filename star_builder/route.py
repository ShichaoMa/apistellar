# -*- coding:utf-8 -*-
from apistar import Route

__all__ = ["route", "get", "post", "delete", "put", "options"]


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
