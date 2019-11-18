import pytest

from apistar.exceptions import ValidationError

from factories import TypeTestBase


class FormatDateTimeTest(TypeTestBase):
    _type = "FormatDateTime"


class TestFormat(FormatDateTimeTest):
    kwargs = {"format": "%Y-%m-%d", "default": "2018-03-04"}

    def test_format(self):
        e = self.Example()
        e.format()
        assert e.field.year == 2018
        assert e.field.month == 3
        assert e.field.day == 4

    def test_format_failed(self):
        with pytest.raises(ValidationError) as exc_info:
            e = self.gen_class(self._type, format="%Y-%m-%d", default="2018")()
            e.format()

        assert exc_info.value.args[0]["field"] == "Must be a valid format_datetime."
