import pytest

from apistellar import Type, validators
from apistar.validators import ValidationError


def test_maximum():
    class A(Type):
        title = validators.Number(maximum=1024)

    a = A()
    with pytest.raises(ValidationError):
        a.title = 12345


def test_allow_null():
    class A(Type):
        title = validators.Number(allow_null=True)

    a = A()
    a.format()


if __name__ == "__main__":
    pytest.main(["test_model.py"])