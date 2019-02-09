import asyncio
from apistellar import inject
from apistellar.bases.model_factory import ModelFactory


class TestModelFactory(object):

    def test_product_with_args_and_model_with_inject(self):
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

    def test_product_without_args_and_model_with_inject(self):
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

    def test_product_and_model_with_same_args_inject(self):
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

    def test_every_product_change_model_prop_for_earch(self):
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

    def test_product_and_inject_with_default(self):
        """
        product的默认参数会覆盖掉model中定义的默认参数

        :return:
        """
        class B:
            pass

        class A:
            a = inject(default=10) << B
            b = inject(default=11) << B

        class AFactory(ModelFactory):
            model = A

            async def product(self, a: B=19, c: A=10) -> A:
                print(a)
                a = A()
                return a

        factory = AFactory()
        loop = asyncio.get_event_loop()
        a = loop.run_until_complete(factory.resolve())
        # 未传参数，使用product的默认值
        assert a.a == 19
        a = loop.run_until_complete(factory.resolve(12))
        assert a.a == 12
        # product没有这个参数或者没有默认值时，使用inject的默认参数
        assert a.b == 11

    def test_product_with_model_inherit(self):
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

    def test_inject_idempotent(self):
        """
        测试上一次注入不会影响当前注入结果
        :return:
        """
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
        a = loop.run_until_complete(factory.resolve(4, 6))
        assert a.a == 4
