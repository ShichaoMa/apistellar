import pytest

from apistellar import Service, inject
from apistellar.bases.exceptions import Readonly


class A:
    pass


class B:
    pass


class MyService(Service):

    aaa = inject << A


class TestService(object):

    def test_inject_prop_annotation(self):
        my_service = MyService()
        assert my_service.resolve.__annotations__["aaa"] == A

    def test_inject_return_annotation(self):
        my_service = MyService()
        assert my_service.resolve.__annotations__["return"] == MyService

    def test_assign_value(self):
        my_service = MyService()
        a = A()
        my_service = my_service.resolve(a)
        assert a is my_service.aaa

    def test_readonly(self):
        my_service = MyService()
        a = A()
        my_service = my_service.resolve(a)
        with pytest.raises(Readonly):
            my_service.aaa = 1

    def test_have_resolve(self):
        class HaveResolveService(Service):
            a = inject << A

            def resolve(self, b: B):
                self.b = b
                return self

        service = HaveResolveService()

        assert "b" in service.resolve.__annotations__
        assert "a" not in service.resolve.__annotations__

    def test_empty_inject(self):
        class EmptyService(Service):
            pass

        service = EmptyService()
        assert service.resolve.__annotations__["return"] == EmptyService

    def test_default(self):
        class DefaultService(Service):
            a = inject(default=3) << A

        service = DefaultService()
        service = service.resolve()
        assert service.a == 3
        service = service.resolve(2)
        assert service.a == 2

    def test_inherit(self):
        class Father(Service):
            a = inject << A

        class Child(Father):
            b = inject << B

        service = Child()
        assert service.resolve.__annotations__["return"] == Child
        assert service.resolve.__annotations__["a"] == A
        assert service.resolve.__annotations__["b"] == B
        service = service.resolve(3, 6)
        assert service.a == 3
        assert service.b == 6

    def test_inherit_override(self):
        class Father(Service):
            a = inject << A

        class Child(Father):
            a = inject << A

        service = Child()
        assert service.resolve.__annotations__["return"] == Child
        assert service.resolve.__annotations__["a"] == A
        service = service.resolve(3)

    def test_inherit_override_with_resolve(self):
        class Father(Service):
            def resolve(self, b: B, a: A):
                print(a)
                return self

        class Child(Father):
            c = inject << B
            a = inject << A

        service = Child()
        assert service.resolve.__annotations__["return"] == Child
        assert service.resolve.__annotations__["a"] == A
        service = service.resolve(4, 3, 3)

    def test_inherit_same_name_with_different_type(self):
        class Father(Service):
            a = inject << A

        class Child(Father):
            a = inject << B

        service = Child()
        assert service.resolve.__annotations__["return"] == Child
        assert service.resolve.__annotations__["a"] == B
        assert service.resolve.__annotations__["qwertrewq_a"] == A
        service = service.resolve(3, 5)
        assert service.a == 5

    def test_inherit_same_name_with_different_type_resove_exists(self):
        class Father(Service):
            def resolve(self, a: A):
                print(a)
                return self

        class Child(Father):
            a = inject << B

        service = Child()
        assert service.resolve.__annotations__["return"] == Child
        assert service.resolve.__annotations__["a"] == B
        assert service.resolve.__annotations__["qwertrewq_a"] == A
        service = service.resolve(3, 5)
        assert service.a == 5

    def test_inherit_father_with_nomal_default_and_child_inject(self):
        """
        a: int=10不会生效，在子类中的定义会无视父类的参数列表

        :return:
        """
        class Father(Service):
            def resolve(self, b: B, a: int=10):
                print(a)
                return self

        class Child(Father):
            c = inject << B
            a = inject << A

        service = Child()
        assert service.resolve.__annotations__["return"] == Child
        assert service.resolve.__annotations__["a"] == A
        service = service.resolve(4, 3, 7)
        assert service.c == 7
        assert service.a == 3
