# -*- coding:utf-8 -*-
from . import Meta
from ..route import route


@route("", name="全部模块")
class Service(metaclass=Meta):
    """
    所有一级模块业务类都需要继承于Service类
    """
    pass
