import pytest
import typing
from apistar import http
from aiohttp import ClientSession, FormData
from apistellar import route, post, Controller, FormParam, Cookie, \
    validators, Type, get, FileStream


class ModelTest(Type):
    a = validators.String()
    b = validators.Integer()
    c = validators.String(default="test")


@route("/component")
class ComponentsTestController(Controller):

    @post()
    def args_test(self, query_arg: http.QueryParam,
                  referer: http.Header,
                  form_arg: FormParam,
                  session: Cookie,
                  cookies: typing.Dict[str, Cookie]):
        return {"query_arg": query_arg,
                "referer": referer,
                "form_arg": form_arg,
                "session": session,
                "cookies": cookies}

    @post()
    def form_model(self, model: ModelTest):
        model.format(allow_coerce=True)
        return model

    @post()
    def form_model_default_none(self, model: ModelTest = None):
        return model

    @post()
    def form_model_default_dict(self, model: ModelTest = {"a": "14", "b": 2}):
        model.format()
        return model

    @get()
    def query_model(self, model: ModelTest):
        model.format(allow_coerce=True)
        return model

    @get()
    def query_model_default_none(self, model: ModelTest=None):
        return model

    @get()
    def query_model_default_dict(self, model: ModelTest={"a": "14", "b": 2}):
        model.format()
        return model

    @get()
    def no_component(self, abc: object):
        print(11111111111111111, abc)

    @post()
    async def file_stream(self, stream: FileStream):
        buffer = b""
        async for file in stream:
            async for chunk in file:
                buffer += chunk
        return {"data": buffer}


@pytest.mark.asyncio
class TestComponent(object):

    async def test_args(self, server):
        url = f"http://127.0.0.1:{server.port}/component/args_test?" \
            f"query_arg=test_query"
        async with ClientSession(conn_timeout=10, read_timeout=10,
                                 cookies={"session": "111", "uid": "222"},
                                 headers={"referer": 'http://www.baidu.com/'}) as session:
            data = FormData()
            data.add_field("form_arg", "test_form")
            resp = await session.post(url, data=data)
            assert await resp.json() == {"query_arg": "test_query",
                "referer": 'http://www.baidu.com/',
                "form_arg": "test_form",
                "session": "111",
                "cookies": {"session": "111", "uid": "222"}}

    async def test_validate_model_form(self, server):
        url = f"http://127.0.0.1:{server.port}/component/form_model"
        async with ClientSession(conn_timeout=10, read_timeout=10) as session:
            data = FormData()
            data.add_field("a", "11")
            data.add_field("b", 2)
            resp = await session.post(url, data=data)
            assert await resp.json() == {"a": "11", "b": 2, "c": "test"}

    async def test_validate_model_form_without_form(self, server):
        url = f"http://127.0.0.1:{server.port}/component/form_model"
        async with ClientSession(conn_timeout=10, read_timeout=10) as session:
            resp = await session.post(url)
            assert (await resp.json())["message"] == 'model cannot be empty!'

    async def test_validate_model_form_with_default_none(self, server):
        url = f"http://127.0.0.1:{server.port}/component/form_model_default_none"
        async with ClientSession(conn_timeout=10, read_timeout=10) as session:
            resp = await session.post(url)
            assert await resp.json() is None

    async def test_validate_model_form_with_default_dict(self, server):
        url = f"http://127.0.0.1:{server.port}/component/form_model_default_dict"
        async with ClientSession(conn_timeout=10, read_timeout=10) as session:
            resp = await session.post(url)
            assert await resp.json() == {"a": "14", "b": 2, "c": "test"}

    async def test_validate_model_query(self, server):
        url = f"http://127.0.0.1:{server.port}/component/query_model?a=11&b=2"
        async with ClientSession(conn_timeout=10, read_timeout=10) as session:
            resp = await session.get(url)
            assert await resp.json() == {"a": "11", "b": 2, "c": "test"}

    async def test_validate_model_query_without_query(self, server):
        url = f"http://127.0.0.1:{server.port}/component/query_model"
        async with ClientSession(conn_timeout=10, read_timeout=10) as session:
            resp = await session.get(url)
            assert (await resp.json())["message"] == 'model cannot be empty!'

    async def test_validate_model_query_with_default_none(self, server):
        url = f"http://127.0.0.1:{server.port}/component/query_model_default_none"
        async with ClientSession(conn_timeout=10, read_timeout=10) as session:
            resp = await session.get(url)
            assert await resp.json() is None

    async def test_validate_model_query_with_default_dict(self, server):
        url = f"http://127.0.0.1:{server.port}/component/query_model_default_dict"
        async with ClientSession(conn_timeout=10, read_timeout=10) as session:
            resp = await session.get(url)
            assert await resp.json() == {"a": "14", "b": 2, "c": "test"}

    async def test_no_component(self, server):
        url = f"http://127.0.0.1:{server.port}/component/no_component"
        async with ClientSession(conn_timeout=10, read_timeout=10) as session:
            resp = await session.get(url)
            assert (await resp.json())["message"] == \
                   'No component able to handle parameter "abc"' \
                   ' on function "no_component".'

    async def test_file_stream_component_with_wrong_content_type(self, server):
        url = f"http://127.0.0.1:{server.port}/component/file_stream"
        async with ClientSession(conn_timeout=10, read_timeout=10) as session:
            data = FormData()
            # 无法使用filestream
            data.add_field("abc", "aa")
            resp = await session.post(url, data=data)
            assert (await resp.json())["message"] == \
                   'Unsupported Content-Type header in request'

    async def test_file_stream_component_without_boundary(self, server, join_root_dir):
        url = f"http://127.0.0.1:{server.port}/component/file_stream"
        async with ClientSession(conn_timeout=10, read_timeout=10) as session:
            data = FormData()
            data.add_field("abc", open(join_root_dir("test_data/settings.py")))
            # 手头增加了Content-Type，会覆盖掉boundary
            resp = await session.post(url, data=data, headers={
                "Content-Type": "multipart/form-data"})
            assert (await resp.json())["message"] == 'Missing boundary'

