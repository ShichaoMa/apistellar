import pytest
from os.path import dirname

pytestmark = [pytest.mark.path(dirname(dirname(dirname(__file__))))]
