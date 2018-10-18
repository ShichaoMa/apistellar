import pytest

from aiohttp import ClientSession
from apistar.http import Response
from apistellar import Controller, get, route


@route("/")
class ExceptionController(Controller):

    @get("/exception")
    def exception():
        1/0

    @get("/exception/response")
    def exception_response():
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
            resp = await  session.get(url)
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
