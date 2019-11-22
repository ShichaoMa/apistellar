import pytest

from apistellar import validators, Type
from apistar.exceptions import ValidationError


class TestValidator(object):

    def test_string(self):
        field = validators.String()
        assert len(field.errors) >= 9

    def test_integer(self):
        field = validators.Integer()
        assert len(field.errors) >= 11

    def test_number(self):
        field = validators.Number()
        assert len(field.errors) >= 11

    def test_boolean(self):
        field = validators.Boolean()
        assert len(field.errors) >= 2

    def test_proxy(self):
        field = validators.Proxy(validators.Boolean())
        assert len(field.errors) >= 1

    def test_object(self):
        class Example(Type):
            a = validators.String()

        assert len(Example.validator.errors) >= 8

    def test_array(self):
        field = validators.Array(validators.String)
        assert len(field.errors) >= 8

    def test_Union(self):
        field = validators.Union([validators.String()])
        assert len(field.errors) >= 2


def clear_cache(ins_or_cls, method_name):
    cache_key = "_" + method_name
    if cache_key in ins_or_cls.__dict__:
        delattr(ins_or_cls, "_errors")


class TestValidatorWithCustomErrorSettings():
    pytestmark = [
        pytest.mark.env(ERROR_DESC="test_data.err_desc.errors")
    ]

    def setup(self):
        clear_cache(validators.String, "errors")
        clear_cache(validators.Integer, "errors")
        clear_cache(validators.Number, "errors")
        clear_cache(validators.NumericType, "errors")
        clear_cache(validators.Proxy, "errors")
        clear_cache(validators.Object, "errors")
        clear_cache(validators.Array, "errors")
        clear_cache(validators.Boolean, "errors")
        clear_cache(validators.Union, "errors")

    def test_string(self):
        field = validators.String()
        assert field.errors["exact"] == '只能是{exact}'

    def test_integer(self):
        field = validators.Integer()
        assert field.errors["exact"] == '必须是{exact}'

    def test_number(self):
        field = validators.Number()
        assert field.errors["exact"] == '必须是{exact}'

    def test_boolean(self):
        field = validators.Boolean()
        assert field.errors["null"] == '不能为空'

    def test_proxy(self):
        field = validators.Proxy(validators.Boolean())
        assert field.errors["null"] == '不能为空'

    def test_array(self):
        field = validators.Array(validators.String)
        assert field.errors["type"] == '必须是数组'

    def test_object(self):
        class Example(Type):
            a = validators.String()
        assert Example.validator.errors["type"] == '必须是一个对象'

    def test_union(self):
        field = validators.Union([validators.String()])
        assert field.errors["union"] == '必须是{items}类型之一'

    def test_union_type_failed(self):
        class Example(Type):
            field = validators.Union([validators.String(), validators.Integer()])
        with pytest.raises(ValidationError) as exc_info:
            Example().field = 1.2
        assert exc_info.value.args[0]["field"] == '必须是[String, Integer]类型之一'
