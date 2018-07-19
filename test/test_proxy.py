from star_builder import Type, validators


class Subject(Type):
    id = validators.String(allow_null=True)


class Student(Type):
    name = validators.String()
    subject = validators.Proxy(Subject, allow_null=True)


class Teacher(Type):
    name = validators.String()
    subject = validators.Proxy(Subject, default=dict)


a = Student({"name": "tom", "subject": {"id": "10"}})

print(a)

a.format()
print(a)

b = Student(name="tom")
print(b)
b.format()
print(b)

c = Teacher(name="john")
print(c)
c.format()
print(c)

d = Teacher(b.to_dict())
print(d)
d.format()
print(d)