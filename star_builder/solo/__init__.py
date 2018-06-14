import json

from toolkit import load_class
from abc import ABC, abstractmethod
from apistar.server.injector import ASyncInjector
from ..helper import find_children


class Solo(ABC):
    """
    独立任务程序子任务接口定义
    """
    def __init__(self, initial, scope, **kwargs):
        if initial:
            initial = {name: __builtins__.get("int") or load_class(cls)
                       for name, cls in json.loads(initial).items()}
        else:
            initial = {}

        if scope:
            self.scope = json.loads(scope)
        else:
            self.scope = {}

        self.injector = ASyncInjector(find_children(), initial)
        self.tasks = []

    @abstractmethod
    async def setup(self, *args, **kwargs):
        """
        任务初始化
        :param args:
        :param kwargs:
        :return:
        """

    @abstractmethod
    async def teardown(self, *args, **kwargs):
        """
        资源回收
        :param args:
        :param kwargs:
        :return:
        """

    @abstractmethod
    async def run(self, *args, **kwargs):
        """
        任务执行
        :param args:
        :param kwargs:
        :return:
        """

    @classmethod
    def enrich_parser(cls, sub_parser):
        """
        自定义命令行参数
        :param sub_parser:
        :return:
        """