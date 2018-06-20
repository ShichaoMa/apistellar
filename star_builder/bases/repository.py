from .components import Component
from toolkit.singleton import Singleton


class RepositoryMeta(Singleton):

    def __new__(mcs, class_name, bases, props):
        """
        创建后更改return annotation
        :param class_name:
        :param bases:
        :param props:
        :return:
        """
        cls = super().__new__(mcs, class_name, bases, props)
        if "resolve" in props:
            props["resolve"].__annotations__['return'] = cls
        return cls


class Repository(Component, metaclass=RepositoryMeta):
    # 需要定义一下，不然会找到的父类的resolove。
    def resolve(self, *args, **kwargs):
        raise NotImplementedError()
