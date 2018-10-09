from apistellar.types import Type, validators


class TypeTestBase(object):
    _type = ""
    args = tuple()
    kwargs = dict()

    @classmethod
    def setup_class(cls):
        cls.Example = cls.gen_class(cls._type, *cls.args, **cls.kwargs)

    @classmethod
    def teardown_class(cls):
        del cls.Example

    @staticmethod
    def gen_class(field_type, *args, **kwargs):
        class Example(Type):
            field = getattr(validators, field_type)(*args, **kwargs)
        return Example


class NestedTypeTestBase(TypeTestBase):
    nested_field_type = ""

    @classmethod
    def nested(cls):
        return TypeTestBase.gen_class(cls.nested_field_type)

    @classmethod
    def setup_class(cls):
        cls.Example = cls.gen_class(cls._type, cls.nested(), *cls.args, **cls.kwargs)
