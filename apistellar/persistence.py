import asyncio

from functools import wraps
from contextlib import contextmanager


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
            with process(self_or_cls, kwargs):
                return await func(self_or_cls, *args, **kwargs)
    else:
        @wraps(func)
        def inner(self_or_cls, *args, **kwargs):
            with process(self_or_cls, kwargs):
                return func(self_or_cls, *args, **kwargs)
    return inner


@contextmanager
def process(self_or_cls, kwargs):
    """
    获取持久化对象
    :param self_or_cls:
    :param kwargs:
    :return:
    """
    with self_or_cls.get_store(**kwargs) as store:
        if not isinstance(self_or_cls, type):
            cls = self_or_cls.__class__
        else:
            cls = self_or_cls
        # 直接为类属性赋值，考虑可能Type类的子类会重写__setattr__
        cls.store = store
        yield


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
    store = None

    @classmethod
    def get_store(cls, **kwargs):
        return NotImplemented
