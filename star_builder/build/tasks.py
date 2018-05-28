import re

from os import makedirs
from os.path import join, exists
from abc import ABC, abstractmethod


__all__ = ["Task", "Project", "Service"]


class Task(ABC):

    @abstractmethod
    def create(self, env, **kwargs):
        pass

    @classmethod
    @abstractmethod
    def enrich_parser(self, sub_parser):
        pass


class Project(Task):
    """
    项目
    """
    def create(self, env, **kwargs):
        task = kwargs.pop("task")
        names = kwargs.pop("name")
        for name in names:
            makedirs(join(name, name), exist_ok=True)
            template = env.get_template(join(task, 'start.py.tmpl'))
            with open(join(name, "start.py"), "w") as f:
                f.write(template.render())
            print(f"{name} 项目已完成创建。")

    @classmethod
    def enrich_parser(cls, sub_parser):
        sub_parser.add_argument("name", nargs=1, help="项目名称")


class Service(Task):
    """
    服务
    """
    def create(self, env, **kwargs):
        task = kwargs.pop("task")
        names = kwargs.pop("name")
        father = None
        if exists("__init__.py"):
            regex = re.compile(r"class\s+(\w*?Service)\(\w*Service\):")
            mth = regex.search(open("__init__.py").read())
            if mth:
                father = mth.group(1)

        for name in names:
            words = re.findall(r"([A-Za-z0-9]+)", name)
            assert words, f"name: {name} invalid!"
            assert words[0][0].isalpha(), f"name: {name} start with number!"
            makedirs(name, exist_ok=True)
            init = env.get_template(join(task, '__init__.py.tmpl'))
            with open(join(name, "__init__.py"), "w") as f:
                f.write(init.render(father=father or "Service", service=name))

        print("、".join(names), "服务模块已完成创建。")

    @classmethod
    def enrich_parser(cls, sub_parser):
        sub_parser.add_argument("name", nargs="+", help="服务模块名称")
