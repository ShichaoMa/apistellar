import os
import pytest

from contextlib import contextmanager
from apistellar.types import PersistentType
from apistellar.persistence import DriverMixin, conn_ignore, get_callargs, proxy


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
            driver = MyDriver()
            try:
                yield proxy(self_or_cls, prop_name="store", prop=driver)
            except Exception as e:
                driver.rollback()
                raise e
            else:
                driver.close()


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
        with super(DynamicTableNameMixin, cls).get_store(
                self_or_cls, **callargs) as self_or_cls:
            driver = DynamicTableNameDriver(
                self_or_cls.DYNAMIC_TABLE.format(**callargs),
                self_or_cls.DYNAMIC_DB.format(**callargs))
        yield proxy(self_or_cls, prop_name="cur", prop=driver)


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
