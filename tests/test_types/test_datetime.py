import datetime

from apistellar.types import Type, validators, formats


class Example(Type):
    field1 = validators.DateTime()
    field2 = validators.Date()
    field3 = validators.Time()


class TestDatetime(object):

    def test_native(self):
        e = Example()
        e.field1 = datetime.datetime.now()
        assert isinstance(e.field1, datetime.datetime)
        assert formats.DATETIME_REGEX.search(e["field1"])

    def test_string(self):
        e = Example()
        e.field1 = "2018-02-02 11:11:11"
        assert isinstance(e.field1, datetime.datetime)
        assert formats.DATETIME_REGEX.search(e["field1"])


class TestDate(object):

    def test_native(self):
        e = Example()
        e.field2 = datetime.date(year=2018, month=10, day=5)
        assert isinstance(e.field2, datetime.date)
        assert formats.DATE_REGEX.search(e["field2"])

    def test_string(self):
        e = Example()
        e.field2 = "2018-02-02"
        assert isinstance(e.field2, datetime.date)
        assert formats.DATE_REGEX.search(e["field2"])


class TestTime(object):

    def test_native(self):
        e = Example()
        e.field3 = datetime.time(hour=11, minute=11, second=11)
        assert isinstance(e.field3, datetime.time)
        assert formats.TIME_REGEX.search(e["field3"])

    def test_string(self):
        e = Example()
        e.field3 = "11:11:11"
        assert isinstance(e.field3, datetime.time)
        assert formats.TIME_REGEX.search(e["field3"])

