import pytest

from apistar.exceptions import ValidationError

from factories import TypeTestBase


@pytest.fixture(params=["Integer", "Number"])
def _type(request):
    return request.param


class NumericTypeTest(TypeTestBase):
    _type = "Integer"


class TestNumericTypeMinimum(NumericTypeTest):
    kwargs = {"minimum": 10}

    def test_failed(self, _type):
        e = self.gen_class(_type, **self.kwargs)()
        with pytest.raises(ValidationError) as exc_info:
            e.field = 9

        assert exc_info.value.args[0]["field"].code == "minimum"

    def test_success(self, _type):
        e = self.gen_class(_type, **self.kwargs)()
        e.field = 11
        assert e.field == 11

    def test_exclude_min_failed(self, _type):
        e = self.gen_class(_type, **self.kwargs, exclusive_minimum=True)()
        with pytest.raises(ValidationError) as exc_info:
            e.field = 10

        assert exc_info.value.args[0]["field"].code == "exclusive_minimum"

    def test_exclude_min_success(self, _type):
        e = self.gen_class(_type, **self.kwargs, exclusive_minimum=True)()
        e.field = 11
        assert e.field == 11

    def test_argument_error(self, _type):
        with pytest.raises(AssertionError):
            self.gen_class(_type, minimum="3")()


class TestNumericTypeMaximum(NumericTypeTest):
    kwargs = {"maximum": 3}

    def test_failed(self, _type):
        e = self.gen_class(_type, **self.kwargs)()
        with pytest.raises(ValidationError) as exc_info:
            e.field = 4

        assert exc_info.value.args[0]["field"].code == "maximum"

    def test_success(self, _type):
        e = self.gen_class(_type, **self.kwargs)()
        e.field = 2
        assert e.field == 2

    def test_exclude_max_failed(self, _type):
        e = self.gen_class(_type, **self.kwargs, exclusive_maximum=True)()
        with pytest.raises(ValidationError) as exc_info:
            e.field = 3

        assert exc_info.value.args[0]["field"].code == "exclusive_maximum"

    def test_exclude_max_success(self, _type):
        e = self.gen_class(_type, **self.kwargs, exclusive_maximum=True)()
        e.field = 2
        assert e.field == 2

    def test_argument_error(self, _type):
        with pytest.raises(AssertionError):
            self.gen_class(_type, maximum="3")()


class TestNumericTypeAllowNull(NumericTypeTest):

    def test_failed(self, _type):
        e = self.gen_class(_type, **self.kwargs)()
        with pytest.raises(ValidationError) as exc_info:
            e.field = None
        assert exc_info.value.args[0]["field"].code == "null"

    def test_success(self, _type):
        e = self.gen_class(_type, allow_null=True)()
        e.field = None
        assert e.field is None


class TestNumericTypeDefault(NumericTypeTest):

    def test_default_value(self, _type):
        cls = self.gen_class(_type, default=111)
        e = cls()
        assert "field" not in e
        with pytest.raises(AttributeError):
            e.field
        assert e["field"] == 111
        assert e.field == 111
        e = cls()
        e.format()
        assert e.field == 111

    def test_default_factory(self, _type):
        cls = self.gen_class(_type, default=lambda: 111)
        e = cls()
        assert "field" not in e
        with pytest.raises(AttributeError):
            e.field
        assert e["field"] == 111
        assert e.field == 111
        e = cls()
        e.format()
        assert e.field == 111


class TestNumericTypeType(NumericTypeTest):

    def test_failed(self, _type):
        e = self.gen_class(_type, **self.kwargs)()
        with pytest.raises(ValidationError) as exc_info:
            e.field = "3"
        assert exc_info.value.args[0]["field"].code == "type"

    def test_success(self, _type):
        e = self.gen_class(_type, **self.kwargs)()
        e.field = 3
        assert e.field == 3


class TestNumericTypeRequired(NumericTypeTest):
    def test_failed(self, _type):
        e = self.gen_class(_type, **self.kwargs)()
        with pytest.raises(ValidationError) as exc_info:
            e.format()
        assert exc_info.value.args[0]["field"].code == "required"

    def test_success(self, _type):
        e = self.gen_class(_type, **self.kwargs)()
        e.field = 3
        e.format()


class TestNumericTypeMultiple(NumericTypeTest):
    kwargs = {"multiple_of": 3}

    def test_failed(self, _type):
        e = self.gen_class(_type, **self.kwargs)()
        with pytest.raises(ValidationError) as exc_info:
            e.field = 4
        assert exc_info.value.args[0]["field"].code == "multiple_of"

    def test_float_failed(self, _type):
        e = self.gen_class(_type, multiple_of=1.5)()
        with pytest.raises(ValidationError) as exc_info:
            e.field = 4
        assert exc_info.value.args[0]["field"].code == "multiple_of"

    def test_success(self, _type):
        e = self.gen_class(_type, **self.kwargs)()
        e.field = 6

    def test_float_success(self, _type):
        e = self.gen_class(_type, multiple_of=1.5)()
        e.field = 6

    def test_argument_error(self, _type):
        with pytest.raises(AssertionError):
            self.gen_class(_type, multiple_of="3")()


class TestNumericTypeEnum(NumericTypeTest):
    kwargs = {"enum": [1, 2]}

    def test_failed_enum(self, _type):
        e = self.gen_class(_type, **self.kwargs)()
        with pytest.raises(ValidationError) as exc_info:
            e.field = 3
        assert exc_info.value.args[0]["field"].code == "enum"

    def test_failed_exact(self, _type):
        e = self.gen_class(_type, enum=[1])()
        with pytest.raises(ValidationError) as exc_info:
            e.field = 2
        assert exc_info.value.args[0]["field"].code == "exact"

    def test_success(self, _type):
        e = self.gen_class(_type, **self.kwargs)()
        e.field = 1

    def test_argument_error(self, _type):
        with pytest.raises(AssertionError):
            self.gen_class(_type, enum="a")()

        with pytest.raises(AssertionError):
            self.gen_class(_type, enum=["a"])()


class TestInteger(NumericTypeTest):
    def test_not_integer(self):
        e = self.Example()
        with pytest.raises(ValidationError) as exc_info:
           e.field = 1.1

        assert exc_info.value.args[0]["field"].code == "integer"

    def test_allow_coerce(self, _type):
        e = self.gen_class(_type, **self.kwargs)(field="123")
        e.format(allow_coerce=True)
        e = self.gen_class(_type, **self.kwargs)(field=True)
        e.format(allow_coerce=True)


class TestNumber(NumericTypeTest):

    def test_finite(self):
        e = self.gen_class("Number")()
        with pytest.raises(ValidationError) as exc_info:
            e.field = float("inf")

        assert exc_info.value.args[0]["field"].code == "finite"
