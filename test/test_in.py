from star_builder import Type, validators


class A(Type):
    a = validators.String()

a = A()

print("a" in a)