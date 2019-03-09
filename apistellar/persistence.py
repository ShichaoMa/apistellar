import os
import asyncio
import warnings

from functools import wraps
from types import FunctionType
from collections import MutableSequence, MutableSet

from toolkit.async_context import contextmanager
from apistellar.helper import proxy, get_callargs


class ConnectionManager(object):
    proxy_driver_names = None

    @staticmethod
    def debug_callback():
        return os.getenv("UNIT_TEST_MODE", "").lower() == "true"

    def __init__(self, debug_callback=None, proxy_driver_names: tuple=None):
        if debug_callback:
            self.debug_callback = debug_callback
        if proxy_driver_names is not None:
            assert isinstance(proxy_driver_names,
                              (tuple, MutableSequence, MutableSet)), \
                "proxy_driver_names TypeError, " \
                "tuple, MutableSequence, MutableSet need!"
            self.proxy_driver_names = proxy_driver_names

    @staticmethod
    def get_generator(func, self_or_cls, need_proxy, *args, **kwargs):
        callargs = get_callargs(func, self_or_cls, *args, **kwargs)
        callargs.pop("cls", None)
        # 将need_proxy代理到self_or_cls中
        self_or_cls = proxy(self_or_cls, need_proxy, "_need_proxy")
        return self_or_cls, self_or_cls.get_store(self_or_cls, **callargs)

    def __call__(self, *args, debug_callback=None,
                 proxy_driver_names=None, asyncable=False):
        """
        返回连接管理下的方法
        :param func:
        :param proxy_driver_names: 可以被代理的驱动名称
        :param asyncable: 有些方法可能是同步的，但是通过返回future来变成异步的
        :return:
        """
        if debug_callback or proxy_driver_names:
            return self.__class__(debug_callback, proxy_driver_names)

        func = args[0]

        def need_proxy(driver_name):
            """
            DriverMixin的子类在实现get_store时，
            可以调用need_proxy来决定是否为实例添加一个driver， 如：
            ```
            with super().get_store(self_or_cls, **callargs) as self_or_cls:
                if self_or_cls._need_proxy("store"):
                    self_or_cls = proxy(self_or_cls, prop_name="store", prop=...)
                try:
                    yield self_or_cls
                finally:
                    conn.commit()

            ```
            :param driver_name: 添加的driver在实例中的属性名字。
            :return:
            """
            if self.proxy_driver_names is None:
                return True
            return driver_name in self.proxy_driver_names

        if getattr(func, "conn_ignore", False):
            return func

        if asyncable or asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def inner(self_or_cls, *args, **kwargs):
                if self.debug_callback():
                    return await func(self_or_cls, *args, **kwargs)

                self_or_cls, gen = self.get_generator(
                    func, self_or_cls, need_proxy, *args, **kwargs)

                async with gen as proxy_instance:
                    return await func(proxy_instance, *args, **kwargs)
        else:
            @wraps(func)
            def inner(self_or_cls, *args, **kwargs):
                if self.debug_callback():
                    return func(self_or_cls, *args, **kwargs)

                self_or_cls, gen = self.get_generator(
                    func, self_or_cls, need_proxy, *args, **kwargs)

                with gen as proxy_instance:
                    return func(proxy_instance, *args, **kwargs)
        return inner


conn_manager = ConnectionManager()


def conn_ignore(func):
    """
    使用了持久化元类时，使方法忽略使用连接管理，该装饰器必须紧靠方法
    :param func:
    :return:
    """
    func.conn_ignore = True
    return func


class DriverMixin(object):
    """
    配合conn_manager用来控制数据库访问。
    DriverMixin实现需要注意以下三点：
    1 所有Mixin都继承于DriverMixin(或其子类)，使用super调用父类的get_store方法，
    2 get_store需要被contextmanager装饰，contextmanager(非内置)来自于toolkit.async_context。
    3 Mixin支持将get_store实现成异步的。
    """

    @classmethod
    @contextmanager
    def get_store(cls, self_or_cls, **callargs):
        """
        子类需要通过super调用父类的get_store方法
        :param self_or_cls: 调用类方法和实例方法时的cls或self
        :param callargs: 方法调用时参数表
        :return: 返回proxy对象
        """
        yield self_or_cls


class PersistentMeta(type):
    """
    为实例方法和类方法增加conn_manager装饰器
    """
    def __new__(mcs, name, bases, attrs):
        for attr_name in attrs.keys():
            func = attrs[attr_name]
            # 去掉魔术方法和私有方法
            if isinstance(func, FunctionType) and not func.__name__.startswith(
                    "__"):
                attrs[attr_name] = conn_manager(func)
            if isinstance(func, classmethod):
                func = func.__func__
                if not func.__name__.startswith("__"):
                    attrs[attr_name] = classmethod(conn_manager(func))

        return super(PersistentMeta, mcs).__new__(mcs, name, bases, attrs)
