import os
import time
import typing
import mimetypes

from apistar.http import Response, StrMapping, StrPairs

from apistellar.helper import parse_date


class FileResponse(Response):
    def __init__(self,
                 content: typing.Any,
                 filename: str = None,
                 status_code: int = 200,
                 headers: typing.Union[StrMapping, StrPairs] = None,
                 exc_info=None,
                 media_type: str = "auto",
                 charset: str = 'utf-8',
                 download: bool = True,
                 req_headers: typing.Union[StrMapping, StrPairs] = None,
    ):
        self.filename = filename
        self.media_type = media_type or self.media_type
        self.charset = charset
        self.download = download
        self.req_headers = req_headers
        super(FileResponse, self).__init__(content, status_code, headers, exc_info)

    def render(self, content: typing.Any):
        if hasattr(content, "read"):
            if not self.filename:
                self.filename = getattr(content, "filename", None) \
                                or os.path.basename(getattr(content, "name", ""))

            return content

        if isinstance(content, bytes):
            return content
        elif isinstance(content, str) and self.charset is not None:
            return content.encode(self.charset)

        valid_types = "bytes" if self.charset is None else "string or bytes"
        raise AssertionError(
            "%s content must be %s. Got %s." %
            (self.__class__.__name__, valid_types, type(content).__name__)
        )

    def set_default_headers(self):
        if 'Content-Length' not in self.headers:
            if hasattr(self.content, "read"):
                assert False, "File like object need specify Content-Length."
            self.headers['Content-Length'] = str(len(self.content))

        assert self.filename, "filename must specify."

        if self.media_type == 'auto':
            self.media_type, encoding = mimetypes.guess_type(self.filename)
            if encoding:
                self.headers['Content-Encoding'] = encoding

        if self.media_type:
            if self.media_type.startswith('text/') and \
                    self.charset and 'charset' not in self.media_type:
                self.media_type += f'; charset={self.charset}'
            self.headers['Content-Type'] = self.media_type

        if self.download:
            self.headers['Content-Disposition'] = f'attachment; ' \
                                                  f'filename="{self.filename}"'
        if "Last-Modified" not in self.headers:
            self.headers['Last-Modified'] = \
                time.strftime("%a, %d %b %Y %H:%M:%S GMT")

        if self.req_headers and "If-Modified-Since" in self.req_headers:
            if_modified_since = parse_date(
                self.req_headers["If-Modified-Since"].split(";")[0].strip())
        else:
            if_modified_since = None

        mtime = parse_date(self.headers['Last-Modified'])
        if if_modified_since is not None and mtime is not None and \
                if_modified_since >= int(mtime):
            self.status_code = 304
