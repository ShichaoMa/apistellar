import os
import pytest
import aiofiles

from toolkit import readexactly
from aiohttp import ClientSession, FormData
from apistellar import Controller, FileStream, post, get


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
        from apistellar.bases.response import FileResponse
        return FileResponse(
            f, filename, headers={"Content-Length": os.path.getsize(filename)})


@pytest.fixture(scope="module", params=["test_in.py", "滋养细胞肿瘤.pdf"])
def filename(request):
    return request.param


@pytest.mark.asyncio
async def test_upload(server_port, filename):
    url = f"http://127.0.0.1:{server_port}/test/upload"
    async with ClientSession(conn_timeout=10, read_timeout=10) as session:
        data = FormData()
        data.add_field(f'test_file', open(filename, "rb"), filename=filename)
        resp = await session.post(url, data=data)
        assert await resp.read() == b'{"value":"success"}'


@pytest.mark.asyncio
async def test_download(server_port, filename):
    url = f"http://127.0.0.1:{server_port}/test/download"
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
