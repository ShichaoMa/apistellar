import sys
import pytest

from apistar.server.asgi import ASGI_COMPONENTS
from apistar.server.injector import ASyncInjector
from apistar.server.validation import VALIDATION_COMPONENTS
from apistellar.bases.manager import Manager
from apistellar.bases.components import ComposeTypeComponent
from apistellar.helper import STATE


class TestManager(object):

    @pytest.mark.prop("apistellar.bases.manager.load_package")
    def test_initialize(self):
        manager = Manager()
        manager.initialize("/tmp")
        assert "/tmp" in sys.path
        assert "/" in sys.path

    @pytest.mark.prop("apistellar.bases.manager.find_children", ret_val=[])
    def test_finalize(self):
        manager = Manager()
        manager.finalize()
        assert STATE["app"] == manager
        assert isinstance(manager.components[-1], ComposeTypeComponent)
        assert isinstance(manager.injector, ASyncInjector)
        components = []
        components.extend(ASGI_COMPONENTS)
        components.extend(VALIDATION_COMPONENTS)
        components.extend(manager.components)
        assert manager.injector.components == components