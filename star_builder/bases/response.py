import time
import typing
import mimetypes

from apistar.http import Response, StrMapping, StrPairs

from ..helper import parse_date, parse_range_header, file_iter_range


class FileResponse(Response):
    def __init__(self,
                 content: typing.Any,
                 filename: str=None,
                 status_code: int=200,
                 headers: typing.Union[StrMapping, StrPairs]=None,
                 exc_info=None,
                 media_type: str="auto",
                 charset: str='utf-8',
                 download: bool=True,
                 last_modified: str=None,
                 if_modified_since: str=None,
                 ranges: str=None,
    ) -> None:
        self.filename = filename
        self.media_type = media_type or self.media_type
        self.charset = charset
        self.download = download
        self.last_modified = last_modified
        self.if_modified_since = if_modified_since
        self.ranges = ranges
        super(FileResponse, self).__init__(content, status_code, headers, exc_info)

    def render(self, content: typing.Any) -> bytes:
        if hasattr(content, "read"):
            if not self.filename:
                self.filename = getattr(content, "filename", None)
            return content

        if isinstance(content, bytes):
            return content
        elif isinstance(content, str) and self.charset is not None:
            return content.encode(self.charset)

        valid_types = "bytes" if self.charset is None else "string or bytes"
        raise RuntimeError(
            "%s content must be %s. Got %s." %
            (self.__class__.__name__, valid_types, type(content).__name__)
        )

    def set_default_headers(self):
        if 'Content-Length' not in self.headers:
            if hasattr(self.content, "read"):
                assert 'Content-Length' not in self.headers, (
                    999, "Need specify Content-Length.")
            self.headers['Content-Length'] = str(len(self.content))

        assert self.filename, "Filename must specific."

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
        if not self.last_modified:
            self.last_modified = time.strftime("%a, %d %b %Y %H:%M:%S GMT")
        self.headers['Last-Modified'] = self.last_modified

        if self.if_modified_since:
            self.if_modified_since = parse_date(
                self.if_modified_since.split(";")[0].strip())

        mtime = parse_date(self.last_modified)
        if self.if_modified_since is not None and mtime is not None and \
                self.if_modified_since >= int(mtime):
            self.headers['Date'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT",
                                            time.gmtime())
        else:
            self.headers["Accept-Ranges"] = "bytes"
            if self.ranges:
                self.ranges = list(
                    parse_range_header(self.ranges, len(self.content)))
                if not self.ranges:
                    self.exc_info = "Requested Range Not Satisfiable"
                    self.status_code = 416
                offset, end = self.ranges[0]
                self.headers["Content-Range"] = "bytes %d-%d/%d" % (
                    offset, end - 1, len(self.content))
                self.headers["Content-Length"] = str(end - offset)
                self.content = file_iter_range(self.content, offset, end - offset)
                self.status_code = 206
