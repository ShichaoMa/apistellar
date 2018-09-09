import sys

from apistar.server.asgi import ASGI_COMPONENTS
from apistar.server.injector import ASyncInjector
from apistar.server.validation import VALIDATION_COMPONENTS

from .components import SettingsComponent, Component
from ..helper import load_packages, find_children, STATE, INITIAL


class Manager(object):

    @staticmethod
    def initialize(path, app_name=None):
        sys.path.insert(0, path)
        if app_name:
            sys.modules.pop(app_name, None)
        load_packages(".")

    def finalize(self, settings="settings"):
        SettingsComponent.register_path(settings)
        INITIAL["app"] = self.__class__
        self.state = STATE
        self.state["app"] = self
        self.components = find_children(Component)
        self.injector = ASyncInjector(
            list(ASGI_COMPONENTS + VALIDATION_COMPONENTS) + self.components,
            INITIAL)
