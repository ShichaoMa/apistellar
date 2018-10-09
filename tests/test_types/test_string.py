import pytest

from apistar.exceptions import ValidationError

from factories import TypeTestBase


class StringTest(TypeTestBase):
    _type = "String"


class TestStringMaxLength(StringTest):
    kwargs = {"max_length": 3}

    def test_failed(self):
        e = self.Example()
        with pytest.raises(ValidationError) as exc_info:
            e.field = "3333"

        assert exc_info.value.args[0].code == "max_length"

    def test_success(self):
        e = self.Example()
        e.field = "33"
        assert e.field == "33"

    def test_argument_error(self):
        with pytest.raises(AssertionError):
            self.gen_class(self._type, max_length="3")()


class TestStringMinLength(StringTest):
    kwargs = {"min_length": 3}

    def test_failed(self):
        e = self.Example()
        with pytest.raises(ValidationError) as exc_info:
            e.field = "33"

        assert exc_info.value.args[0].code == "min_length"

    def test_blank_failed(self):
        e = self.gen_class(self._type, min_length=1)()
        with pytest.raises(ValidationError) as exc_info:
            e.field = ""

        assert exc_info.value.args[0].code == "blank"

    def test_success(self):
        e = self.Example()
        e.field = "333"
        assert e.field == "333"

    def test_argument_error(self):
        with pytest.raises(AssertionError):
            self.gen_class(self._type, min_length="3")()


class TestStringAllowNull(StringTest):

    def test_failed(self):
        e = self.gen_class(self._type)()
        with pytest.raises(ValidationError) as exc_info:
            e.field = None
        assert exc_info.value.args[0].code == "null"

    def test_success(self):
        e = self.gen_class(self._type, allow_null=True)()
        e.field = None
        assert e.field is None
        

class TestStringDefault(StringTest):

    def test_default_value(self):
        cls = self.gen_class(self._type, default="111")
        e = cls()
        assert "field" not in e
        with pytest.raises(AttributeError):
            e.field
        assert e["field"] == "111"
        assert e.field == "111"
        e = cls()
        e.format()
        assert e.field == "111"

    def test_default_factory(self):
        cls = self.gen_class(self._type, default=lambda: "111")
        e = cls()
        assert "field" not in e
        with pytest.raises(AttributeError):
            e.field
        assert e["field"] == "111"
        assert e.field == "111"
        e = cls()
        e.format()
        assert e.field == "111"


class TestStringType(StringTest):

    def test_failed(self):
        e = self.Example()
        with pytest.raises(ValidationError) as exc_info:
            e.field = 3
        assert exc_info.value.args[0].code == "type"

    def test_success(self):
        e = self.Example()
        e.field = "3"
        assert e.field == "3"


class TestStringRequired(StringTest):
    def test_failed(self):
        e = self.Example()
        with pytest.raises(ValidationError) as exc_info:
            e.format()
        assert exc_info.value.args[0]["field"].code == "required"

    def test_success(self):
        e = self.Example()
        e.field = "3"
        e.format()


class TestStringPattern(StringTest):
    kwargs = {"pattern": r"\(.*?\)"}

    def test_failed(self):
        e = self.Example()
        with pytest.raises(ValidationError) as exc_info:
            e.field = "aaa"
        assert exc_info.value.args[0].code == "pattern"

    def test_success(self):
        e = self.Example()
        e.field = "(aaa)"

    def test_argument_error(self):
        with pytest.raises(AssertionError):
            self.gen_class(self._type, pattern=1)()


class TestStringEnum(StringTest):
    kwargs = {"enum": ["a", "b"]}

    def test_failed_enum(self):
        e = self.Example()
        with pytest.raises(ValidationError) as exc_info:
            e.field = "c"
        assert exc_info.value.args[0].code == "enum"

    def test_failed_exact(self):
        e = self.gen_class(self._type, enum=["a"])()
        with pytest.raises(ValidationError) as exc_info:
            e.field = "c"
        assert exc_info.value.args[0].code == "exact"

    def test_success(self):
        e = self.Example()
        e.field = "a"

    def test_argument_error(self):
        with pytest.raises(AssertionError):
            self.gen_class(self._type, enum=3)()

        with pytest.raises(AssertionError):
            self.gen_class(self._type, enum=[3])()


class TestStringFormat(StringTest):

    def test_argument_error(self):
        with pytest.raises(AssertionError):
            self.gen_class(self._type, format=3)()
