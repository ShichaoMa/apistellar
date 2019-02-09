import pytest

from apistellar import FileResponse


class TestFileResposne(object):

    def test_content_is_bytes(self):
        resp = FileResponse(b"abc", filename="ddd.png")
        assert resp.content == b"abc"
        assert resp.headers["content-length"] == "3"
        assert "last-modified" in resp.headers
        assert resp.filename == "ddd.png"
        assert resp.headers["content-type"] == "image/png"
        assert resp.headers["Content-Disposition"] == \
               'attachment; filename="ddd.png"'
        assert resp.status_code == 200

    def test_content_is_bytes_with_media_type(self):
        resp = FileResponse(b"abc", filename="ddd.png", media_type="image/jpeg")
        assert resp.content == b"abc"
        assert resp.headers["content-length"] == "3"
        assert "last-modified" in resp.headers
        assert resp.filename == "ddd.png"
        assert resp.headers["content-type"] == "image/jpeg"
        assert resp.headers["Content-Disposition"] == \
               'attachment; filename="ddd.png"'
        assert resp.status_code == 200

    def test_content_is_fileobj(self, join_root_dir):
        resp = FileResponse(open(join_root_dir("test_data/test.xz")),
                            headers={"content-length": "10"})
        assert resp.filename == "test.xz"
        assert resp.headers["content-length"] == "10"
        assert resp.headers["content-encoding"] == "xz"

    def test_content_is_fileobj_without_content_length(self, join_root_dir):
        with pytest.raises(AssertionError) as error_info:
            FileResponse(open(join_root_dir("test_data/settings.py")))

        assert error_info.value.args[0] == \
               "File like object need specify Content-Length."

    def test_content_is_invalid(self):
        with pytest.raises(AssertionError) as error_info:
            FileResponse({})

        assert error_info.value.args[0] == \
               "FileResponse content must be string or bytes. Got dict."

    def test_content_is_invalid_without_charset(self):
        with pytest.raises(AssertionError) as error_info:
            FileResponse({} ,charset=None)

        assert error_info.value.args[0] == \
               "FileResponse content must be bytes. Got dict."

    def test_content_is_bytes_without_filename(self):
        with pytest.raises(AssertionError) as error_info:
            FileResponse(b"abc")
        assert error_info.value.args[0] == "filename must specify."

    def test_content_type(self, join_root_dir):
        resp = FileResponse(open(join_root_dir("test_data/settings.py")),
                            headers={"content-length": "10"})
        assert resp.headers["content-type"] == "text/x-python; charset=utf-8"

    def test_not_download(self, join_root_dir):
        resp = FileResponse(open(join_root_dir("test_data/settings.py")),
                            headers={"content-length": "10"}, download=False)
        assert "Content-Disposition" not in resp.headers

    def test_if_modified_since(self):
        resp = FileResponse("我的", filename="ddd.jpg",
                            headers={"Last-Modified":
                                         "Fri, 08 Feb 2019 22:56:51 GMT"},
                            req_headers={"If-Modified-Since":
                                             "Fri, 08 Feb 2019 22:56:53 GMT"})
        assert resp.status_code == 304
