import os
import sys

from apistar.server.asgi import ASGI_COMPONENTS
from apistar.server.injector import ASyncInjector
from apistar.server.validation import VALIDATION_COMPONENTS

from apistellar.bases.entities import init_settings
from apistellar.helper import load_packages, find_children, STATE, INITIAL
from apistellar.bases.components import Component, ValidateRequestDataComponent


class Manager(object):

    @staticmethod
    def initialize(path, app_name=None):
        # 这一步是为了将settings.py所以目录加入可搜索路径
        sys.path.insert(0, path)
        path, app_name = os.path.split(path.rstrip("/"))
        sys.path.insert(0, path)
        load_packages(path, app_name)

    def finalize(self, settings_path="settings"):
        init_settings(settings_path)

        INITIAL["app"] = self.__class__
        self.state = STATE
        self.state["app"] = self
        self.components = find_children(Component)
        self.components.append(ValidateRequestDataComponent())
        self.injector = ASyncInjector(
            list(ASGI_COMPONENTS + VALIDATION_COMPONENTS) + self.components,
            INITIAL)
