# -*- coding:utf-8 -*-
from ..route import route


@route("", name="view")
class Controller(object):
    """
    所有一级模块控制类都需要继承于Controller
    """
    pass
