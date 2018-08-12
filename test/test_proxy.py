from star_builder import Type, validators


class Subject(Type):
    id = validators.String(allow_null=True)


class Student(Type):
    name = validators.String()
    subject = validators.Proxy(Subject, allow_null=True)


class Teacher(Type):
    name = validators.String()
    subject = validators.Proxy(Subject, default=dict)


def test_proxy1():
    a = Student({"name": "tom", "subject": {"id": "10"}})
    assert a.name == "tom"


def test_proxy2():
    b = Student(name="tom")
    b.format()
    assert b.subject is None


def test_proxy3():
    c = Teacher(name="john")
    c.format()
    assert isinstance(c.subject, Subject)
    assert c.subject.id is None
