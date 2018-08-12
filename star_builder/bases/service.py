from .metas import ServiceMeta
from .components import Component


class Service(Component, metaclass=ServiceMeta):

    def resolve(self, *args, **kwargs):
        return self.__class__()
