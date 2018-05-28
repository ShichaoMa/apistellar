import inspect

from toolkit.frozen import FrozenSettings
from toolkit.settings import SettingsLoader
from apistar import Route, Component as _Component

from . import ComponentMeta
from .service import Service


class Component(_Component, metaclass=ComponentMeta):
    order = 1000

    def resolve(self, *args, **kwargs):
        raise NotImplementedError()


class ServiceComponent(Component):
    """
    注入Service
    """
    order = 1

    def resolve(self, route: Route) -> Service:
        return route.service


class SettingsComponent(Component):
    """
    注入Settings
    """
    settings_path = None
    order = 0

    def __init__(self):
        self.settings = SettingsLoader().load(self.settings_path or "settings")

    def resolve(self) -> FrozenSettings:
        return self.settings

    @classmethod
    def register_path(cls, settings_path):
        cls.settings_path = settings_path
