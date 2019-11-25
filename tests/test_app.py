import os
import pytest

from aiohttp import ClientSession
from apistar.http import Response
from apistellar import Controller, get, route, Application, show_routes


@route("/exception")
class ExceptionController(Controller):

    @get("/")
    def exception(self):
        1/0

    @get("/response")
    def exception_response(self):
        try:
            1/0
        except ZeroDivisionError:
            import sys
            return Response("error", exc_info=sys.exc_info())


@pytest.mark.asyncio
class TestException(object):

    async def test_exception_debug_true(self, server):
        server.app.debug = True
        url = f"http://127.0.0.1:{server.port}/exception"
        async with ClientSession(conn_timeout=10, read_timeout=10) as session:
            resp = await session.get(url)
            data = await resp.json()
            assert data["code"] == 999
            assert data["errcode"] == 999
            assert data["message"] == "division by zero"
            assert "detail" in data

    async def test_exception_debug_false(self, server):
        server.app.debug = False
        url = f"http://127.0.0.1:{server.port}/exception"
        async with ClientSession(conn_timeout=10, read_timeout=10) as session:
            resp = await  session.get(url)
            data = await resp.json()
            assert data["code"] == 999
            assert data["errcode"] == 999
            assert data["message"] == "division by zero"
            assert "detail" not in data

    async def test_not_found_debug_true(self, server):
        server.app.debug = True
        url = f"http://127.0.0.1:{server.port}/not/found"
        async with ClientSession(conn_timeout=10, read_timeout=10) as session:
            resp = await  session.get(url)
            data = await resp.json()
            assert data["code"] == 404
            assert data["errcode"] == 404
            assert data["message"] == "Not found"
            assert "detail" in data

    async def test_not_found_debug_false(self, server):
        server.app.debug = False
        url = f"http://127.0.0.1:{server.port}/not/found"
        async with ClientSession(conn_timeout=10, read_timeout=10) as session:
            resp = await session.get(url)
            data = await resp.json()
            assert data["code"] == 404
            assert data["errcode"] == 404
            assert data["message"] == "Not found"
            assert "detail" not in data

    async def test_exception_response_debug_true(self, server):
        server.app.debug = True
        url = f"http://127.0.0.1:{server.port}/exception/response"
        async with ClientSession(conn_timeout=100, read_timeout=100) as session:
            resp = await session.get(url)
            data = await resp.json()
            assert data["code"] == 999
            assert data["errcode"] == 999
            assert data["message"] == "division by zero"
            assert "detail" in data

    async def test_exception_response_debug_false(self, server):
        server.app.debug = False
        url = f"http://127.0.0.1:{server.port}/exception/response"
        async with ClientSession(conn_timeout=10, read_timeout=10) as session:
            resp = await session.get(url)
            data = await resp.read()
            assert data == b"error"


@pytest.mark.prop("apistellar.app.routing", ret_val=[])
def test_app_no_route():
    Application("test")


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
    assert captured.out.count(
        "view:haveroutes:hello                    GET     /                                        test_app:HaveRoutes#hello")

