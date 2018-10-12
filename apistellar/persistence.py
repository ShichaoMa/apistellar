from functools import wraps


def conn_manager(func):
    @wraps(func)
    def inner(self_or_cls, *args, **kwargs):
        with self_or_cls.get_store(**kwargs) as store:

            if not isinstance(self_or_cls, type):
                cls = self_or_cls.__class__
            else:
                cls = self_or_cls
            # 直接为类属性赋值，考虑可能Type类的子类会重写__setattr__
            cls.store = store

            return func(self_or_cls, *args, **kwargs)
    return inner


class DriverMixin(object):
    """
    配合conn_manager用来控制数据库访问。
    """
    store = None

    @classmethod
    def get_store(cls, **kwargs):
        return NotImplemented
