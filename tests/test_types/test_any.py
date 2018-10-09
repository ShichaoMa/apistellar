from factories import TypeTestBase


class AnyTest(TypeTestBase):
    _type = "Any"


class TestAny(AnyTest):

    def test_any(self):
        e = self.Example()
        e.field = complex(1, 2)
        assert e.field == complex(1, 2)
