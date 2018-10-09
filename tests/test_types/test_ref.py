from factories import TypeTestBase


class RefTest(TypeTestBase):
    _type = "Ref"

    @classmethod
    def setup_class(cls):
        cls.Example = cls.gen_class(cls._type, "Example", *cls.args, **cls.kwargs)


class TestRef(RefTest):
    kwargs = {"allow_null": True}

    def test_ref(self):
        e = self.Example(field={"field": {}})
        e.format()
        assert e.field.field.field is None

