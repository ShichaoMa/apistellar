import sys
import typing

from abc import ABCMeta


def getUnionClass():
    if sys.version_info[:2] == (3, 7):
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
