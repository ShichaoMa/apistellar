import asyncio
from star_builder import inject
from star_builder.bases.model_factory import ModelFactory


def test_product1():
    class B:
        pass

    class A:
        a = inject << B

    class AFactory(ModelFactory):
        model = A

        async def product(self, b: B) -> A:
            print(b)
            a = A()
            return a

    factory = AFactory()
    loop = asyncio.get_event_loop()
    a = loop.run_until_complete(factory.resolve(3, 5))
    assert a.a == 3


def test_product2():
    class B:
        pass

    class A:
        a = inject << B

    class AFactory(ModelFactory):
        model = A

        async def product(self) -> A:
            a = A()
            return a

    factory = AFactory()
    loop = asyncio.get_event_loop()
    a = loop.run_until_complete(factory.resolve(5))
    assert a.a == 5


def test_product3():
    class B:
        pass

    class A:
        b = inject << B

    class AFactory(ModelFactory):
        model = A

        async def product(self, b: B) -> A:
            print(b)
            a = A()
            return a

    factory = AFactory()
    loop = asyncio.get_event_loop()
    a = loop.run_until_complete(factory.resolve(5))
    assert a.b == 5


def test_product4():
    class B:
        pass

    class A:
        b = inject << B

    import typing

    class AFactory(ModelFactory):
        model = A

        async def product(self, b: B) -> A:
            print(b)
            a = A()
            return a

    class AListFactory(ModelFactory):
        model = A

        async def product(self, b: B) -> typing.List[A]:
            print(b)
            return [A(), A()]

    factory = AFactory()
    loop = asyncio.get_event_loop()
    a = loop.run_until_complete(factory.resolve(5))
    assert a.b == 5

    factory = AListFactory()
    a_list = loop.run_until_complete(factory.resolve(7))
    assert all(a.b == 7 for a in a_list)


def test_product5():
    """
    product的默认参数会覆盖掉model中定义的默认参数
    :return:
    """
    class B:
        pass

    class A:
        a = inject(default=10) << B

    class AFactory(ModelFactory):
        model = A

        async def product(self, a: B=19, c: A=10) -> A:
            print(a)
            a = A()
            return a

    factory = AFactory()
    loop = asyncio.get_event_loop()
    a = loop.run_until_complete(factory.resolve())
    assert a.a == 19
    a = loop.run_until_complete(factory.resolve(12))
    assert a.a == 12


def test_product6():
    """
    product的默认参数会覆盖掉model中定义的默认参数
    :return:
    """
    class B:
        pass

    class A:
       pass

    class AFactory(ModelFactory):
        model = A

        async def product(self, a: B=19, c: A=10) -> A:
            print(a)
            a = A()
            return a

    factory = AFactory()
    loop = asyncio.get_event_loop()
    a = loop.run_until_complete(factory.resolve())


def test_product7():
    """
    model发生了继承时
    :return:
    """
    class B:
        pass

    class A:
        b = inject << B

    class C(A):
        pass

    class CFactory(ModelFactory):
        model = C

        async def product(self) -> C:
            c = C()
            assert c.b == 3
            return c

    factory = CFactory()
    loop = asyncio.get_event_loop()
    a = loop.run_until_complete(factory.resolve(3))


if __name__ == "__main__":
    import pytest
    pytest.main(["test_model_inject.py"])
