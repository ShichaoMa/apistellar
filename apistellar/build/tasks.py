import re
import os
import sys
import string

from collections import OrderedDict
from importlib import import_module
from os import makedirs, sep, listdir, getcwd
from os.path import join, exists, abspath, dirname, isdir, basename

from toolkit import load
from apistellar.types import validators
from apistellar.document import DocPainter
from toolkit.markdown_helper import MarkDownRender


__all__ = ["Task", "Project", "Service", "Model", "Solo", "Document", "Rpc"]


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


class Model(ModuleTask):
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
        # sub_parser.add_argument(
        #     "-a", "--async", action="store_true", help="是否拥有异步获取属性的能力")
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


class APIRenderTask(Task):
    """
    通过API生成文档，RPC调用等
    """
    @staticmethod
    def _cwd(module):
        """
        切换到模块包所在目录并返回
        :param module:
        :return:
        """
        if module:
            current_dir = dirname(load(module).__file__)
            sys.modules.pop(module, None)
        else:
            current_dir = "."
        os.chdir(current_dir)
        return current_dir

    @staticmethod
    def _ignore_input():
        """
        不再提醒是否覆盖
        :return:
        """
        global input

        def _input(prompt):
            return "y"
        input = _input

    def create(self, env, **kwargs):
        """
        创建一个模板实例
        :param env:
        :param kwargs: 解析命令行获取的参数
        :return:
        """
        name = kwargs.pop("name", [])[0]
        self._ignore_input()
        base_dir_name = abspath(join(os.getcwd(), kwargs.pop("location"), name))
        cwd = self._cwd(kwargs["module"])
        indices = OrderedDict()

        for parent, doc in DocPainter(cwd, kwargs["parser"]).paint().items():
            self.kwargs = self._enrich_kwargs(doc, base_dir_name, kwargs)
            self._enrich_indices(doc, indices)
            makedirs(self.kwargs["dirname"], exist_ok=True)
            self.copytree(env, kwargs["task"])

        self._finalize(indices, name, base_dir_name)

    @classmethod
    def _enrich_kwargs(cls, doc, base_dir_name, kwargs):
        doc["dirname"] = base_dir_name
        doc.setdefault("enumerate", enumerate)
        doc.setdefault("bool", bool)
        doc.setdefault("len", len)
        doc.setdefault("map", map)
        return doc

    @staticmethod
    def _enrich_indices(doc: dict, indices: dict):
        """
        在渲染完多个模块时，为能生成一个索引页(或`__init__.py`)保留一些数据
        :param doc:
        :param indices:
        """

    @staticmethod
    def _finalize(indices: dict, name: str, base_dir_name: str):
        """
        使indices等数据生成一个索引页或执行其它收尾工作
        :param indices:
        :param name:
        :param base_dir_name:
        :return:
        """
    @classmethod
    def enrich_parser(cls, sub_parser):
        sub_parser.add_argument("name", nargs=1, help="输出名称")
        sub_parser.add_argument("-m", "--module", help="模块地址", required=True)
        sub_parser.add_argument("-l", "--location", help="输出地址", default=".")
        sub_parser.add_argument(
            "-p", "--parser", help="parser模块地址",
            default="apistellar.document.parser.RstDocParserDocParser")


class Document(APIRenderTask):

    @staticmethod
    def _enrich_indices(doc, indices):
        """
        生成index.md所需要的数据
        :param doc:
        :param indices:
        :return:
        """
        fn = os.path.join(
            doc["dirname"], doc["file_path"], doc["doc_name"] + ".md.html")
        indices[fn] = doc["doc_name"]

    @classmethod
    def _enrich_kwargs(cls, doc, base_dir_name, kwargs):
        """
        为模板增加一个迭代器用来迭代接口
        :param doc:
        :param base_dir_name:
        :param kwargs:
        :return:
        """
        doc = super()._enrich_kwargs(doc, base_dir_name, kwargs)
        doc.setdefault("iter", cls.iter_interface)
        return doc

    @staticmethod
    def iter_interface(interface):
        """
        迭代接口里面的参数
        :param interface:
        :return:
        """
        if "params" in interface:
            yield ("查询参数", interface["params"])

        if "path_params" in interface:
            yield ("路径参数", interface["path_params"])

        if "form_params" in interface:
            yield ("表单参数", interface["form_params"])

    @staticmethod
    def _finalize(indices, name, base_dir_name):
        """
        渲染markdown文档成html，并添加一个目录，同时打开文档
        :param indices:
        :param name:
        :param base_dir_name:
        :return:
        """
        os.makedirs(base_dir_name, exist_ok=True)
        with open(os.path.join(base_dir_name, "index.md"), "w") as f:
            f.write(f"# {name}\n\n")
            for index, (key, val) in enumerate(indices.items()):
                f.write(f"{index+1}. [{val}]({key})\n")

        print(f"{name}已创建。")
        with MarkDownRender("github-markdown.css", base_dir_name) as mk_render:
            output = mk_render.render()

        if output:
            try:
                os.system(f"open {output}")
            except Exception:
                print(f"打开{output}失败! ")
        else:
            print("未找到可打开的文档！")

    @classmethod
    def enrich_parser(cls, sub_parser):
        super().enrich_parser(sub_parser)


class Rpc(APIRenderTask):

    @staticmethod
    def _enrich_indices(doc, indices):
        """
        生成__init__.py所需要的数据
        :param doc:
        :param indices:
        :return:
        """
        indices[doc["controller"].capitalize()] = doc["controller"]

    @classmethod
    def _enrich_kwargs(cls, doc, base_dir_name, kwargs):
        """
        增加一些渲染参数
        :param doc:
        :param base_dir_name:
        :param kwargs:
        :return:
        """
        doc = super()._enrich_kwargs(doc, base_dir_name, kwargs)
        doc["dirname"] = base_dir_name
        base = kwargs["base"]
        assert base.count(":") == 1, f"Invalid format: {base}"
        doc["base_module"], doc["base_class"] = base.split(":")
        doc.setdefault("agg", cls._agg_interface_aiohttp)
        doc.setdefault("str", str)
        if kwargs["conn_timeout"]:
            doc.setdefault(
                "conn_timeout", ", conn_timeout=%d" % kwargs["conn_timeout"])
        if kwargs["read_timeout"]:
            doc.setdefault(
                "read_timeout", ", read_timeout=%d" % kwargs["read_timeout"])
        return doc

    @staticmethod
    def _agg_interface_aiohttp(interface):
        """
        将一个接口中的数据组合成构建方法所需要的部分结构
        :param interface:
        :return:
        """
        args_def = ""
        body_def = ""
        call_args_def = ""
        have_path_param = ""
        if "path_params" in interface:
            args_def += f"path_params: dict, "
            have_path_param = ", have_path_param=True"

        if "json_params" in interface:
            args_def += f"json: dict, "
            call_args_def += ", json=json"

        if "form_params" in interface:
            args_def += f"form_fields: typing.List[dict], "
            form_body = """        data = FormData()
        for meta in form_fields:
            data.add_field(meta["name"],
                           meta["value"],
                           filename=meta.get("filename"),
                           content_type=meta.get("content_type"))\n"""
            call_args_def += ", data=data"
            body_def += form_body

        if "params" in interface:
            params = list()

            for name, param in interface["params"].items():
                args_def += f"{name}: {param['type']}"
                params.append(name)
                # 服务端有默认参数，所以客户端不需要主动传参，默认为None
                if "default" in param:
                    args_def += "=None"
                args_def += ", "

            if params:
                pair = ""
                for name in params:
                    pair += f'        if {name} is not None:' \
                            f'\n            params["{name}"] = {name}\n'

                body_def += "        params = dict()\n%s" % pair
            call_args_def += ", params=params"

        args_def += "cookies: dict=None"

        if "return_wrapped" in interface:
            method = "json"
            success_key_name = interface["return_wrapped"]["success_key_name"]
            success_code = interface["return_wrapped"]["success_code"]
        else:
            success_code = None
            success_key_name = None

            if "return_class" in interface:
                if interface["return_class"] in (bytes, str):
                    method = "read"
                else:
                    method = "json"
            else:
                method = "read"

        if method == "read" or success_code is None:
            error_check = ""
        else:
            error_check = ', error_check=lambda x: x["code"] != %s' % success_code

        if success_key_name is None:
            success_key_name = ""
        else:
            success_key_name = f', "{success_key_name}"'

        return args_def, body_def, call_args_def, method, \
               error_check, success_key_name, have_path_param

    @staticmethod
    def _finalize(indices, name, base_dir_name):
        """
        生成一个__init__.py，将所有模块中的接口结合起来
        :param indices:
        :param name:
        :param base_dir_name:
        :return:
        """
        os.makedirs(base_dir_name, exist_ok=True)
        tmpl = f"class {name.capitalize()}(%s):\n    pass"

        with open(os.path.join(base_dir_name, "__init__.py"), "w") as f:
            f.write(f"# {name} API\n")
            import_str = ""
            base_str = ""

            for key, val in indices.items():
                import_str += f"from .{val} import {key}\n"
                base_str += f"{key}, "
            f.write(import_str + "\n\n")
            f.write(tmpl % base_str[:-2])

        print(f"{name} 驱动已创建。")

    @classmethod
    def enrich_parser(cls, sub_parser):
        super().enrich_parser(sub_parser)
        sub_parser.add_argument(
            "-b", "--base",
            default="apistellar.helper:RestfulApi",
            help="rpc基类 eg：apistellar.helper:RestfulApi")

        sub_parser.add_argument(
            "-ct", "--conn-timeout", type=int,
            help="连接超时时间， 单位：秒")

        sub_parser.add_argument(
            "-rt", "--read-timeout", type=int,
            help="数据读取时间， 单位：秒")
