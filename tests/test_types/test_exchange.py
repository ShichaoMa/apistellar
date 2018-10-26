import pytest

from apistellar.types import validators, Type
from apistar.exceptions import ValidationError

from enum import Enum


class B(Enum):
    a = "export"
    b = "extract"


class A(Type):
    field = validators.Exchange(B)


def test_exchange():
    a = A()
    a.field = "export"


def test_exchange_error():
    a = A()
    with pytest.raises(ValidationError):
        a.field = "333"


