from apistellar.types.formats import DateTimeFormat, install
from apistellar import Type
from apistellar.types.validators import String, DateTime, Proxy
from datetime import datetime
import pytz


def now():
    return datetime.now().strftime("%Y/%m/%d %H:%M:%S")


install(date_format="%Y/%m/%d %H:%M:%S", tz=pytz.timezone("Asia/Tokyo"))


class CustomDatetimeFormat(DateTimeFormat):
    name = "custom_datetime"

    def __init__(self, tz=None, date_format="%Y-%m-%d %H:%M:%S", **kwargs):
        super().__init__( **kwargs)
        self.tz = tz
        self.date_format = date_format

    def validate(self, value):
        return datetime.fromtimestamp(
            datetime.strptime(value, self.date_format).timestamp(), self.tz)

    def to_string(self, value):
        if isinstance(value, datetime):
            return value.strftime(self.date_format)
        return value


class B(Type):
    a = String(allow_null=True)
    b = String(default="")


class A(Type):

    created_at = String(default=now, format="custom_datetime")
    #updated_at = DateTime(default=now)
    b = Proxy(B, default=B)


def test_format():
    a = A()
    a.format()
    assert a.created_at.hour == datetime.now().hour + 1