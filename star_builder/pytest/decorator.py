"""
未完成
"""
import inspect
import warnings


def test_warn(message):
    warnings.warn(message)


class Test:
    pass


class Mock(object):

    def __init__(self, datas, chain=0):
        self.chain = chain
        self.datas = datas

    def __getattr__(self, item):
        return self.__class__(self.datas, self.chain + 1)

    def __getitem__(self, item):
        return self.__class__(self.datas, self.chain + 1)

    def __call__(self, *args, **kwargs):
        return self.__class__(self.datas, self.chain + 1)

    def __bool__(self):
        return False

    def __str__(self):
        return ""

    def __radd__(self, obj):
        return obj + type(obj)(self)

    def __iter__(self):
        return iter([])

    def __await__(self):
        loop = get_event_loop()
        future = loop.create_future()
        future.set_result(self)
        return future.__await__()

    __repr__ = __str__


class ModelTest(Test):

    __slots__ = ("input", "output", "state")

    def __init__(self, input=None, output=None, state=None, mock_self=None, ):
        self.input = input or {}
        self.output = output
        self.state = state or {}

    def __call__(self, func):
        for name, param in inspect.signature(func).parameters.items():
            if param.kind == inspect._POSITIONAL_OR_KEYWORD and \
                    name not in self.input:
                test_warn(f"Test: positional arg: {name} not found in input.")
        func.__dict__.setdefault("test_case", []).append(self)
        return func


class FactoryTest(Test):
    pass


class ControllerTest(Test):
    pass


class ServiceTest(Test):
    pass