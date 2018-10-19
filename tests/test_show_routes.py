import os
import pytest

from apistellar import Controller, route, get, show_routes


@pytest.mark.prop("apistellar.helper.routing", ret_val=[])
@pytest.mark.path(os.path.dirname(__file__))
def test_show_routes_without_include(capsys):
    show_routes()
    captured = capsys.readouterr()
    assert captured.out.count("Noting to route. ")


@pytest.mark.path(os.path.dirname(__file__))
def test_show_routes_with_include(capsys):
    @route("/")
    class HaveRoutes(Controller):
        @get("/")
        def hello(self):
            pass

    show_routes()
    captured = capsys.readouterr()
    assert captured.out.count("view:haveroutes:hello                    GET     /                                        test_show_routes:HaveRoutes#hello")