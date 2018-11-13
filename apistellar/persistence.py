import inspect
import asyncio

from functools import wraps
from types import FunctionType

from pyaop import Proxy, Return, AOP


def wrapper(obj, prop, prop_name):
    def common(proxy, name, value=None):
        if name == prop_name:
            Return(prop)

    return Proxy(obj, before=[
        AOP.Hook(common, ["__getattribute__", "__setattr__", "__delattr__"]),
        ])


def conn_manager(func):
    """
    返回连接管理下的方法
    :param func:
    :return:
    """

    if getattr(func, "conn_ignore", False):
        return func

    if asyncio.iscoroutinefunction(func):
        @wraps(func)
        async def inner(self_or_cls, *args, **kwargs):
            callargs = get_callargs(func, self_or_cls, *args, **kwargs)
            callargs.pop("cls", None)
            with self_or_cls.get_store(**callargs) as store:
                return await func(wrapper(
                    self_or_cls, store, self_or_cls.conn_name), *args, **kwargs)
    else:
        @wraps(func)
        def inner(self_or_cls, *args, **kwargs):
            callargs = get_callargs(func, self_or_cls, *args, **kwargs)
            callargs.pop("cls", None)
            with self_or_cls.get_store(**callargs) as store:
                return func(wrapper(
                    self_or_cls, store, self_or_cls.conn_name), *args, **kwargs)
    return inner


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
    """
    conn_name = "store"
    store = None

    @classmethod
    def get_store(cls, **callargs):
        return NotImplemented


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


def get_callargs(func, *args, **kwargs):
    """
    找到层层装饰器下最里层的函数的callargs
    :param func:
    :param args:
    :param kwargs:
    :return:
    """
    for closure in func.__closure__ or []:
        if isinstance(closure.cell_contents, FunctionType):
            func = closure.cell_contents
            return get_callargs(func, *args, **kwargs)

    else:
        return inspect.getcallargs(func, *args, **kwargs)
