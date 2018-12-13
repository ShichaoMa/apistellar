import pytest

from apistellar.bases.entities import SettingsMixin


class A(SettingsMixin):
    pass


class TestSettingsMixin(object):
    def test_settings_get(self):
        a = A()
        assert a.settings.get("A") == 1

    @pytest.mark.env(A=2)
    def test_settings_overwrite(self):
        a = A()
        assert a.settings.get_int("A") == 2