import re
import sys

from os import makedirs
from os.path import join, exists

from argparse import ArgumentParser
from jinja2 import PackageLoader, Environment, FileSystemLoader

from .helper import ArgparseHelper


class Command(object):
    """
    项目构建工具
    """
    def __init__(self):
        args = self.parse_args()
        self.templates_path = args.templates
        self.names = args.name
        self.type = args.type

    def create(self):
        if self.templates_path:
            env = Environment(loader=FileSystemLoader(self.templates_path))
        else:
            env = Environment(loader=PackageLoader('star_builder', 'templates'))
        getattr(self, f"create_{self.type}")(env)

    def create_project(self, env):
        for name in self.names:
            makedirs(name, exist_ok=True)
            makedirs(join(name, "static"), exist_ok=True)
            makedirs(join(name, "templates"), exist_ok=True)
            template = env.get_template(join(self.type, 'start.py.tmpl'))
            with open(join(name, "start.py"), "w") as f:
                f.write(template.render())
            print(f"{name} 项目已完成创建。")

    def create_service(self, env):
        father = None
        if exists("__init__.py"):
            regex = re.compile(r"class\s+(\w*?Service)\(\w*Service\):")
            mth = regex.search(open("__init__.py").read())
            if mth:
                father = mth.group(1)

        for name in self.names:
            words = re.findall(r"([A-Za-z0-9]+)", name)
            if words[0][0].isdigit():
                print("Service name cannot start with number!")
                exit(1)
            makedirs(name, exist_ok=True)
            template = env.get_template(join(self.type, '__init__.py.tmpl'))
            with open(join(name, "__init__.py"), "w") as f:
                f.write(template.render(father=father or "Service", service=name))

        print("、".join(self.names), "服务模块已完成创建。")

    def parse_args(self):
        base_parser = ArgumentParser(
            description=self.__class__.__doc__, add_help=False)
        base_parser.add_argument("-t", "--templates", help="模板路径.")

        parser = ArgumentParser(description="Apistar项目构建工具", add_help=False)
        parser.add_argument('-h', '--help', action=ArgparseHelper,
                            help='显示帮助信息并退出. ')
        sub_parsers = parser.add_subparsers(dest="type", help="创建项目还是服务模块 ")

        project = sub_parsers.add_parser(
            "project", parents=[base_parser], help="创建项目")
        project.add_argument("name", nargs=1, help="项目名称")

        service = sub_parsers.add_parser(
            "service", parents=[base_parser], help="创建服务模块")
        service.add_argument("name", nargs="+", help="服务模块名称")
        if len(sys.argv) < 2:
            parser.print_help()
            exit(1)
        return parser.parse_args()


def main():
    Command().create()


if __name__ == "__main__":
    main()
