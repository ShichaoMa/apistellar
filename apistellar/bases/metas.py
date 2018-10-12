import inspect

from .entities import InheritType, Inject


class InjectMeta(type):

    @classmethod
    def extract(mcs, method, inject_props):
        names = list()
        params = inspect.signature(method).parameters
        for name, param in params.items():
            if name == "self":
                continue
            # 仅处理位置参数或关键字参数
            if param.kind != inspect._POSITIONAL_OR_KEYWORD:
                continue
            ret = mcs.check_duplicate(inject_props, param)
            if ret != InheritType.DUPLICATE:
                if param.default == inspect._empty:
                    default = None
                else:
                    default = param.default
                prop = Inject(param.annotation, default)
                if ret == InheritType.OVERWRITE:
                    name = f"qwertrewq_{name}"
                mcs.add_prop(inject_props, prop, name)
            names.append(name)
        return ", ".join("%s=%s" % (
            name.replace("qwertrewq_", ""), name) for name in names)

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

    @staticmethod
    def enrich_args_def(props, namespace, args_def):
        for name, prop, default in props:
            type_name = prop.type.__name__
            prop.name = name
            namespace[type_name] = prop.type
            args_def.append(f"{name}: {type_name}" +
                            ("" if default is None else f"={repr(default)}"))


class ServiceMeta(InjectMeta):
    func_def = """
def resolve(self{}):
    {}
    {}
    return instance
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
            args_def, args_assignment = list(), list()

            for name, prop, default in inject_props:
                args_assignment.append(f"instance.__dict__['{name}'] = {name}")
            name_str = ""
            # 处理继承情况
            if hasattr(bases[0], "resolve"):
                name_str = mcs.extract(getattr(bases[0], "resolve"), inject_props)
            super_str = f"instance = super({class_name}, self).resolve({name_str})"

            mcs.enrich_args_def(inject_props, namespace, args_def)
            args_def = ", " + ", ".join(args_def) if args_def else ""
            args_assignment = "\n    ".join(
                args_assignment) if args_assignment else ""
            func_def = mcs.func_def.format(args_def, super_str,
                                           args_assignment)
            exec(func_def, namespace)
            props["resolve"] = namespace["resolve"]
        cls = super().__new__(mcs, class_name, bases, props)
        props["resolve"].__annotations__['return'] = cls
        props["resolve"].__globals__[class_name] = cls
        return cls


class ModelFactoryMeta(InjectMeta):
    func_def = """
async def resolve(self{}):
    {}
    {}
    """

    def __new__(mcs, class_name, bases, props):
        """
        创建后更改return annotation，并对未实现resolve方法的类生成一个resolve方法
        :param class_name:
        :param bases:
        :param props:
        :return:
        """
        model_cls = props.get("model")
        #assert model_cls is not None, "ModelFactory need specify a model!"
        assert "resolve" not in props, "Cannot overwrite resolve method!"
        assert "product" in props, "Need to implement product method!"

        product_method = props.get("product")
        return_type = product_method.__annotations__.get("return")
        assert return_type, "product need return type!"
        inject_props, assignment_props = list(), list()
        name_str = mcs.extract(product_method, inject_props)
        return_str = f"return await self.product({name_str})"

        for model_prop_name in dir(model_cls):
            model_prop = getattr(model_cls, model_prop_name)
            if isinstance(model_prop, Inject):
                model_prop.name = model_prop_name
                ret = mcs.check_duplicate(inject_props, model_prop)
                if ret == InheritType.OVERWRITE:
                    name = f"qwertrewq_{name}"
                mcs.add_prop(assignment_props, model_prop, model_prop_name)
                if ret == InheritType.NORMAL:
                    mcs.add_prop(inject_props, model_prop, model_prop_name)

        namespace = dict(__name__='entries_%s_resolve' % class_name)
        args_def, args_assignment = list(), list()

        for name, prop, default in assignment_props:
            args_assignment.append(f"self.model.{name} = {name}")
        mcs.enrich_args_def(inject_props, namespace, args_def)

        args_def = ", " + ", ".join(args_def) if args_def else ""
        args_assignment = "\n    ".join(
            args_assignment) if args_assignment else ""
        func_def = mcs.func_def.format(args_def, args_assignment, return_str)
        exec(func_def, namespace)
        props["resolve"] = namespace["resolve"]
        cls = super().__new__(mcs, class_name, bases, props)
        props["resolve"].__annotations__['return'] = return_type
        props["resolve"].__globals__[class_name] = cls
        return cls
