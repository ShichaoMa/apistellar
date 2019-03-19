import os
import pytest
import asyncio

from apistellar.types import PersistentType
from apistellar.persistence import DriverMixin, conn_ignore, \
    get_callargs, proxy, contextmanager, conn_debug, conn_asyncgen, \
    conn_asyncable, conn_proxy_driver_names


class MyDriver(object):

    def __init__(self):
        self.state = "init"

    def find_one(self):
        if os.getenv("TEST_FLAG") == "error":
            raise RuntimeError(self)
        else:
            return self

    def rollback(self):
        self.state = "rollback"

    def close(self):
        self.state = "close"


class MyDriverMixin(DriverMixin):

    store = None  # type: MyDriver

    @classmethod
    @contextmanager
    def get_store(cls, self_or_cls, **callargs):
        with super(MyDriverMixin, cls).get_store(
                self_or_cls, **callargs) as self_or_cls:
            prop_name = "store"
            if self_or_cls._need_proxy(prop_name):
                driver = MyDriver()
                try:
                     yield proxy(self_or_cls, prop_name=prop_name, prop=driver)
                except Exception as e:
                    driver.rollback()
                    raise e
                else:
                    driver.close()
            else:
                yield self_or_cls


def custom_wrapper(func):
    d = 1

    def inner(*args, **kwargs):
        return func(*args, d=d, **kwargs)
    return inner


class Model(PersistentType, MyDriverMixin):

    def __init__(self, *args, **kwargs):
        super(Model, self).__init__(*args, **kwargs)
        # 双下方法不会被加上store
        assert self.store is None

    def find_one(self):
        return self.store.find_one()

    def find(self):
        return self.find_one()

    def find_one_with_args(self, a, b, *args, c=3):
        return a, b, args, c

    def find_one_with_kwonly_args(self, a, b, *, c=3):
        return a, b, c

    async def find_one_async(self):
        return self.store.find_one()

    @classmethod
    def find_one_classmethod(cls):
        return cls.store.find_one()

    @conn_ignore
    def find_one_ignore_store(self):
        assert self.store is None

    @conn_debug(lambda: True)
    def find_one_debug_true(self):
        assert self.store is None

    @conn_debug(lambda: False)
    def find_one_debug_false(self):
        assert self.store is None

    @custom_wrapper
    def find_one_with_wrapper(self, a, b, c=3, d=4):
        self.store.find_one()
        return a, b, c, d


class DynamicTableNameDriver(object):
    def __init__(self, table, db, *args, **kwargs):
        self.table = table
        self.db = db
        super(DynamicTableNameDriver, self).__init__(*args, **kwargs)

    def find_one(self):
        return self.table, self.db


class DynamicTableNameMixin(DriverMixin):
    cur = None # type: DynamicTableNameDriver
    DYNAMIC_TABLE = NotImplemented
    DYNAMIC_DB = NotImplemented

    @classmethod
    @contextmanager
    def get_store(cls, self_or_cls, **callargs):
        prop_name = "cur"
        with super(DynamicTableNameMixin, cls).get_store(
                self_or_cls, **callargs) as self_or_cls:
            if self_or_cls._need_proxy(prop_name):
                driver = DynamicTableNameDriver(
                    self_or_cls.DYNAMIC_TABLE.format(**callargs),
                    self_or_cls.DYNAMIC_DB.format(**callargs))
                self_or_cls = proxy(self_or_cls, prop_name=prop_name, prop=driver)
        yield self_or_cls


class DynamicTableNameModel(PersistentType, DynamicTableNameMixin):
    DYNAMIC_TABLE = "test_table_{partition}"
    DYNAMIC_DB = "test_db_{partition}"

    def find_one(self, partition):
        return self.cur.find_one()

    def get_table(self, partition):
        return self.DYNAMIC_TABLE


class MultiDriverModel(PersistentType, DynamicTableNameMixin, MyDriverMixin):
    DYNAMIC_TABLE = "test_table_{partition}"
    DYNAMIC_DB = "test_db_{partition}"

    def find_one(self, partition):
        table1, db1 = self.cur.find_one()
        driver = self.store.find_one()
        return table1, db1, driver

    @conn_proxy_driver_names(("cur", ))
    def find_one_ignore_store(self, partition):
        assert self.store is None
        return self.cur.find_one()


class AsyncDriverMixin(MyDriverMixin):

    @classmethod
    @contextmanager
    async def get_store(cls, self_or_cls, **callargs):
        with super().get_store(self_or_cls, **callargs) as self_or_cls:
            yield proxy(self_or_cls, 111, "a")


class AsyncDriverModel(PersistentType, AsyncDriverMixin):
    async def find_one(self):
        driver = self.store.find_one()
        return driver, self.a

    @conn_asyncable
    def find_one_async_with_future(self):
        feature = asyncio.get_event_loop().create_future()
        feature.set_result(self.store.find_one())
        return feature

    @conn_asyncgen
    def async_with_asyncgen(self):
        async def gen():
            yield 1
        return gen()

    def find_one_sync(self):
        driver = self.store.find_one()
        return driver


class TestPersistence(object):

    def test_normal(self):
         model = Model()
         store = model.find_one()
         assert isinstance(store, MyDriver)
         assert store.state == "close"
         assert model.store is None

    def test_call_method(self):
        model = Model()
        store = model.find()
        assert isinstance(store, MyDriver)
        assert store.state == "close"
        assert model.store is None

    @pytest.mark.asyncio
    async def test_async(self):
         model = Model()
         store = await model.find_one_async()
         assert isinstance(store, MyDriver)
         assert store.state == "close"
         assert model.store is None

    def test_classmethod(self):
         model = Model()
         store = model.find_one_classmethod()
         assert isinstance(store, MyDriver)
         assert store.state == "close"
         assert model.store is None

    def test_find_one_ignore_store(self):
        model = Model()
        model.find_one_ignore_store()

    def test_find_one_debug_store(self):
        model = Model()
        model.find_one_debug_true()

    def test_find_one_not_debug_store(self):
        model = Model()
        with pytest.raises(AssertionError):
            model.find_one_debug_false()

    def test_find_one_with_wrapper(self):
        model = Model()
        assert model.find_one_with_wrapper(1, 2, 5) == (1, 2, 5, 1)

    @pytest.mark.env(TEST_FLAG="error")
    def test_error(self):
        model = Model()
        with pytest.raises(RuntimeError) as exc_info:
            model.find_one()

        assert exc_info.value.args[0].state == "rollback"

    def test_with_args(self):
        model = Model()
        store = model.find_one_with_args(1, 5, 8, 7)
        assert store == (1, 5, (8, 7), 3)

    def test_with_kwonly_args(self):
        model = Model()
        store = model.find_one_with_kwonly_args(1, 5)
        assert store == (1, 5, 3)

    def test_with_dynamic_table_name(self):
        assert DynamicTableNameModel().find_one(2) == ("test_table_2", "test_db_2")

    def test_get_prop(self):
        assert DynamicTableNameModel().get_table(2) == "test_table_{partition}"

    def test_get_callargs(self):
        def fun(cls, query, **kwargs):
            pass
        callargs = get_callargs(fun, "111",
                                *({'primary_key': '7', 'second_level_kid': '6',
                                  'node_id': '2', 'first_level_kid': '5',
                                  'patient_sn': '3'},),
                                **{'desease_id': 'test'})
        assert callargs["desease_id"] == "test"

    def test_multi_driver(self):
        table, db, driver = MultiDriverModel().find_one(2)
        assert (table, db) == ("test_table_2", "test_db_2")
        assert isinstance(driver, MyDriver)

    def test_multi_driver_with_specify_driver_names(self):
        table, db = MultiDriverModel().find_one_ignore_store(2)
        assert (table, db) == ("test_table_2", "test_db_2")

    @pytest.mark.asyncio
    async def test_async_driver_mixin(self):
        driver, a = await AsyncDriverModel().find_one()
        assert a == 111
        assert isinstance(driver, MyDriver)

    @pytest.mark.asyncio
    async def test_async_driver_with_future(self):
        driver = await AsyncDriverModel().find_one_async_with_future()
        assert isinstance(driver, MyDriver)

    @pytest.mark.asyncio
    async def test_async_driver_with_asyncgen(self):
        async for i in AsyncDriverModel().async_with_asyncgen():
            assert i == 1

    def test_async_driver_mixin_with_sync_method(self):
        driver = AsyncDriverModel().find_one_sync()
        assert isinstance(driver, MyDriver)
