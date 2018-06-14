import os
import sys
import json
import uvloop
import signal
import asyncio
import logging

from argparse import ArgumentParser
from toolkit import cache_property

from . import Solo
from ..bases.components import SettingsComponent
from ..helper import find_children, ArgparseHelper, load_packages


class SoloManager(object):
    """
    独立任务程序管理器
    """
    alive = True

    def __init__(self):
        load_packages(".")
        self.solos = {solo.__name__.lower(): solo
                      for solo in find_children(Solo, False)}
        self.args = self.parse_args()
        SettingsComponent.register_path(self.args.settings)
        self.solo = self.solos[self.args.solo](**vars(self.args))
        self.task = None

    @cache_property
    def logger(self):
        """
        可以选择覆盖这个属性
        :return:
        """
        logger = logging.getLogger("solo")
        logger.setLevel(10)
        logger.addHandler(logging.StreamHandler(sys.stdout))
        return logger

    def start(self):
        asyncio.get_event_loop().close()
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

        loop = asyncio.get_event_loop()
        loop.add_signal_handler(signal.SIGQUIT, self.handle_exit,
                                signal.SIGQUIT, None)
        loop.add_signal_handler(signal.SIGTERM, self.handle_exit,
                                signal.SIGTERM, None)
        loop.add_signal_handler(signal.SIGINT, self.handle_exit,
                                signal.SIGINT, None)
        loop.add_signal_handler(signal.SIGABRT, self.handle_exit,
                                signal.SIGABRT, None)

        self.task = loop.create_task(
            self.solo.injector.run_async(
                [self.solo.setup, self.solo.run], dict(self.solo.scope)))
        loop.create_task(self.tick(loop))

        self.logger.info(f'Starting worker [{os.getpid()}]')

        loop.run_forever()

    async def tick(self, loop):
        while self.alive:
            if self.task.done():
                break
            await asyncio.sleep(1)
        await self.solo.injector.run_async(
            [self.solo.teardown], dict(self.solo.scope))
        self.logger.warning(f"Stopping [{os.getpid()}]")
        loop.stop()
        for task in self.solo.tasks:
            try:
                self.logger.info(task.result())
            except Exception as e:
                self.logger.error(e)

    def handle_exit(self, sig, frame):
        self.alive = False
        self.logger.warning(
            "Received signal {}. Shutting down.".format(sig.name))

    def parse_args(self):
        base_parser = ArgumentParser(
            description=self.__class__.__doc__, add_help=False)
        base_parser.add_argument(
            "--settings", help="配置模块路径.", default="settings")
        base_parser.add_argument(
            "-s", "--scope", help="配置全局注入值. eg: '{\"name\": \"tom\"}'")
        base_parser.add_argument(
            "-i", "--initial", help="配置初始化注入类型. eg: '{\"name\": \"str\"}'")

        parser = ArgumentParser(description="独立任务程序构建工具", add_help=False)
        parser.add_argument(
            '-h', '--help', action=ArgparseHelper, help='显示帮助信息并退出.')
        sub_parsers = parser.add_subparsers(dest="solo", help="创建独立任务服务类型.")

        for name, solo in self.solos.items():
            sub_parser = sub_parsers.add_parser(
                name.lower(), parents=[base_parser], help=solo.__doc__)
            solo.enrich_parser(sub_parser)
        # 当不提供参数时，len(sys.argv) == 1, 不会打印帮助，需要手动打印
        # add_subparsers无法指定required=True, 这是argparse的bug。
        if len(sys.argv) < 2:
            parser.print_help()
            exit(1)
        return parser.parse_args()