# -*- coding:utf-8 -*-
import os
import sys

from abc import ABC, abstractmethod
from contextlib import contextmanager

from toolkit import cache_property, load

from apistellar.bases.controller import Controller
from apistellar.helper import load_packages, routing

from .parser import LogParser


class Painter(ABC):
    """
    用来处理routes并生成描述信息
    """
    routes = None

    def __init__(self, current_dir):
        self.current_dir = current_dir

    @cache_property
    def routes(self):
        """
        获取所有routes
        :return:
        """
        # 这一步是为了将settings.py所以目录加入可搜索路径
        sys.path.insert(0, self.current_dir)
        self.current_dir, app_name = os.path.split(self.current_dir.rstrip("/"))
        sys.path.insert(0, self.current_dir)

        load_packages(self.current_dir, app_name)
        include = routing(Controller)
        routes = [include] if include else []
        return routes

    @abstractmethod
    def paint(self):
        """
        遍历routes渲染描述信息
        :return:
        """


class LogPainter(Painter):
    """
    打印route的简单信息，如日志等
    """

    def __init__(self, write, format, current_dir):
        super(LogPainter, self).__init__(current_dir)
        self.write = write
        self.format = format
        self.parser = LogParser()

    @contextmanager
    def paint(self):
        yield self.routes

        if not self.routes:
            self.write("Noting to route. ")
            return

        for args in self.parser.parse_docs(self.routes):
            self.write(self.format(*args))


class AppLogPainter(LogPainter):
    """
    在app启动时的routes日志输出
    """

    def __init__(self, write, current_dir):
        super(AppLogPainter, self).__init__(write, self._format, current_dir)

    @staticmethod
    def _format(method, parttern, name, ca_name):
        return f"Route method: {method}, url: {parttern} to {name}."


class ShowLogPainter(LogPainter):
    """
    查看routes时使用
    """

    def __init__(self, format):
        super(ShowLogPainter, self).__init__(print, format, os.getcwd())


class DocPainter(Painter):
    """
    用来生成接口文档
    """

    def __init__(self, current_dir, parser_path):
        super(DocPainter, self).__init__(current_dir)
        self.parser = load(parser_path)()

    def paint(self):
        return self.parser.parse_docs(self.routes)
