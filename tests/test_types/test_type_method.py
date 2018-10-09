import pytest

from datetime import datetime
from apistar.exceptions import ConfigurationError
from apistellar.types import Type, validators


def test_method_define():
    with pytest.raises(ConfigurationError):
        class Example(Type):
            def get(self):
                pass


def test_to_dict():
    class Example(Type):
        field = validators.String(default="aaa")

    e = Example()
    assert e.to_dict() == {}
    e.format()
    assert e.to_dict() == {"field": "aaa"}


def test_del_before_format():
    class Example(Type):
        field = validators.FormatDateTime(default=datetime.now,
                                          format="%Y%m%d")

    e = Example()
    e.field = "20181010"
    del e.field
    e.format()
    assert "field" in e
    assert len(e) == 1


def test_del_after_format():
    class Example(Type):
        field = validators.FormatDateTime(default=datetime.now, format="%Y%m%d")

    e = Example()

    e.format()
    del e.field
    assert "field" in e
    assert len(e) == 1


def test_init():
    class Example(Type):
        pass
    Example.init(aaaa=1)
    e = Example()
    assert e.aaaa == 1


def test_update():
    class Example(Type):
        field = validators.String()
    e = Example()
    e.update(field="1111")
    assert e.field == "1111"


def test_set():
    class Example(Type):
        pass

    e = Example()
    with pytest.raises(AttributeError):
        e.field = 3

    with pytest.raises(KeyError):
        e["field"] = 4


def test_get():
    class Example(Type):
        pass

    e = Example()
    with pytest.raises(AttributeError):
        e.field

    with pytest.raises(KeyError):
        e["field"]

