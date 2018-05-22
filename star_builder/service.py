# -*- coding:utf-8 -*-
from apistar import Component, Route
from .route import route


class ServiceMeta(type):
    """
    元类的主要作用是建立Service继承树，以便发现所有Service。
    """
    def __new__(mcs, class_name, bases, props):
        cls = super(ServiceMeta, mcs).__new__(mcs, class_name, bases, props)
        cls.children = []

        if len(bases) > 1:
            raise RuntimeError("Service class unsupprt multi inherit!")

        if not bases or bases[0] == object:
            return cls

        bases[0].children.append(cls)
        return cls


@route("", name="全部模块")
class Service(metaclass=ServiceMeta):
    """
    所有一级模块业务类都需要继承于Service类
    """
    pass


class ServiceComponent(Component):
    """
    依赖注入Service组件
    """
    def resolve(self, route: Route) -> Service:
        return route.service

