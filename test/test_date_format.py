from star_builder import Type, validators

import datetime


class A(Type):
    created_at = validators.FormatDateTime(format="%Y-%m-%d%H%M%S", default=datetime.datetime.now)


a = A()
a.format()
#a.created_at = "2018-01-02111111"
print(a.to_json())
