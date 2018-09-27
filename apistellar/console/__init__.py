import os
import sys
import asyncio
import inspect

from IPython import embed
from IPython.core import formatters
from toolkit import cache_property

from .mocker import Mocker
from ..bases.manager import Manager
from ..helper import get_real_method

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

        return await self.injector.run_async([wrapper], dict(self.state))

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

    def __getattr__(self, item):
        assert item in self.beans, f"{item} cannot inject!"
        beans = self.beans[item]
        if len(beans) == 1:
            bean, _ = beans[0]
        else:
            i = input("Same bean name: {}: ".format(
                ", ".join(f"({index+1}) of {module}" for index, (_, module)
                                                in enumerate(beans))))
            bean = beans[int(i) - 1][0]
        return self.await(self.resolve(bean))

    def __getitem__(self, item):
        return self.__getattr__(item)

    @cache_property
    def beans(self):
        beans = dict()
        for component in self.components:
            type = component.resolve.__annotations__["return"]
            beans.setdefault(type.__name__, []).append((type, type.__module__))
        return beans

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
            await = self._await
        else:
            _await = self._await
        mock = self.mock

        def inject(class_name):
            return getattr(self, class_name)

        embed()


def main():
    ConsoleManager().start()
