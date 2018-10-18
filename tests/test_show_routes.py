import os
import pytest

from apistellar import Controller, route, get, show_routes


@route("/")
class HaveRoutes(Controller):
    @get("/")
    def hello(self):
        pass


@pytest.mark.usefixtures("mock")
@pytest.mark.path(os.path.dirname(__file__))
def test_show_routes_with_include(capsys):
    show_routes()
    captured = capsys.readouterr()
    assert captured.out.count("view:haveroutes:hello                    GET     /                                        test_show_routes:HaveRoutes#hello")