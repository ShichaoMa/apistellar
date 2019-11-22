import re
import os
import typing
import contextvars

from enum import Enum
from urllib.parse import unquote
from collections import namedtuple
from flask.sessions import SecureCookieSession

from toolkit import global_cache_classproperty, load
from toolkit.settings import SettingsLoader, Settings, FrozenSettings

from .exceptions import Readonly

Cookie = typing.NewType('Cookie', str)
# 用于标记已知名字的表单字段
FormParam = typing.NewType("FormParam", str)
Session = typing.NewType("Session", SecureCookieSession)
# 这种类型用于标记有且只有文件的表单
MultiPartForm = typing.NewType("MultiPartForm", dict)
# 这种类型用于标记不存在文件的表单
UrlEncodeForm = typing.NewType("UrlEncodeForm", dict)
DummyFlaskApp = namedtuple(
    "DummyFlaskApp",
    "session_cookie_name,secret_key,permanent_session_lifetime,config")

# 全局settings对象，使用init_settings来初始化
settings = FrozenSettings(Settings())


class File(object):
    mime_type_regex = re.compile(rb"Content-Type: (\S*)")
    content_length_regex = re.compile(rb"Content-Length: (\d*)")
    disposition_regex = re.compile(
        rb'Content-Disposition: form-data(?:; name\*?=\"?'
        rb'(?:(?P<name_enc>[\w\-]+?)'
        rb'\'(?P<name_lang>\w*)\')?'
        rb'(?P<name>[^\";]*)\"?)?.*?(?:; filename\*?=\"?'
        rb'(?:(?P<enc>[\w\-]+?)'
        rb'\'(?P<lang>\w*)\')?'
        rb'(?P<filename>[^\"]*?)\"?)?(?:$|\r\n)')

    def __init__(self, stream, receive, boundary, name,
                 filename, mimetype, content_length):
        self.content_length = content_length
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

    def __str__(self):
        return f"<{self.__class__.__name__} " \
               f"name={self.name} " \
               f"filename={self.filename} >"

    __repr__ = __str__

    def iter_content(self):
        return self.body_iter

    async def _iter_content(self):
        stream = self.stream
        while True:
            # 如果存在read过程中剩下的，则直接返回
            if self._last:
                read = self._last
                self._last = b""
                yield read
                continue

            index = self.stream.body.find(self.tmpboundary)
            if index != -1:
                # 找到分隔线，返回分隔线前的数据
                # 并将分隔及分隔线后的数据返回给stream
                read, stream.body = stream.body[:index], stream.body[index:]
                self._size += len(read)
                yield read
                if self._last:
                    read = self._last
                    self._last = b""
                    yield read
                break
            else:
                assert not self.stream.closed, "Content not complete!"
                # 若没有找到分隔线，为了防止分隔线被读取了一半
                # 选择只返回少于分隔线长度的部分body
                read = stream.body[:-self.boundary_len]
                stream.body = stream.body[-self.boundary_len:]
                self._size += len(read)
                yield read
                await self.get_message(self.receive, stream)

    async def read(self, size=10240):
        """
        推荐直接迭代File对象，性能较好

        :param size:
        :return:
        """
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

        assert message['type'] == 'http.request', \
            f"Unexpected ASGI message type: {message['type']}."

        if not message.get('more_body', False):
            stream.closed = True
        stream.body += message.get("body", b"")

    def tell(self):
        return self._size - len(self._last)

    @classmethod
    async def from_boundary(cls, stream, receive, boundary):
        tmp_boundary = b"--" + boundary
        while not stream.closed:
            await cls.get_message(receive, stream)

            if b"\r\n\r\n" in stream.body and tmp_boundary in stream.body or \
                    stream.closed:
                break

        return cls(
            stream, receive, boundary, *cls.get_headers(stream, tmp_boundary))

    @classmethod
    def get_headers(cls, stream, tmp_boundary):
        end_boundary = tmp_boundary + b"--"
        body = stream.body
        index = body.find(tmp_boundary)
        if index == body.find(end_boundary):
            raise StopAsyncIteration
        body = body[index + len(tmp_boundary):]
        split_index = body.find(b"\r\n\r\n")
        header_str, body = body[:split_index], body[split_index + 4:]
        headers = cls.parse(header_str)
        stream.body = body
        return headers

    @classmethod
    def parse(cls, header_str):
        groups = cls.disposition_regex.search(header_str).groupdict()

        filename = groups["filename"] and unquote(groups["filename"].decode())
        if groups["enc"]:
            filename = filename.encode().decode(groups["enc"].decode())

        name = groups["name"] and unquote(groups["name"].decode())
        if groups["name_enc"]:
            name = name.encode().decode(groups["name_enc"].decode())

        mth = cls.mime_type_regex.search(header_str)
        mimetype = mth and mth.group(1).decode()
        mth = cls.content_length_regex.search(header_str) or 0
        content_length = int(mth and mth.group(1))
        assert name, "FileStream iterated without File consumed. "
        return name, filename, mimetype, content_length


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


class InheritType(Enum):
    DUPLICATE = 0  # 重名且类型相符，在参数列表和赋值中不体现，在super中体现
    OVERWRITE = 1  # 重名但是类型不同，全部位置要体现，但是需要父类的参数改名字
    NORMAL = 2  # 正常的情况


class Inject(object):

    def __init__(self, type, default):
        self.annotation = self.type = type
        self.name = type.__name__.lower()
        self.default = default

    def __set__(self, instance, value):
        raise Readonly(f"Readonly object of {self.type.__name__}.")

    def __get__(self, instance, cls):
        if instance:
            return instance.__dict__[self.name]
        else:
            return self


class InjectManager(object):

    def __init__(self, default=None):
        self.default = default

    def __lshift__(self, other):
        return Inject(other, self.default)

    def __call__(self, *, default=None):
        return InjectManager(default)


inject = InjectManager()


class SettingsMixin(object):
    settings_path = None

    @global_cache_classproperty
    def settings(cls):
        """
        这个应该在app加载时调用，这样project_path才准确。
        由于有些项目可能在模块作用域就需要使用settings中的配置，
        所以调用应该在项目模块加载之前。

        :return:
        """
        return SettingsLoader().load(
            SettingsMixin.settings_path or "settings",
            default={"PROJECT_PATH": os.path.abspath(os.getcwd())})


def init_settings(settings_path):
    """
    初始化settings
    :param settings_path:
    :return:
    """
    SettingsMixin.settings_path = settings_path
    settings._json.update(SettingsMixin.settings._json)


class Local(object):
    """
    提供一个协程的上下文，使用set_default在此上文中预设一些请求相关的可注入对象
    如：ASGIScope, session等
    """

    _default = dict(scope="apistar.server.asgi.ASGIScope")
    cotextvar_mappings = dict()

    @global_cache_classproperty
    def local_variable(cls):
        """
        存储配置的可注入的上下文变量及其类型
        :return:
        """
        lv = cls._default.copy()
        lv.update(settings.get("LOCAL_VARIABLE", dict()))
        var_types = dict()
        for k, v in lv.items():
            var_types[k] = load(v)
        return var_types

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError as e:
            raise AttributeError(e)

    def __getitem__(self, item):
        key = self.cotextvar_mappings.get(item)
        if key is None:
            raise KeyError(f"{item} not found!")
        return key.get()

    def get(self, item, default=None):
        try:
            return self[item]
        except KeyError:
            return default

    def __setitem__(self, key, value):
        if key not in self.cotextvar_mappings:
            self.cotextvar_mappings[key] = contextvars.ContextVar(key)
        self.cotextvar_mappings[key].set(value)

    def __setattr__(self, key, value):
        self[key] = value

    def set(self, key, value):
        self[key] = value

    def clear(self):
        ctx = contextvars.copy_context()
        for var in ctx.keys():
            var.set(None)

    @classmethod
    def set_default(cls, name, val_path):
        cls._default[name] = val_path


coroutinelocal = Local()
