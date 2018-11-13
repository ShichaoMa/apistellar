import os
import pytest

from contextlib import contextmanager
from apistellar.types import PersistentType
from apistellar.persistence import DriverMixin, conn_ignore


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


    @classmethod
    @contextmanager
    def get_store(cls, **callargs):
        driver = MyDriver()
        try:
            yield driver
        except Exception as e:
            driver.rollback()
            raise e
        else:
            driver.close()


def wrapper(func):
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

    def find_one_with_args(self, a, b, *args, c=3):
        return a, b, args, c

    async def find_one_async(self):
        return self.store.find_one()

    @classmethod
    def find_one_classmethod(cls):
        return cls.store.find_one()

    @conn_ignore
    def find_one_ignore_store(self):
        assert self.store is None

    @wrapper
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
    TABLE = "test_table_{partition}"
    DB = "test_db_{partition}"
    conn_name = "cur"

    @classmethod
    @contextmanager
    def get_store(cls, **callargs):
        yield DynamicTableNameDriver(
            cls.TABLE.format(**callargs), cls.DB.format(**callargs))


class DynamicTableNameModel(PersistentType, DynamicTableNameMixin):

    def find_one(self, partition):
        return self.cur.find_one()

    def get_table(self, partition):
        return self.TABLE


class TestPersistence(object):

    def test_normal(self):
         model = Model()
         store = model.find_one()
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

    def test_with_dynamic_table_name(self):
        assert DynamicTableNameModel().find_one(2) == ("test_table_2", "test_db_2")

    def test_get_prop(self):
        assert DynamicTableNameModel().get_table(2) == "test_table_{partition}"
