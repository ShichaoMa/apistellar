import re

from os import makedirs, sep
from os.path import join, exists
from abc import ABC, abstractmethod
from star_builder.types import validators


__all__ = ["Task", "Project", "Service", "Model", "Repository"]


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
            fn = join(name, "start.py")
            if exists(fn) and input(f"文件{fn}已存在，是否覆盖y/n?") not in ["y", "yes"]:
                exit(0)
            with open(fn, "w") as f:
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
            fn = join(name, "__init__.py")
            if exists(fn) and input(f"文件{fn}已存在，是否覆盖y/n?") not in ["y", "yes"]:
                exit(0)
            with open(fn, "w") as f:
                f.write(init.render(father=father or "Service", service=name))

        print("、".join(names), "服务模块已完成创建。")

    @classmethod
    def enrich_parser(cls, sub_parser):
        sub_parser.add_argument("name", nargs="+", help="服务模块名称")


class Model(Task):
    """
    模型层
    """
    def create(self, env, **kwargs):
        task = kwargs.pop("task")
        name = kwargs.pop("name")
        path = kwargs.pop("path").replace(".", sep)
        fields = kwargs.pop("fields", [])

        words = re.findall(r"([A-Za-z0-9]+)", name)
        assert words, f"name: {name} invalid!"
        assert words[0][0].isalpha(), f"name: {name} start with number!"

        fields = [f.split(":", 1) for f in fields]
        if fields:
            types = dict()
            for p in dir(validators):
                obj = getattr(validators, p)
                if isinstance(obj, type) and \
                        issubclass(obj, validators.Validator):
                    types[obj.__name__.lower()] = obj.__name__
            new_fields = []
            for k, v in fields[:]:
                new_fields.append((k, types.get(v.lower(), "")))
            fields = new_fields

        makedirs(path, exist_ok=True)
        model = env.get_template(join(task, 'model.py.tmpl'))
        fn = join(path, f"{name}.py")
        if exists(fn) and input(f"文件{fn}已存在，是否覆盖y/n?") not in ["y", "yes"]:
            exit(0)
        with open(fn, "w") as f:
            f.write(model.render(model=name, fields=fields))

        print(f"{name} model已完成创建。")

    @classmethod
    def enrich_parser(cls, sub_parser):
        sub_parser.add_argument("-n", "--name", required=True, help="models名称")
        sub_parser.add_argument(
            "-p", "--path", required=True, help="model地址, eg:uploader.s3")
        sub_parser.add_argument("fields", nargs="*", help="字段，eg: id:int")


class Repository(Task):
    """
    业务层
    """
    def create(self, env, **kwargs):
        task = kwargs.pop("task")
        name = kwargs.pop("name")
        path = kwargs.pop("path").replace(".", sep)

        words = re.findall(r"([A-Za-z0-9]+)", name)
        assert words, f"name: {name} invalid!"
        assert words[0][0].isalpha(), f"name: {name} start with number!"

        makedirs(path, exist_ok=True)
        repository = env.get_template(join(task, 'repository.py.tmpl'))
        fn = join(path, "repository.py")
        if exists(fn) and input(f"文件{fn}已存在，是否覆盖y/n?") not in ["y", "yes"]:
            exit(0)
        with open(fn, "w") as f:
            f.write(repository.render(repository=name))

        print(f"{name} 仓库已完成创建。")

    @classmethod
    def enrich_parser(cls, sub_parser):
        sub_parser.add_argument("-n", "--name", required=True, help="仓库名称")
        sub_parser.add_argument(
            "-p", "--path", required=True, help="仓库地址, eg:uploader.s3")
