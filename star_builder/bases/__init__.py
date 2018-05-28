from threading import RLock
from apistar import Component


class Meta(type):
    """
    元类的主要作用是建立继承树，以便发现所有Service/Component。
    """
    lock = RLock()

    def __new__(mcs, class_name, bases, props):
        props["_instance"] = None
        props["children"] = []

        if len(bases) > 1:
            raise RuntimeError(f"{class_name} unsupprt multi inherit!")

        cls = super().__new__(mcs, class_name, bases, props)
        if not bases or bases[0] in [object, Component]:
            return cls

        bases[0].children.append(cls)
        return cls


class ComponentMeta(Meta):
    """
    单例，修改resolve return annotation
    """
    def __new__(mcs, class_name, bases, props):
        props["_instance"] = None
        return super().__new__(mcs, class_name, bases, props)

    def __call__(cls, *args, **kwargs):
        with cls.lock:
            cls._instance = cls._instance or super().__call__(*args, **kwargs)
            return cls._instance
