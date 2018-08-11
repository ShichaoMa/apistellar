import pytest
from star_builder.bases.service import Service, inject
from star_builder.bases.exceptions import Readonly


class A:
    pass


class MyService(Service):

    aaa = inject << A


def test_inject_prop_annotation():
    my_service = MyService()
    assert my_service.resolve.__annotations__["aaa"] == A


def test_inject_return_annotation():
    my_service = MyService()
    assert my_service.resolve.__annotations__["return"] == MyService


def test_assign_value():
    my_service = MyService()
    a = A()
    my_service.resolve(a)
    assert a is my_service.aaa


def test_readonly():
    my_service = MyService()
    a = A()
    my_service.resolve(a)
    with pytest.raises(Readonly):
        my_service.aaa = 1


class B:
    pass


def test_have_resolve():
    class HaveResolveService(Service):
        a = inject << A

        def resolve(self, b: B):
            self.b = b
            return self

    service = HaveResolveService()

    assert "b" in service.resolve.__annotations__
    assert "a" not in service.resolve.__annotations__


def test_empty_inject():
    class EmptyService(Service):
        pass

    service = EmptyService()
    assert service.resolve.__annotations__["return"] == EmptyService
