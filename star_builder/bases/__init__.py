class ServiceMeta(type):
    """
    元类的主要作用是建立继承树，以便发现所有Service/Component。
    """
    def __new__(mcs, class_name, bases, props):
        props["_instance"] = None
        props["children"] = []

        if len(bases) > 1:
            raise RuntimeError(f"{class_name} unsupprt multi inherit!")

        cls = super().__new__(mcs, class_name, bases, props)
        if not bases or bases[0] in [object]:
            return cls

        bases[0].children.append(cls)
        return cls
