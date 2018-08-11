from toolkit.singleton import Singleton

from .exceptions import Readonly
from .components import Component


class ServiceMeta(Singleton):
    func_def = """
def resolve(self{}):
    {}
    return self
            """

    def __new__(mcs, class_name, bases, props):
        """
        创建后更改return annotation，并对未实现resolve方法的类生成一个resolve方法
        :param class_name:
        :param bases:
        :param props:
        :return:
        """
        if "resolve" not in props:
            inject_props = dict()
            for name, prop in props.items():
                if isinstance(prop, Inject):
                    inject_props[name] = prop

            namespace = dict(__name__='entries_%s_resolve' % class_name)
            args_def = list()
            args_assignment = list()

            for name, prop in inject_props.items():
                type_name = prop.type.__name__
                prop.name = name
                namespace[type_name] = prop.type
                args_def.append(f"{name}: {type_name}")
                args_assignment.append(f"self.__dict__['{name}'] = {name}")

            args_def = ", " + ", ".join(args_def) if args_def else ""
            args_assignment = "\n    ".join(args_assignment) if args_assignment else ""
            func_def = mcs.func_def.format(args_def, args_assignment)
            exec(func_def, namespace)
            props["resolve"] = namespace["resolve"]
        cls = super().__new__(mcs, class_name, bases, props)
        props["resolve"].__annotations__['return'] = cls
        return cls


class Inject(object):

    def __init__(self, type):
        self.type = type
        self.name = self.type.__name__.lower()

    def __set__(self, instance, value):
        raise Readonly(f"Readonly object of {self.type.__name__}.")

    def __get__(self, instance, cls):
        return instance.__dict__[self.name]


class InjectManager(object):

    def __lshift__(self, other):
        return Inject(other)


class Service(Component, metaclass=ServiceMeta):
    # 需要定义一下，不然会找到的父类的resolove。
    def resolve(self, *args, **kwargs):
        raise NotImplementedError()


inject = InjectManager()