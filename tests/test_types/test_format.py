import uuid
import pytz
import pytest
import datetime

from apistar.exceptions import ValidationError
from apistellar.types import Type, validators
from apistellar.types.formats import DateTimeFormat, install, FORMATS


class Example(Type):
    field1 = validators.DateTime()
    field2 = validators.Time()
    field3 = validators.Date()
    field4 = validators.FormatDateTime()
    field5 = validators.String(format="UUID")


def test_datetime_validate():
    e = Example()
    with pytest.raises(ValidationError):
        e.field1 = "19771010"

    e.field1 = "1977-10-10T10:10:10+08:00"
    delta = datetime.timedelta(hours=8)
    tzinfo = datetime.timezone(delta)
    assert e.field1 == datetime.datetime(1977, 10, 10, 10, 10, 10, tzinfo=tzinfo)
    e.field1 = "1977-10-10T10:10:10-08:00"
    tzinfo = datetime.timezone(-delta)
    assert e.field1 == datetime.datetime(1977, 10, 10, 10, 10, 10,
                                         tzinfo=tzinfo)

    e.field1 = "1977-10-10T10:10:10Z"
    tzinfo = datetime.timezone.utc
    assert e.field1 == datetime.datetime(1977, 10, 10, 10, 10, 10,
                                         tzinfo=tzinfo)
    assert e["field1"] == "1977-10-10T10:10:10Z"
    e.field1 = "1977-10-10T10:10:10"
    assert e.field1 == datetime.datetime(1977, 10, 10, 10, 10, 10)
    assert e["field1"] == "1977-10-10T10:10:10"

    # 这种方式不会format
    e = Example(field1="1111")
    assert e["field1"] == "1111"

    e = Example(field1=None)
    assert e["field1"] is None


def test_time_validate():
    e = Example()
    with pytest.raises(ValidationError):
        e.field2 = "197710"

    e.field2 = "11:11:11"
    assert e.field2 == datetime.time(11, 11, 11)
    assert e["field2"] == "11:11:11"

    # 这种方式不会format
    e = Example(field2="1111")
    assert e["field2"] == "1111"

    e = Example(field2=None)
    assert e["field2"] is None


def test_date_validate():
    e = Example()
    with pytest.raises(ValidationError):
        e.field3 = "19771010"

    e.field3 = "1977-10-10"
    assert e.field3 == datetime.date(1977, 10, 10)
    assert e["field3"] == "1977-10-10"

    # 这种方式不会format
    e = Example(field3="1111")
    assert e["field3"] == "1111"

    e = Example(field3=None)
    assert e["field3"] is None


def test_format_datetime_validate():
    e = Example()
    with pytest.raises(ValidationError):
        e.field4 = "19771010"

    e.field4 = "1970-10-10 10:10:10"
    assert e.field4 == datetime.datetime(1970, 10, 10, 10, 10, 10)
    assert e["field4"] == "1970-10-10 10:10:10"

    # 这种方式不会format
    e = Example(field4="1111")
    assert e["field4"] == "1111"

    e = Example(field4=None)
    assert e["field4"] is None


def test_uuid_validate():
    e = Example()
    e.field5 = "19771010"
    # 不合法的UUID是可以使用的，主要是为了兼容
    assert e.field5 == "19771010"
    id = uuid.uuid4()
    e.field5 = id
    assert e.field5 == id
    assert e["field5"] == str(id)
    e = Example(field5=None)
    assert e["field5"] is None


def test_custom_format():

    install(date_format="%H:%M:%S", tz=pytz.timezone("Asia/Tokyo"))

    class CustomDatetimeFormat(DateTimeFormat):
        name = "custom_datetime"

        def __init__(self, tz=None, date_format="%Y-%m-%d %H:%M:%S", **kwargs):
            super().__init__(**kwargs)
            self.tz = tz
            self.date_format = date_format

        def validate(self, value):
            return datetime.datetime.fromtimestamp(
                datetime.datetime.strptime(value, self.date_format).timestamp(),
                self.tz)

        def to_string(self, value):
            if isinstance(value, datetime):
                return value.strftime(self.date_format)
            return value

    class Example(Type):
        field = validators.String(default="11:11:11", format="custom_datetime")

    e = Example()
    e.format()
    assert e.field.hour == 12


def test_custom_format_set():
    class CustomFormat(object):
        pass

    assert "test" not in FORMATS
    FORMATS["test"] = CustomFormat
    assert "test" in FORMATS


def test_format_field_error_with_field_name():
    e = Example()
    with pytest.raises(ValidationError) as err_info:
        e.field5 = 3

    assert err_info.value.detail["field5"] == 'Must be a string.'


def test_reformat_field_error_with_field_name():
    e = Example(field5=3)
    with pytest.raises(ValidationError) as err_info:
        e.reformat("field5")

    assert err_info.value.detail["field5"] == 'Must be a string.'
