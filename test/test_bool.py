from star_builder import Type
from star_builder import validators


class A(Type):

    a = validators.Boolean()


class B(Type):
    b = validators.Boolean()
    c = A


def test_coerce():
    a = B(b=1, c={"a": 0})
    a.format(allow_coerce=True)
    assert a.b is True and a.c.a is False