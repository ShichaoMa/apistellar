import pytest

from apistar.exceptions import ValidationError

from apistellar.types import Type, validators


class TestUnion(object):

    @classmethod
    def setup_class(cls):
        class Example(Type):
            field1 = validators.String() | validators.Integer()
            field2 = validators.Union([validators.String(), validators.Integer()]) | validators.Array()
            field3 = validators.Array() | validators.Union([validators.String(), validators.Integer()])

        cls.Example = Example

    def test_string_type(self):
        e = self.Example()
        e.field1 = "1"
        assert e.field1 == "1"
        e.field2 = []
        assert e.field2 == []
        e.field3 = "3"
        assert e.field3 == "3"

    def test_integer_type(self):
        e = self.Example()
        e.field1 = 1
        assert e.field1 == 1
        e.field2 = []
        assert e.field2 == []
        e.field3 = "3"
        assert e.field3 == "3"

    def test_allow_null_failed(self):
        e = self.Example()
        with pytest.raises(ValidationError) as exc_info:
            e.field1 = None
        assert exc_info.value.args[0]["field1"].code == "null"

    def test_allow_null_success(self):
        class Example(Type):
            field = (validators.String() | validators.Integer()) << {"allow_null": True}

        e = Example()
        e.field = None
        assert e.field is None

    def test_default(self):
        class Example(Type):
            field = (validators.String() | validators.Integer()) << {"default": "11"}

        e = Example()
        e.format()
        assert e.field == "11"

    def test_union_type_failed(self):
        e = self.Example()
        with pytest.raises(ValidationError) as exc_info:
            e.field1 = []
        assert exc_info.value.args[0]["field1"].code == "union"
