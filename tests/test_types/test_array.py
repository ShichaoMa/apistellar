import pytest

from apistar.exceptions import ValidationError
from apistellar.types.validators import String, Integer, Boolean

from factories import TypeTestBase


class ArrayTest(TypeTestBase):
    _type = "Array"


class TestArrayMaxItems(ArrayTest):
    kwargs = {"max_items": 3}

    def test_failed(self):
        e = self.Example()
        with pytest.raises(ValidationError) as exc_info:
            e.field = ["aaa", "bbb", "ccc", "ddd"]

        assert exc_info.value.args[0].code == "max_items"

    def test_success(self):
        e = self.Example()
        e.field = ["aaa", "bbb"]
        assert e.field == ["aaa", "bbb"]

    def test_argument_error(self):
        with pytest.raises(AssertionError):
            self.gen_class(self._type, max_items="3")()


class TestArrayMinItems(ArrayTest):
    kwargs = {"min_items": 3}

    def test_failed(self):
        e = self.Example()
        with pytest.raises(ValidationError) as exc_info:
            e.field = ["aaa", "bbb"]

        assert exc_info.value.args[0].code == "min_items"

    def test_empty_failed(self):
        e = self.gen_class(self._type, min_items=1)()
        with pytest.raises(ValidationError) as exc_info:
            e.field = []

        assert exc_info.value.args[0].code == "empty"

    def test_success(self):
        e = self.Example()
        e.field = ["aaa", "bbb", "ccc"]
        assert e.field == ["aaa", "bbb", "ccc"]

    def test_argument_error(self):
        with pytest.raises(AssertionError):
            self.gen_class(self._type, min_items="3")()


class TestArrayExactItems(ArrayTest):
    kwargs = {"min_items": 3, "max_items": 3}

    def test_failed(self):
        e = self.Example()
        with pytest.raises(ValidationError) as exc_info:
            e.field = ["aaa", "bbb"]

        assert exc_info.value.args[0].code == "exact_items"

    def test_success(self):
        e = self.Example()
        e.field = ["aaa", "bbb", "ccc"]
        assert e.field == ["aaa", "bbb", "ccc"]


class TestArrayAllowNull(ArrayTest):

    def test_failed(self):
        e = self.gen_class(self._type)()
        with pytest.raises(ValidationError) as exc_info:
            e.field = None
        assert exc_info.value.args[0].code == "null"

    def test_success(self):
        e = self.gen_class(self._type, allow_null=True)()
        e.field = None
        assert e.field is None


class TestArrayDefault(ArrayTest):

    def test_default_value(self):
        cls = self.gen_class(self._type, default=[])
        e = cls()
        assert "field" not in e
        with pytest.raises(AttributeError):
            e.field
        assert e["field"] == []
        assert e.field == []
        e = cls()
        e.format()
        assert e.field == []

    def test_default_factory(self):
        cls = self.gen_class(self._type, default=lambda: [])
        e = cls()
        assert "field" not in e
        with pytest.raises(AttributeError):
            e.field
        assert e["field"] == []
        assert e.field == []
        e = cls()
        e.format()
        assert e.field == []


class TestArrayType(ArrayTest):

    def test_failed(self):
        e = self.Example()
        with pytest.raises(ValidationError) as exc_info:
            e.field = 3
        assert exc_info.value.args[0].code == "type"

    def test_success(self):
        e = self.Example()
        e.field = []
        assert e.field == []

    def test_failed_inner_type_one(self):
        e = self.gen_class(self._type, items=String())()
        with pytest.raises(ValidationError) as exc_info:
            e.field = [1]
        assert exc_info.value.args[0][0].code == "type"

    def test_success_inner_type_one(self):
        e = self.gen_class(self._type, items=String())()
        e.field = ["1"]
        assert e.field == ["1"]

    def test_failed_inner_type_many(self):
        e = self.gen_class(self._type, items=[String(), Integer()])()
        with pytest.raises(ValidationError) as exc_info:
            e.field = [1, "1"]
        assert exc_info.value.args[0][0].code == "type"
        assert exc_info.value.args[0][1].code == "type"

    def test_success_inner_type_many(self):
        e = self.gen_class(self._type, items=[String(), Integer()])()
        e.field = ["1", 1]
        assert e.field == ["1", 1]


class TestArrayRequired(ArrayTest):
    def test_failed(self):
        e = self.Example()
        with pytest.raises(ValidationError) as exc_info:
            e.format()
        assert exc_info.value.args[0]["field"].code == "required"

    def test_success(self):
        e = self.Example()
        e.field = []
        e.format()


class TestArrayAdditionalItems(ArrayTest):

    def test_additional_items_failed(self):
        e = self.gen_class(self._type, items=[String(), Integer()],
                           additional_items=False)()
        with pytest.raises(ValidationError) as exc_info:
            e.field = ["1", 1, 1]
        assert exc_info.value.args[0].code == "additional_items"

    def test_additional_items_success(self):
        e = self.gen_class(self._type, items=[String(), Integer()])()
        e.field = ["1", 1, None]
        assert e.field == ["1", 1, None]

    def test_additional_items_validate_failed(self):
        e = self.gen_class(self._type, items=[String(), Integer()],
                           additional_items=String())()
        with pytest.raises(ValidationError) as exc_info:
            e.field = ["1", 1, 1]
        assert exc_info.value.args[0][2].code == "type"

    def test_additional_items_validate_success(self):
        e = self.gen_class(self._type, items=[String(), Integer()],
                           additional_items=Boolean())(field=["1", 1, "1"])
        e.format(allow_coerce=True)
        assert e.field == ["1", 1, True]

    def test_argument_error(self):
        with pytest.raises(AssertionError):
            self.gen_class(self._type, additional_items="1")()


class TestArrayUniqueItems(ArrayTest):

    def test_unique_items_failed(self):
        e = self.gen_class(self._type, unique_items=True)()
        with pytest.raises(ValidationError) as exc_info:
            e.field = ["1", 1, 1]
        assert exc_info.value.args[0][2].code == "unique_items"

    def test_argument_error(self):
        with pytest.raises(AssertionError):
            self.gen_class(self._type, unique_items=3)()
