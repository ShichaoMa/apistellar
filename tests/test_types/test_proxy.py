import pytest

from apistar.exceptions import ValidationError

from factories import NestedTypeTestBase


class ProxyTest(NestedTypeTestBase):
    nested_field_type = "String"
    _type = "Proxy"


class TestProxyAllowNull(ProxyTest):

    def test_failed(self):
        e = self.gen_class(self._type, self.nested())()
        with pytest.raises(ValidationError) as exc_info:
            e.field = None
        assert exc_info.value.args[0]["field"].code == "null"

    def test_success(self):
        e = self.gen_class(self._type, self.nested(), allow_null=True)()
        e.field = None
        assert e.field is None


class TestProxyDefault(ProxyTest):

    def test_default_value(self):
        cls = self.gen_class(self._type, self.nested(), default={"field": "111"})
        e = cls()
        assert "field" not in e
        with pytest.raises(AttributeError):
            e.field
        assert e["field"]["field"] == "111"
        assert e.field.field == "111"
        e = cls()
        e.format()
        assert e.field.field == "111"

    def test_default_factory(self):
        cls = self.gen_class(self._type, self.nested(), default=lambda: {"field": "111"})
        e = cls()
        assert "field" not in e
        with pytest.raises(AttributeError):
            e.field
        assert e["field"]["field"] == "111"
        assert e.field.field == "111"
        e = cls()
        e.format()
        assert e.field.field == "111"


