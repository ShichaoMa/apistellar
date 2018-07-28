import os
import sys
import uvloop
import signal
import asyncio
import logging
import traceback

from toolkit import cache_property
from argparse import ArgumentParser

from apistar import Route
from apistar.http import PathParams, Response
from apistar.server.injector import ASyncInjector
from apistar.server.validation import VALIDATION_COMPONENTS
from apistar.server.asgi import ASGI_COMPONENTS, ASGIReceive, \
    ASGIScope, ASGISend

from . import Solo
from ..bases.components import SettingsComponent, Component
from ..helper import find_children, ArgparseHelper, load_packages, MySelf


class SoloManager(object):
    """
    独立任务程序管理器
    """
    alive = True

    def __init__(self, app_name, current_dir="."):
        os.chdir(current_dir)
        sys.path.insert(0, current_dir)
        sys.modules.pop(app_name, None)
        load_packages(".")
        self.solos = {solo.__name__.lower(): solo
                      for solo in find_children(Solo, False)}
        self.args = self.parse_args()
        SettingsComponent.register_path(self.args.settings)
        initial_components = {
            'scope': ASGIScope,
            'receive': ASGIReceive,
            'send': ASGISend,
            'exc': Exception,
            'app': SoloManager,
            'path_params': PathParams,
            'route': Route,
            'response': Response,
        }
        self.state = {
                'scope': MySelf(),
                'receive': MySelf(),
                'send': MySelf(),
                'exc': None,
                'app': self,
                'path_params': MySelf(),
                'route': MySelf()
            }
        self.injector = ASyncInjector(
            list(ASGI_COMPONENTS + VALIDATION_COMPONENTS) + find_children(Component),
            initial_components)
        self.solo = self.solos[self.args.solo](**vars(self.args))
        self.task = None

    @cache_property
    def logger(self):
        """
        可以选择覆盖这个属性
        :return:
        """
        return logging.getLogger("solo")

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
            self.injector.run_async(
                [self.solo.setup, self.solo.run], dict(self.state)))
        loop.create_task(self.tick(loop))

        self.logger.info(f'Starting worker [{os.getpid()}]')

        loop.run_forever()

    async def tick(self, loop):
        while self.alive:
            if self.task.done():
                break
            for task in self.solo.tasks[:]:
                try:
                    if task.done():
                        rs = task.result()
                        if rs is not None:
                            self.logger.info(rs)
                        self.solo.tasks.remove(task)
                except Exception as e:
                    self.logger.error(f"Error in task: {task} error: {e}")
                    self.solo.tasks.remove(task)

            await asyncio.sleep(1)
        try:
            if self.task.done():
                rs = self.task.result()
                if rs is not None:
                    self.logger.info(rs)
        except Exception as e:
            self.logger.error(
                f"Error in main coroutine, error: {traceback.format_exc()}")

        await self.injector.run_async(
            [self.solo.teardown], dict(self.state))
        self.logger.warning(f"Stopping [{os.getpid()}]")
        loop.stop()

    def handle_exit(self, sig, frame):
        self.alive = False
        self.logger.warning(
            "Received signal {}. Shutting down.".format(sig.name))

    def parse_args(self):
        base_parser = ArgumentParser(
            description=self.__class__.__doc__, add_help=False)
        base_parser.add_argument(
            "--settings", help="配置模块路径.", default="settings")

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