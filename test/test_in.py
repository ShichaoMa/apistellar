from star_builder import Type, validators


class A(Type):
    a = validators.String()


def test_in():
    a = A()
    assert "a" not in a
    a.a = "a"
    assert "a" in a