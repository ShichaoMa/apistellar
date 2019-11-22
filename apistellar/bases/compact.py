import sys
import typing

from abc import ABCMeta


PYTHON_VERSION = sys.version_info[:3]


def get_union_class():
    if PYTHON_VERSION >= (3, 7, 0):
        return typing.Union
    else:
        return typing._Union


class CompactAbcMeta(ABCMeta):
    def __subclasscheck__(self, subclass):
        """
        3.7.3 abc __subclasscheck__ 被抽象到builtin模块中，当subclass为非类时会报错：
        TypeError: issubclass() arg 1 must be a class
        :param subclass:
        :return:
        """
        try:
            return super().__subclasscheck__(subclass)
        except TypeError:
            return False
