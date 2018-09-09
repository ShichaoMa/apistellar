import pytest
from apistellar import validators, Type


def test_array1():
    class A(Type):
        field = validators.Array()
    a = A()
    a.field = [3]
    a.field = ["a"]
    a.format()


pytest.main([__file__])