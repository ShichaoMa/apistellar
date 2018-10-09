import pytest

from apistellar.types import Type, validators


@pytest.fixture(scope="session")
def gen_class():
    def gen(field_type, *args, **kwargs):
        class Example(Type):
            field = getattr(validators, field_type)(*args, **kwargs)
        return Example
    return gen
