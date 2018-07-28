import re
import typing

from urllib.parse import unquote
from collections import namedtuple
from flask.sessions import SecureCookieSession


Cookie = typing.NewType('Cookie', str)
Session = typing.NewType("Session", SecureCookieSession)
DummyFlaskApp = namedtuple(
    "DummyFlaskApp",
    "session_cookie_name,secret_key,permanent_session_lifetime,config")


class File(object):

    def __init__(self, stream, receive, boundary, name, filename, mimetype):
        self.mimetype = mimetype
        self.receive = receive
        self.filename = filename
        self.name = name
        self.stream = stream
        self.tmpboundary = b"\r\n--" + boundary
        self.boundary_len = len(self.tmpboundary)
        self._last = b""
        self._size = 0
        self.body_iter = self._iter_content()

    def __aiter__(self):
        return self.body_iter

    def __iter__(self):
        yield "name"
        yield "filename"
        yield "mimetype"

    def __getitem__(self, item):
        return getattr(self, item)

    def __str__(self):
        string = f"<{self.__class__.__name__} "
        for k in self:
            v = self[k]
            string += f"{k}={v} "
        return string[:-1] + ">"

    __repr__ = __str__

    def iter_content(self):
        return self.body_iter

    async def _iter_content(self):
        body = self.stream.body
        while True:
            # 如果存在read过程中剩下的，则直接返回
            if self._last:
                yield self._last
                continue

            index = body.find(self.tmpboundary)
            if index != -1:
                # 找到分隔线，返回分隔线前的数据
                # 并将分隔及分隔线后的数据返回给stream
                read, self.stream.body = body[:index], body[index:]
                self._size += len(read)
                yield read
                if self._last:
                    yield self._last
                break
            else:
                if self.stream.closed:
                    raise RuntimeError("Uncomplete content!")
                # 若没有找到分隔线，为了防止分隔线被读取了一半
                # 选择只返回少于分隔线长度的部分body
                read, body = body[:-self.boundary_len], body[-self.boundary_len:]
                self._size += len(read)
                yield read
                await self.get_message(self.receive, self.stream)

    async def read(self, size=10240):
        read = b""
        assert size > 0, (999, "Read size must > 0")
        while len(read) < size:
            try:
                buffer = await self.body_iter.asend(None)
            except StopAsyncIteration:
                return read
            read = read + buffer
            read, self._last = read[:size], read[size:]
        return read

    @staticmethod
    async def get_message(receive, stream):
        message = await receive()

        if not message['type'] == 'http.request':
            raise RuntimeError(
                f"Unexpected ASGI message type: {message['type']}.")

        if not message.get('more_body', False):
            stream.closed = True
        stream.body += message.get("body", b"")

    def tell(self):
        return self._size

    @classmethod
    async def from_boundary(cls, stream, receive, boundary):
        tmp_boundary = b"--" + boundary
        while not stream.closed:
            await cls.get_message(receive, stream)

            if b"\r\n\r\n" in stream.body and tmp_boundary in stream.body or \
                    stream.closed:
                break

        return cls(stream, receive, boundary,
                   *cls.parse_headers(stream, tmp_boundary))

    @staticmethod
    def parse_headers(stream, tmp_boundary):
        end_boundary = tmp_boundary + b"--"
        body = stream.body
        index = body.find(tmp_boundary)
        if index == body.find(end_boundary):
            raise StopAsyncIteration

        body = body[index + len(tmp_boundary):]
        header_str = body[:body.find(b"\r\n\r\n")]
        body = body[body.find(b"\r\n\r\n") + 4:]
        filename, name, mimetype = "", "", ""
        mime_type_regex = re.compile(b"Content-Type: (.*)")
        for header in header_str.split(b"\r\n"):
            if header.startswith(b"Content-Disposition"):
                for d in header.split(b";"):
                    d = d.strip()
                    if b"=" in d:
                        k, v = d.split(b'=')
                        if k == b'name':
                            name = v.strip(b"\"").decode()
                        elif k == b'filename':
                            filename = v.strip(b"\"").decode()
                        elif k == b"filename*":
                            # 用来处理带编码的文件名，返回unicode
                            enc, lang, fn = v.split(b"'")
                            filename = unquote(
                                fn.decode()).encode().decode(enc.decode())
                break
        mth = mime_type_regex.search(header_str)
        if mth:
            mimetype = mth.group(1).decode()
        stream.body = body
        assert name, "FileStream iterated without File consumed. "
        return name, filename, mimetype


class FileStream(object):

    def __init__(self, receive, boundary):
        self.receive = receive
        self.boundary = boundary
        self.body = b""
        self.closed = False

    def __aiter__(self):
        return self

    async def __anext__(self):
        return await File.from_boundary(self, self.receive, self.boundary)

