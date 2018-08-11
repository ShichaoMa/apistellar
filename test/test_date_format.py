import datetime

from star_builder import Type, validators


class A(Type):
    created_at = validators.FormatDateTime(format="%Y-%m-%d%H%M%S", default=datetime.datetime.now)


def test_date_format():
    a = A()
    a.format()
    a.created_at = "2018-01-02111111"
    assert a.created_at == datetime.datetime(year=2018, month=1, day=2, hour=11, minute=11, second=11)
