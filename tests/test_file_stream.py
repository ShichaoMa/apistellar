import os
import pytest
import aiofiles
import requests

from toolkit import readexactly
from aiohttp import ClientSession, FormData
from apistellar.bases.response import FileResponse
from apistellar.bases.entities import File
from apistellar import Controller, FileStream, post, get, route


@route("/upload")
class UploadController(Controller):

    @post("/test/upload")
    async def up(stream: FileStream):
        async for file in stream:
            if file.filename:
                with open("upload_" + file.filename, "wb") as f:
                    async for chuck in file:
                        f.write(chuck)
            else:
                # 没有filename的是其它类型的form参数
                await file.read()
        return {"value": "success"}

    @get("/test/download")
    async def down(filename: str):
        f = await aiofiles.open(filename, "rb")
        return FileResponse(
            f, filename, headers={"Content-Length": os.path.getsize(filename)})


@pytest.fixture(scope="module", params=["conftest.py", "滋养细胞肿瘤.pdf"])
def filename(request):
    return request.param


@pytest.mark.asyncio
async def test_upload(server, filename):
    url = f"http://127.0.0.1:{server.port}/upload/test/upload"
    async with ClientSession(conn_timeout=10, read_timeout=10) as session:
        data = FormData()
        data.add_field(f'test_file', open(filename, "rb"), filename=filename)
        resp = await session.post(url, data=data)
        assert await resp.read() == b'{"value":"success"}'


def test_upload_use_requests(server, filename):
    url = f"http://127.0.0.1:{server.port}/upload/test/upload"
    files = [(filename, open(filename, "rb"))]
    resp = requests.post(url, files=files)
    assert resp.text == '{"value":"success"}'


def test_parse_header_str_with_encoding():
    name, filename, mimetype, content_length = File.parse(
        b'\r\nContent-Disposition: form-data; name="test_file"; '
        b'filename="%E6%BB%8B%E5%85%BB%E7%BB%86%E8%83%9E%E8%82%BF%E7%98%A4.pdf"; '
        b'filename*=utf-8\'\'%E6%BB%8B%E5%85%BB%E7%BB%86%E8%83%9E%E8%82%BF%E7%98%A4.pdf'
        b'\r\nContent-Type: application/pdf\r\nContent-Length: 1292384')
    assert filename == "滋养细胞肿瘤.pdf"
    assert name == "test_file"
    assert mimetype == "application/pdf"
    assert content_length == 1292384


def test_parse_header_str_without_encoding():
    name, filename, mimetype, content_length = File.parse(
        b'\r\nContent-Disposition: form-data; name="test_file"; '
        b'filename="conftest.py"; filename*=utf-8\'\'conftest.py'
        b'\r\nContent-Type: text/x-python\r\nContent-Length: 0')
    assert filename == "conftest.py"
    assert name == "test_file"
    assert mimetype == "text/x-python"
    assert content_length == 0


def test_parse_header_str_without_content_length_and_content_type():
    name, filename, mimetype, content_length = File.parse(
        b'\r\nContent-Disposition: form-data; name="test_file"; '
        b'filename*=utf-8\'\'%E6%BB%8B%E5%85%BB%E7%BB%86%E8%83%9E%E8%82%BF%E7%98%A4.pdf')
    assert filename == "滋养细胞肿瘤.pdf"
    assert name == "test_file"
    assert mimetype is None
    assert content_length == 0


def test_parse_header_str_without_content_length_and_content_type_with_encoding():
    name, filename, mimetype, content_length = File.parse(
        b"\r\nContent-Disposition: form-data; "
        b"name*=utf-8''%E6%BB%8B%E5%85%BB%E7%BB%86%E8%83%9E%E8%82%BF%E7%98%A4.pdf; "
        b"filename*=utf-8''%E6%BB%8B%E5%85%BB%E7%BB%86%E8%83%9E%E8%82%BF%E7%98%A4.pdf")
    assert filename == "滋养细胞肿瘤.pdf"
    assert name == "滋养细胞肿瘤.pdf"
    assert mimetype is None
    assert content_length == 0


@pytest.mark.asyncio
async def test_download(server, filename):
    url = f"http://127.0.0.1:{server.port}/upload/test/download"
    async with ClientSession(conn_timeout=10, read_timeout=10) as session:
        resp = await session.get(url, params={"filename": f"upload_{filename}"})
        chunk = await readexactly(resp.content, 1024000)
        async with aiofiles.open(f"download_{filename}", "wb") as f:
            while chunk:
                await f.write(chunk)
                chunk = await readexactly(resp.content, 1024000)
            assert await f.tell() == os.path.getsize(filename)


if __name__ == "__main__":
    pytest.main(["test_file_stream.py"])
