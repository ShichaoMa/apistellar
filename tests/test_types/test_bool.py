import pytest

from apistar.exceptions import ValidationError

from factories import TypeTestBase


class BoolTest(TypeTestBase):
    _type = "Boolean"


class TestBooleanAllowNull(BoolTest):

    def test_failed(self):
        e = self.gen_class(self._type)()
        with pytest.raises(ValidationError) as exc_info:
            e.field = None
        assert exc_info.value.args[0]["field"].code == "null"

    def test_success(self):
        e = self.gen_class(self._type, allow_null=True)()
        e.field = None
        assert e.field is None

    def test_allow_coerce_and_empty(self):
        e = self.gen_class(self._type, allow_null=True)(field="")
        e.format(allow_coerce=True)
        assert e.field is None

    def test_allow_coerce_and_none(self):
        e = self.gen_class(self._type, allow_null=True)(field="none")
        e.format(allow_coerce=True)
        assert e.field is None

    def test_allow_coerce_and_null(self):
        e = self.gen_class(self._type, allow_null=True)(field="null")
        e.format(allow_coerce=True)
        assert e.field is None

    def test_allow_coerce_and_not_found(self):
        with pytest.raises(ValidationError) as exc_info:
            e = self.gen_class(self._type, allow_null=True)(field="nul")
            e.format(allow_coerce=True)
        assert exc_info.value.args[0]["field"].code == "type"


class TestBooleanDefault(BoolTest):

    def test_default_value(self):
        cls = self.gen_class(self._type, default=True)
        e = cls()
        assert "field" not in e
        with pytest.raises(AttributeError):
            e.field
        assert e["field"] is True
        assert e.field is True
        e = cls()
        e.format()
        assert e.field is True

    def test_default_factory(self):
        cls = self.gen_class(self._type, default=lambda: False)
        e = cls()
        assert "field" not in e
        with pytest.raises(AttributeError):
            e.field
        assert e["field"] is False
        assert e.field is False
        e = cls()
        e.format()
        assert e.field is False


class TestBooleanType(BoolTest):

    def test_failed(self):
        e = self.Example()
        with pytest.raises(ValidationError) as exc_info:
            e.field = 11
        assert exc_info.value.args[0]["field"].code == "type"

    def test_success(self):
        e = self.Example()
        e.field = True
        assert e.field is True

    def test_coerce_integer_true(self):
        e = self.Example(field=1)
        e.format(allow_coerce=True)
        assert e.field is True

    def test_coerce_integer_false(self):
        e = self.Example(field=0)
        e.format(allow_coerce=True)
        assert e.field is False

    def test_coerce_empty(self):
        e = self.Example(field="")
        e.format(allow_coerce=True)
        assert e.field is False

    def test_coerce_string_integer_true(self):
        e = self.Example(field="1")
        e.format(allow_coerce=True)
        assert e.field is True

    def test_coerce_string_integer_false(self):
        e = self.Example(field="0")
        e.format(allow_coerce=True)
        assert e.field is False

    def test_coerce_string_true(self):
        e = self.Example(field="true")
        e.format(allow_coerce=True)
        assert e.field is True

    def test_coerce_string_false(self):
        e = self.Example(field="false")
        e.format(allow_coerce=True)
        assert e.field is False

    def test_coerce_string_on(self):
        e = self.Example(field="on")
        e.format(allow_coerce=True)
        assert e.field is True

    def test_coerce_string_off(self):
        e = self.Example(field="off")
        e.format(allow_coerce=True)
        assert e.field is False


class TestBooleanRequired(BoolTest):
    def test_failed(self):
        e = self.Example()
        with pytest.raises(ValidationError) as exc_info:
            e.format()
        assert exc_info.value.args[0]["field"].code == "required"

    def test_success(self):
        e = self.Example()
        e.field = False
        e.format()
