import os
import sys
import asyncio
import inspect

from apistar import Route
from IPython import embed
from IPython.core import formatters

from apistellar.bases.manager import Manager
from apistellar.helper import get_real_method

from .mocker import Mocker

# bugfix
formatters.get_real_method = get_real_method


class ConsoleManager(Manager):

    def __init__(self):
        self.initialize(os.getcwd())
        self.finalize()
        self.mock_keys = list()

    async def resolve(self, type):
        def wrapper(arg: type):
            return arg

        route = Route("/", "post", wrapper)
        state = dict(self.state)
        state["route"] = route
        return await self.injector.run_async([wrapper], state)

    def mock(self, mocker):
        """
        构建测试数据
        :param mocker: Mocker对象
        :return:
        """
        for type, val, param_name in mocker:
            param_name = param_name or type.__class__.__name__.lower()
            parameter = inspect.Parameter(
                param_name, inspect._POSITIONAL_OR_KEYWORD, annotation=type)
            for component in self.injector.components:
                if component.can_handle_parameter(parameter):
                    identity = component.identity(parameter)
                    break
            else:
                raise RuntimeError(f"Type: {type} cannot be mocked! ")

            self.mock_keys.append(identity)
            self.state[identity] = val
            self.injector.initial[identity] = type

    @staticmethod
    def _await(awaitable):
        """
        模拟await关键字
        :param awaitable:
        :return:
        """
        loop = asyncio.get_event_loop()
        task = loop.create_task(awaitable.__await__())
        loop.run_until_complete(task)
        return task.result()

    def clear(self):
        """
        清除mock数据
        :return:
        """
        for key in self.mock_keys:
            del self.state[key]
            del self.injector.initial[key]

    def start(self):
        if sys.version_info < (3, 7, 0):
            locals()["await"] = self._await
        else:
            locals()["_await"] = self._await
        mock = self.mock

        def inject(cls):
            return self._await(self.resolve(cls))
            #return getattr(self, cls)

        embed()


def main():
    ConsoleManager().start()
