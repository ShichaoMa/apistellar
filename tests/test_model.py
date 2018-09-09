import pytest

from apistellar import Type, validators
from apistar.validators import ValidationError


@pytest.fixture()
def model():
    class A(Type):
        title = validators.Number(maximum=1024)
    return A


def test_model1(model):
    a = model()
    with pytest.raises(ValidationError):
        a.title = 12345


if __name__ == "__main__":
    pytest.main(["test_model.py"])