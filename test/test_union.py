import pytest

from apistar.exceptions import ValidationError
from star_builder import Type, validators


@pytest.mark.slow
def test_union1():
    class Union(Type):
        field = (validators.Array(validators.String()) | validators.String()) \
                << {"allow_null": True}
    a = Union()
    a.format()
    assert a.field is None
    a.field = ["aaa"]
    assert a.field == ["aaa"]
    a.field = "aaa"
    assert a.field == "aaa"
    with pytest.raises(ValidationError):
        a.field = 1


def test_union2():
    class Union(Type):
        field = (validators.Array(validators.String()) | validators.String()) \
                << {"default": list}
    a = Union()
    a.format()
    assert a.field == []
    a.field = ["aaa"]
    assert a.field == ["aaa"]
    a.field = "aaa"
    assert a.field == "aaa"
    with pytest.raises(ValidationError):
        a.field = 1

