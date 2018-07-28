from star_builder import Type
from star_builder import validators


class A(Type):

    a = validators.Boolean()


class B(Type):
    b = validators.Boolean()
    c = A

a = B(b=0, c={"a": 0})

a.format(allow_coerce=True)
print(a)