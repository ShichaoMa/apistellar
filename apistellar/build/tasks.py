import re
import os
import sys
import string

from collections import OrderedDict
from importlib import import_module
from os import makedirs, sep, listdir, getcwd
from os.path import join, exists, abspath, dirname, isdir, basename

from toolkit import load
from toolkit.markdown_helper import MarkDownRender
from apistellar.types import validators
from apistellar.document import DocPainter

__all__ = ["Task", "Project", "Service", "Model", "Solo", "Document"]


class Task(object):
    def __init__(self):
        self.template = None
        self.kwargs = {}

    def create(self, env, **kwargs):
        task = kwargs.pop("task")
        names = kwargs.pop("name", [])
        self.kwargs.update(kwargs)

        for name in names:
            self.enrich_kwargs(self.validate_name(name))
            makedirs(self.kwargs["dirname"], exist_ok=True)
            self.copytree(env, task)
        print("、".join(names), "已创建。")

    def validate_name(self, name):
        return name

    def enrich_kwargs(self, name):
        self.kwargs["name"] = name
        self.kwargs["dirname"] = name

    @classmethod
    def enrich_parser(cls, sub_parser):
        pass

    def copytree(self, env, task, dest_path=None):
        if dest_path is None:
            dest_path = self.kwargs["dirname"]
        copy_path = join(self.template, task)

        for file in listdir(copy_path):
            file = join(copy_path, file)

            if file.count("__pycache__"):
                continue

            if isdir(file):
                dir_name = abspath(join(dest_path, self.render_path_name(file)))
                makedirs(dir_name, exist_ok=True)
                self.copytree(env, file, dir_name)
            else:
                template = env.get_template(file.replace(self.template, ""))
                file = self.render_path_name(file)
                filename = abspath(join(dest_path, file).replace(".tmpl", ""))
                if exists(filename) and \
                        input(f"{filename}已存在，是否覆盖y/n?") not in ["y", "yes"]:
                    continue

                with open(filename, "w") as f:
                    f.write(template.render(**self.kwargs))
                    f.write("\n")

    def render_path_name(self, path):
        return string.Template(basename(path)).substitute(**self.kwargs)


class Project(Task):
    """
    项目
    """
    def validate_name(self, name):
        assert re.search(r'^[_a-zA-Z]\w*$', name), \
            '项目名称只能包含数字、字母、下划线并以字母开头！'
        try:
            mod = import_module(name)
        except ImportError:
            mod = None
        assert mod is None, f'模块 {name} 已存在！'
        return name

    def enrich_kwargs(self, name):
        super(Project, self).enrich_kwargs(name)
        self.kwargs["project_dir"] = join(getcwd(), name)

    @classmethod
    def enrich_parser(cls, sub_parser):
        sub_parser.add_argument("name", nargs=1, help="项目名称")


class ModuleTask(Task):

    def validate_name(self, name):
        words = re.findall(r"([A-Za-z0-9]+)", name)
        assert words, f"name: {name} invalid!"
        assert words[0][0].isalpha(), f"name: {name} start with number!"
        return words

    def enrich_kwargs(self, words):
        class_name = "".join(word.capitalize() for word in words)
        module_name = "_".join(word.lower() for word in words)
        self.kwargs["class_name"] = class_name
        self.kwargs["module_name"] = module_name
        self.kwargs["dirname"] = module_name


class Service(ModuleTask):
    """
    服务
    """

    def enrich_kwargs(self, words):
        super().enrich_kwargs(words)
        father = None

        if exists("__init__.py"):
            regex = re.compile(r"class\s+(\w*?Controller)\(\w*Controller\):")
            mth = regex.search(open("__init__.py").read())
            if mth:
                father = mth.group(1)
        self.kwargs["father"] = father or "Controller"

    @classmethod
    def enrich_parser(cls, sub_parser):
        sub_parser.add_argument("name", nargs="+", help="服务模块名称")


class Drivable(Task):

    def enrich_kwargs(self, name):
        super().enrich_kwargs(name)
        driver = self.kwargs.get("driver")
        if driver and driver.count(":") == 1:
            module, cls = driver.split(":")
        else:
            module, cls = None, None
        self.kwargs["module"] = module
        self.kwargs["cls"] = cls

    @classmethod
    def enrich_parser(cls, sub_parser):
        super().enrich_parser(sub_parser)
        sub_parser.add_argument(
            "-d", "--driver", help="驱动 eg：pymongo:MongoClient")


class Model(Drivable, ModuleTask):
    """
    模型层
    """
    @staticmethod
    def to_list(val):
        """用来兼容接口"""
        return [val]

    def enrich_kwargs(self, words):
        super().enrich_kwargs(words)
        fields = [f.split(":", 1) for f in self.kwargs.get("fields", [])]
        types = dict()

        for p in dir(validators):
            obj = getattr(validators, p)
            if isinstance(obj, type) and \
                    issubclass(obj, validators.Validator):
                types[obj.__name__.lower()] = obj.__name__

        new_fields = []
        for k, v in fields[:]:
            new_fields.append((k, types.get(v.lower(), "")))
        self.kwargs["fields"] = new_fields
        self.kwargs["dirname"] = self.kwargs.get("path") or self.kwargs["dirname"]

    @classmethod
    def enrich_parser(cls, sub_parser):
        super().enrich_parser(sub_parser)
        sub_parser.add_argument(
            "-n", "--name", required=True, type=cls.to_list, help="models名称")
        sub_parser.add_argument(
            "-p", "--path", help="所属服务路径 eg: article/comment")
        sub_parser.add_argument(
            "-a", "--async", action="store_true", help="是否拥有异步获取属性的能力")
        sub_parser.add_argument("fields", nargs="*", help="字段 eg: id:integer")


class Solo(ModuleTask):
    """
    独立任务程序
    """
    def enrich_kwargs(self, words):
        super().enrich_kwargs(words)
        project_name = basename(abspath(getcwd()))
        self.kwargs["project_name"] = project_name
        self.kwargs["dirname"] = join(project_name, self.kwargs["dirname"])
        self.kwargs["back_trace"] = ".." + sep + ".." + sep

    @classmethod
    def enrich_parser(cls, sub_parser):
        sub_parser.add_argument("name", nargs="+", help="独立任务程序名称")


class Document(Task):

    def create(self, env, **kwargs):
        task = kwargs.pop("task")
        parser = kwargs.pop("parser")
        name = kwargs.pop("name", [])[0]
        module = kwargs["module"]
        location = abspath(join(os.getcwd(), kwargs.pop("location")))


        if module:
            current_dir = dirname(load(module).__file__)
            sys.modules.pop(module, None)
        else:
            current_dir = "."
        os.chdir(current_dir)

        painter = DocPainter(current_dir, parser)
        # 不再提醒是否覆盖
        global input
        input = self._input
        base_dir_name = join(location, name)

        indices = OrderedDict()
        for parent, doc in painter.paint().items():
            doc["dirname"] = base_dir_name
            self.kwargs = doc
            fn = os.path.join(
                base_dir_name, doc["file_path"], doc["doc_name"] + ".md.html")
            indices[fn] = doc["doc_name"]
            self.copytree(env, task)

        os.makedirs(base_dir_name, exist_ok=True)
        with open(os.path.join(base_dir_name, "index.md"), "w") as f:
            f.write(f"# {name}文档\n\n")
            for index, (key, val) in enumerate(indices.items()):
                f.write(f"{index+1}. [{val}]({key})\n")

        print(f"{name}已创建。")
        with MarkDownRender("github-markdown.css", base_dir_name) as mk_render:
            output = mk_render.render()

        if output:
            os.system(f"open {output}")
        else:
            print("未找到可打开的文档！")

    @staticmethod
    def _input(prompt):
        return "y"

    @classmethod
    def enrich_parser(cls, sub_parser):
        sub_parser.add_argument("name", nargs=1, help="文档名称")
        sub_parser.add_argument("-m", "--module", help="模块地址", required=True)
        sub_parser.add_argument("-l", "--location", help="文章地址", default=".")
        sub_parser.add_argument(
            "-p", "--parser", help="parser模块地址",
            default="apistellar.document.parser.RstDocParserDocParser")

