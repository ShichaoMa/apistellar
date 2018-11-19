import inspect
import asyncio

from functools import wraps
from contextlib import contextmanager
from types import FunctionType, MethodType

from pyaop import Proxy, Return, AOP


def proxy(obj, prop, prop_name):
    """
    为object对象代理一个属性
    :param obj:
    :param prop: 属性
    :param prop_name: 属性名
    :return:
    """
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
            with self_or_cls.get_store(self_or_cls, **callargs) as self_or_cls:
                return await func(self_or_cls, *args, **kwargs)
    else:
        @wraps(func)
        def inner(self_or_cls, *args, **kwargs):
            callargs = get_callargs(func, self_or_cls, *args, **kwargs)
            callargs.pop("cls", None)
            with self_or_cls.get_store(self_or_cls, **callargs) as self_or_cls:
                return func(self_or_cls, *args, **kwargs)
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


def get_callargs(func, *args, **kwargs):
    """
    找到层层装饰器下最里层的函数的callargs
    :param func:
    :param args:
    :param kwargs:
    :return:
    """
    for closure in func.__closure__ or []:
        if isinstance(closure.cell_contents, (FunctionType, MethodType)):
            func = closure.cell_contents
            return get_callargs(func, *args, **kwargs)

    args = inspect.getcallargs(func, *args, **kwargs)
    spec = inspect.getfullargspec(func)
    if spec.varkw:
        args.update(args.pop(spec.varkw, {}))

    return args
