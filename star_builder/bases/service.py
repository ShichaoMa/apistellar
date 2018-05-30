# -*- coding:utf-8 -*-
from . import ServiceMeta
from ..route import route


@route("", name="全部模块")
class Service(metaclass=ServiceMeta):
    """
    所有一级模块业务类都需要继承于Service类
    """
    pass
