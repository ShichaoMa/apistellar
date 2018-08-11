import inspect

from enum import Enum
from toolkit.singleton import Singleton

from .exceptions import Readonly
from .components import Component


class InheritType(Enum):
    DUPLICATE = 0 # 重名且类型相符，在参数列表和赋值中不体现，在super中体现
    OVERWRITE = 1 # 重名但是类型不同，全部位置要体现，但是需要父类的参数改名字
    NORMAL = 2  # 正常的情况


class ServiceMeta(Singleton):
    func_def = """
def resolve(self{}):
    {}
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
            inject_props = list()
            for name, prop in props.items():
                if isinstance(prop, Inject):
                    mcs.add_prop(inject_props, prop, name)

            namespace = dict(__name__='entries_%s_resolve' % class_name)
            args_def = list()
            args_assignment = list()
            super_str = ""

            for name, prop, default in inject_props:
                args_assignment.append(f"self.__dict__['{name}'] = {name}")
            # 处理继承情况
            if hasattr(bases[0], "resolve"):
                names = list()
                params = inspect.signature(getattr(bases[0], "resolve")).parameters
                for name, param in params.items():
                    if name == "self":
                        continue
                    # 仅处理要继承的位置参数
                    if param.kind != inspect._POSITIONAL_OR_KEYWORD:
                        continue
                    ret = mcs.check_duplicate(inject_props, param)
                    if ret != InheritType.DUPLICATE:
                        prop = Inject(param.annotation, None)
                        if ret == InheritType.OVERWRITE:
                            name = f"father_{name}"
                        mcs.add_prop(inject_props, prop, name)
                    names.append(name)
                print(names)
                if names:
                    name_str = ", ".join("%s=%s" % (
                        name.replace("father_", ""), name) for name in names)
                    super_str = f"super({class_name}, self).resolve({name_str})"
                print(super_str)

            for name, prop, default in inject_props:
                type_name = prop.type.__name__
                prop.name = name
                namespace[type_name] = prop.type
                args_def.append(f"{name}: {type_name}" +
                                ("" if default is None else f"={repr(default)}"))

            args_def = ", " + ", ".join(args_def) if args_def else ""
            args_assignment = "\n    ".join(args_assignment) if args_assignment else ""
            func_def = mcs.func_def.format(args_def, super_str, args_assignment)
            print(func_def)
            exec(func_def, namespace)
            props["resolve"] = namespace["resolve"]
        cls = super().__new__(mcs, class_name, bases, props)
        props["resolve"].__annotations__['return'] = cls
        props["resolve"].__globals__[class_name] = cls
        return cls

    @staticmethod
    def check_duplicate(inject_props, param):
        for name, prop, default in inject_props:
            if param.name == name and param.annotation == prop.type:
                return InheritType.DUPLICATE
            elif param.name == name:
                return InheritType.OVERWRITE
        return InheritType.NORMAL

    @staticmethod
    def add_prop(inject_props, prop, name):
        if prop.default is None:
            inject_props.insert(0, (name, prop, prop.default))
        else:
            inject_props.append((name, prop, prop.default))


class Inject(object):

    def __init__(self, type, default):
        self.type = type
        self.name = type.__name__.lower()
        self.default = default

    def __set__(self, instance, value):
        raise Readonly(f"Readonly object of {self.type.__name__}.")

    def __get__(self, instance, cls):
        return instance.__dict__[self.name]


class InjectManager(object):

    def __init__(self, default=None):
        self.default = default

    def __lshift__(self, other):
        return Inject(other, self.default)

    def __call__(self, *, default=None):
        return InjectManager(default)


class Service(Component, metaclass=ServiceMeta):
    # 需要定义一下，不然会找到的父类的resolove。
    def resolve(self, *args, **kwargs):
        raise NotImplementedError()


inject = InjectManager()