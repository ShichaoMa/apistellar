import json

from apistar.http import Response
from apistellar.bases.hooks import ErrorHook

from collections import namedtuple


def test_error_hook1():
    hook = ErrorHook()
    app = namedtuple("App", "debug")
    app.debug = True
    content = hook.on_error(AssertionError([123, "error", {"id": 1111}]), app).content
    data = json.loads(content)
    assert data["code"] == 123
    assert data["message"] == "error"
    assert data["extra"] == {"id": 1111}
    assert "detail" in data


def test_error_hook2():
    hook = ErrorHook()
    app = namedtuple("App", "debug")
    app.debug = False
    content = hook.on_error(AssertionError([123, "error", {"id": 1111}]), app).content
    data = json.loads(content)
    assert data["code"] == 123
    assert data["message"] == "error"
    assert data["extra"] == {"id": 1111}
    assert "detail" not in data


def test_error_hook3():
    hook = ErrorHook()
    app = namedtuple("App", "debug")
    app.debug = False
    content = hook.on_error(AssertionError(123), app).content
    data = json.loads(content)
    assert data["code"] == 123
    assert data["message"] == "Not configured error"
    assert data["extra"] is None
    assert "detail" not in data


def test_error_hook4():
    hook = ErrorHook()
    app = namedtuple("App", "debug")
    app.debug = False
    content = hook.on_error(AssertionError("test error"), app).content
    data = json.loads(content)
    assert data["code"] == 999
    assert data["message"] == "test error"
    assert data["extra"] is None
    assert "detail" not in data


def test_error_hook5():
    hook = ErrorHook()
    app = namedtuple("App", "debug")
    app.debug = False
    content = hook.on_error(AssertionError(["test error", {"id": 2}]), app).content
    data = json.loads(content)
    assert data["code"] == 999
    assert data["message"] == "test error"
    assert data["extra"] == {"id": 2}
    assert "detail" not in data


def test_error_hook6():
    hook = ErrorHook()
    app = namedtuple("App", "debug")
    content = hook.on_error(Exception(Response(content="abc")), app).content
    assert content == b"abc"


def test_error_hook7():
    hook = ErrorHook()
    app = namedtuple("App", "debug")
    content = hook.on_error(AssertionError(), app).content
    data = json.loads(content)
    assert data["code"] == 999
    assert data["message"] == "Unknown error"


def test_error_hook8():
    errors = {123: "测试错误"}
    ErrorHook.register(errors)
    hook = ErrorHook()
    app = namedtuple("App", "debug")
    content = hook.on_error(AssertionError(123), app).content
    data = json.loads(content)
    assert data["code"] == 123
    assert data["message"] == errors[123]
