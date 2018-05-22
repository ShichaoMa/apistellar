import os
import glob

from apistar import Include
from argparse import Action, _SubParsersAction


def print_routing(routes, callback=print, parent=""):
    for route in routes:
        if isinstance(route, Include):
            print_routing(route.routes, callback ,parent + route.url)
        else:
            callback(
                f"Route method: {route.method}, "
                f"url: {parent + route.url} to {route.name}.")


def load_packages(current_path):
    """
    加载当前路径下的所有package，使得其中的Service子类得以激活
    加载一个包时，如果包下面有子包，只需要导入子包，父包也会一起
    被加载。项目约定service子类必须定义在包中(__init__.py)。
    所以只考虑加载所有包，不考虑加载其它模块。
    :param current_path:
    :return:
    """
    files = glob.glob(os.path.join(current_path, "*"))
    find_dir = False

    for file in files:
        if os.path.isdir(file):
            find_dir = True
            if not load_packages(file):
                __import__(file.replace("/", ".").strip("."))

    return find_dir


def routing(service, parent_prefix):
    """
    获取当前Service下所有route及其子Service组成的Include
    :param service:
    :param parent_prefix:
    :return:
    """
    if not hasattr(service, "prefix") or service.prefix == parent_prefix:
        raise RuntimeError(f"{service} is not routed! ")
    routes = []
    for name in vars(service).keys():
        prop = getattr(service, name)
        if hasattr(prop, "routes"):
            for route in prop.routes:
                route.service = service
            routes.extend(prop.routes)

    for child_service in service.children:
        child_include = routing(child_service, service.prefix)
        if child_include:
            routes.append(child_include)

    if routes:
        return Include(service.prefix, service.name, routes)


class ArgparseHelper(Action):
    """
        显示格式友好的帮助信息
    """

    def __init__(self,
                 option_strings,
                 dest="",
                 default="",
                 help=None):
        super(ArgparseHelper, self).__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        parser.print_help()
        subparsers_actions = [
            action for action in parser._actions
            if isinstance(action, _SubParsersAction)]
        for subparsers_action in subparsers_actions:
            for choice, subparser in subparsers_action.choices.items():
                print("Command '{}'".format(choice))
                print(subparser.format_usage())

        parser.exit()
