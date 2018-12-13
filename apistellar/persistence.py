import sys
import inspect
import asyncio
import warnings

from functools import wraps
from contextlib import _GeneratorContextManager
from types import FunctionType, MethodType

from pyaop import Proxy, Return, AOP


def contextmanager(func):
    @wraps(func)
    def helper(*args, **kwds):
        return _AsyncGeneratorContextManager(func, args, kwds)

    return helper


class _AsyncGeneratorContextManager(_GeneratorContextManager):
    def __enter__(self):
        try:
            # 对于同步的方式驱动异步生成器，则什么也不返回，后续在业务层面警告
            if inspect.isasyncgen(self.gen):
                return
            else:
                return self.gen.send(None)
        except StopIteration:
            raise RuntimeError("generator didn't yield") from None

    def __exit__(self, type, value, traceback):
        if type is None:
            try:
                if inspect.isgenerator(self.gen):
                    self.gen.send(None)
                else:
                    raise StopIteration()
            except StopIteration:
                return False
            else:
                raise RuntimeError("generator didn't stop")
        else:
            if value is None:
                # Need to force instantiation so we can reliably
                # tell if we get the same exception back
                value = type()
            try:
                if inspect.isgenerator(self.gen):
                    self.gen.throw(type, value, traceback)
                else:
                    raise value
            except StopIteration as exc:
                # Suppress StopIteration *unless* it's the same exception that
                # was passed to throw().  This prevents a StopIteration
                # raised inside the "with" statement from being suppressed.
                return exc is not value
            except RuntimeError as exc:
                # Don't re-raise the passed in exception. (issue27122)
                if exc is value:
                    return False
                # Likewise, avoid suppressing if a StopIteration exception
                # was passed to throw() and later wrapped into a RuntimeError
                # (see PEP 479).
                if type is StopIteration and exc.__cause__ is value:
                    return False
                raise
            except:
                # only re-raise if it's *not* the exception that was
                # passed to throw(), because __exit__() must not raise
                # an exception unless __exit__() itself failed.  But throw()
                # has to raise the exception to signal propagation, so this
                # fixes the impedance mismatch between the throw() protocol
                # and the __exit__() protocol.
                #
                if sys.exc_info()[1] is value:
                    return False
                raise
            raise RuntimeError("generator didn't stop after throw()")

    async def __aenter__(self):
        try:
            if inspect.isgenerator(self.gen):
                return self.gen.send(None)
            else:
                return await self.gen.asend(None)
        except (StopAsyncIteration, StopIteration):
            raise RuntimeError("generator didn't yield") from None

    async def __aexit__(self, type, value, traceback):
        if type is None:
            try:
                if inspect.isgenerator(self.gen):
                    self.gen.send(None)
                else:
                    await self.gen.asend(None)
            except (StopAsyncIteration, StopIteration):
                return False
            else:
                raise RuntimeError("generator didn't stop")
        else:
            if value is None:
                value = type()
            try:
                if inspect.isgenerator(self.gen):
                    await self.gen.throw(type, value, traceback)
                else:
                    await self.gen.athrow(type, value, traceback)
            except (StopAsyncIteration, StopIteration) as exc:
                return exc is not value
            except RuntimeError as exc:
                if exc is value:
                    return False
                if issubclass(type, (StopAsyncIteration, StopIteration))\
                        and exc.__cause__ is value:
                    return False
                raise
            except:
                if sys.exc_info()[1] is value:
                    return False
                raise
            raise RuntimeError("generator didn't stop after throw()")


def proxy(obj, prop, prop_name):
    """
    为object对象代理一个属性
    :param obj:
    :param prop: 属性
    :param prop_name: 属性名
    :return:
    """
    assert isinstance(prop_name, str), "prop_name must be string!"

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
            gen = self_or_cls.get_store(self_or_cls, **callargs)
            async with gen as proxy_instance:
                return await func(proxy_instance, *args, **kwargs)
    else:
        @wraps(func)
        def inner(self_or_cls, *args, **kwargs):
            callargs = get_callargs(func, self_or_cls, *args, **kwargs)
            callargs.pop("cls", None)
            gen = self_or_cls.get_store(self_or_cls, **callargs)
            with gen as proxy_instance:
                if proxy_instance is None:
                    warnings.warn("All DriverMixin lose efficacy，because of "
                                  "AsyncDriverMixin used with sync method.")
                    proxy_instance = self_or_cls
                return func(proxy_instance, *args, **kwargs)
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
    DriverMixin实现需要注意以下三点：
    1 所有Mixin都继承于DriverMixin(或其子类)，使用super调用父类的get_store方法，
      get_store需要被contextmanager装饰， contextmanager(非内置)来自于apistellar。
    2 Mixin支持将get_store实现成异步的，但最好是叶子节点类，
      异步Mixin最好不要被其它Mixin继承，除非你可以理清mro顺序。
    3 如果继承了异步Mixin创建业务类，那么其中的同步方法不能被conn_manager装饰。
      若装饰了，也不会有任何Mixin效果，还会收到警告。
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
