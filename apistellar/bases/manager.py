import os
import sys

from apistar.server.asgi import ASGI_COMPONENTS
from apistar.server.injector import ASyncInjector
from apistar.server.validation import VALIDATION_COMPONENTS

from apistellar.helper import load_packages, find_children, STATE, INITIAL
from apistellar.bases.components import \
    Component, SettingsComponent, ValidateRequestDataComponent


class Manager(object):

    @staticmethod
    def initialize(path, app_name=None):
        path, app_name = os.path.split(path.rstrip("/"))
        sys.path.insert(0, path)
        load_packages(path, app_name)

    def finalize(self, settings="settings"):
        SettingsComponent.register_path(settings)
        INITIAL["app"] = self.__class__
        self.state = STATE
        self.state["app"] = self
        self.components = find_children(Component)
        self.components.append(ValidateRequestDataComponent())
        self.injector = ASyncInjector(
            list(ASGI_COMPONENTS + VALIDATION_COMPONENTS) + self.components,
            INITIAL)
