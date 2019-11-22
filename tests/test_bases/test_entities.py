import os
import asyncio
import pytest
import aiofiles
import requests

from toolkit import readexactly
from aiohttp import ClientSession, FormData
from apistellar.bases.response import FileResponse
from apistellar.bases.entities import File, SettingsMixin, init_settings, coroutinelocal
from apistellar import Controller, FileStream, post, get, route


init_settings("test_data.settings")


class A(SettingsMixin):
    pass


class TestSettingsMixin(object):
    def test_settings_get(self):
        a = A()
        assert a.settings.get("A") == 1

    @pytest.mark.env(A=2)
    def test_settings_overwrite(self):
        a = A()
        assert a.settings.get_int("A") == 2

    def test_settings_mixin_not_have_property(self):
        a = A()
        assert not hasattr(a, "property")


@route("/upload")
class UploadController(Controller):

    def join_test_dir(self, filename):
        return os.path.join(os.path.dirname(
            os.path.abspath(os.getcwd())), "test_data", filename)

    @post("/test/upload")
    async def up(self, stream: FileStream):
        async for file in stream:
            if file.filename:
                with open(self.join_test_dir("upload_" + file.filename), "wb") as f:
                    async for chuck in file:
                        # 迭代的同时，还能使用read方法，并保证文件的完整性。
                        # 这样的用法很恶心，但是的确应该支持。
                        f.write(chuck)
                        f.write(await file.read(1024))
                        assert f.tell() == file.tell()
            else:
                # 没有filename的是其它类型的form参数
                await file.read()
        return {"value": "success"}

    @get("/test/download")
    async def down(self, filename: str):
        f = await aiofiles.open(self.join_test_dir(filename), "rb")
        return FileResponse(
            f, filename, headers={"Content-Length": os.path.getsize(
                self.join_test_dir(filename))})


@pytest.fixture(scope="module", params=["conftest.py", "滋养细胞肿瘤.pdf"])
def filename(request):
    return request.param


class TestFileStream(object):

    @pytest.mark.asyncio
    async def test_upload(self, server, filename, join_root_dir):
        url = f"http://127.0.0.1:{server.port}/upload/test/upload"
        async with ClientSession(conn_timeout=10, read_timeout=10) as session:
            data = FormData()
            data.add_field(f'test_file',
                           open(join_root_dir("test_data", filename), "rb"),
                           filename=filename)
            resp = await session.post(url, data=data)
            assert await resp.read() == b'{"value":"success"}'

    def test_upload_use_requests(self, server, filename, join_root_dir):
        url = f"http://127.0.0.1:{server.port}/upload/test/upload"
        files = [(filename, open(join_root_dir("test_data", filename), "rb"))]
        resp = requests.post(url, files=files)
        assert resp.text == '{"value":"success"}'

    def test_parse_header_str_with_encoding(self):
        name, filename, mimetype, content_length = File.parse(
            b'\r\nContent-Disposition: form-data; name="test_file"; '
            b'filename="%E6%BB%8B%E5%85%BB%E7%BB%86%E8%83%9E%E8%82%BF%E7%98%A4.pdf"; '
            b'filename*=utf-8\'\'%E6%BB%8B%E5%85%BB%E7%BB%86%E8%83%9E%E8%82%BF%E7%98%A4.pdf'
            b'\r\nContent-Type: application/pdf\r\nContent-Length: 1292384')
        assert filename == "滋养细胞肿瘤.pdf"
        assert name == "test_file"
        assert mimetype == "application/pdf"
        assert content_length == 1292384

    def test_parse_header_str_without_encoding(self):
        name, filename, mimetype, content_length = File.parse(
            b'\r\nContent-Disposition: form-data; name="test_file"; '
            b'filename="conftest.py"; filename*=utf-8\'\'conftest.py'
            b'\r\nContent-Type: text/x-python\r\nContent-Length: 0')
        assert filename == "conftest.py"
        assert name == "test_file"
        assert mimetype == "text/x-python"
        assert content_length == 0

    def test_parse_header_str_without_content_length_and_content_type(self):
        name, filename, mimetype, content_length = File.parse(
            b'\r\nContent-Disposition: form-data; name="test_file"; '
            b'filename*=utf-8\'\'%E6%BB%8B%E5%85%BB%E7%BB%86%E8%83%9E%E8%82%BF%E7%98%A4.pdf')
        assert filename == "滋养细胞肿瘤.pdf"
        assert name == "test_file"
        assert mimetype is None
        assert content_length == 0

    def test_parse_header_str_without_content_length_and_content_type_with_encoding(
            self):
        name, filename, mimetype, content_length = File.parse(
            b"\r\nContent-Disposition: form-data; "
            b"name*=utf-8''%E6%BB%8B%E5%85%BB%E7%BB%86%E8%83%9E%E8%82%BF%E7%98%A4.pdf; "
            b"filename*=utf-8''%E6%BB%8B%E5%85%BB%E7%BB%86%E8%83%9E%E8%82%BF%E7%98%A4.pdf")
        assert filename == "滋养细胞肿瘤.pdf"
        assert name == "滋养细胞肿瘤.pdf"
        assert mimetype is None
        assert content_length == 0

    @pytest.mark.asyncio
    async def test_download(self, server, filename, join_root_dir):
        url = f"http://127.0.0.1:{server.port}/upload/test/download"
        async with ClientSession(conn_timeout=10, read_timeout=10) as session:
            resp = await session.get(url,
                                     params={"filename": f"upload_{filename}"})
            chunk = await readexactly(resp.content, 1024000)
            path = join_root_dir("test_data", f"download_{filename}")
            async with aiofiles.open(path, "wb") as f:
                while chunk:
                    await f.write(chunk)
                    chunk = await readexactly(resp.content, 1024000)
                await f.flush()
                assert await f.tell() == os.path.getsize(path)


class TestLocal(object):
    @pytest.mark.asyncio
    async def test_local(self):
        coroutinelocal["a"] = 11
        loop = asyncio.get_event_loop()

        async def fun():
            return coroutinelocal["a"]

        async def bar():
            coroutinelocal["a"] = 33
            return coroutinelocal["a"]

        task2 = loop.create_task(bar())
        await asyncio.gather(task2)
        task1 = loop.create_task(fun())

        await asyncio.gather(task1)
        assert task1.result() == 11
        assert task2.result() == 33

