import pytest

from datetime import datetime
from apistar.exceptions import ConfigurationError, ValidationError
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
    e.update(field_not_exist="222")
    assert e.field_not_exist == "222"


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
        field1 = validators.String(default="10")
        field2 = validators.FormatDateTime(default=datetime(2018, 10, 20, 11, 11, 11))
        field3 = validators.String()

    e = Example()
    with pytest.raises(KeyError):
        e["field"]

    with pytest.raises(KeyError):
        e["field3"]

    with pytest.raises(AttributeError):
        e.field1

    e["field1"]

    with pytest.raises(AttributeError):
        e.field

    with pytest.raises(AttributeError):
        e.field3

    e.field1

    assert e["field2"] == "2018-10-20 11:11:11"


def test_repr():
    class Example(Type):
        field = validators.String(default="10")
        field1 = validators.String(default="20")
    e = Example()
    assert repr(e) == "<Example()>"
    e.format()
    assert repr(e) == "<Example(field='10', field1='20')>"


def test___init__():
    class Example(Type):
        field = validators.String()
        field1 = validators.String(default="1")

    a = Example({"field": "1"})
    assert str(a) == "<Example(field='1')>"

    a = Example(field="1")
    assert str(a) == "<Example(field='1')>"

    class A:
        field = "1"

    a = Example(A())
    assert str(a) == "<Example(field='1')>"

    with pytest.raises(ValidationError):
        Example("1")

    with pytest.raises(ValidationError) as exc_info:
        Example({"field": 1}, force_format=True)

    assert exc_info.value.args[0]["field"].code == "type"


def test_format():
    class Example(Type):
        field = validators.String()
    e = Example()
    e.field = "a"
    e.format()
    with pytest.raises(ValidationError):
        del e.field
    # 第二次format无效
    e.format()


def test_is_valid():
    class Example(Type):
        field = validators.String()

    assert Example.validator.properties["field"].is_valid(1) is False
    assert Example.validator.properties["field"].is_valid("a") is True


