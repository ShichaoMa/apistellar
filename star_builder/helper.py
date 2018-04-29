import os
import glob

from apistar import Include
from argparse import Action, _SubParsersAction


def look_for_services(current_path):
    files = glob.glob(os.path.join(current_path, "*"))

    for file in files:
        if os.path.isdir(file):
            services_from_package(file)
            look_for_services(file)


def services_from_package(package_path):
    module_str = package_path.replace("/", ".").strip(".")
    __import__(module_str, fromlist=module_str.split(".")[-1])


def collect_route(service):
    routes = list()
    routes.append(get_include(service, None))
    return routes


def get_include(service, parent_prefix):
    if not hasattr(service, "prefix") or service.prefix == parent_prefix:
        raise RuntimeError(f"{service} is not routed! ")
    routes = []
    for name in dir(service):
        prop = getattr(service, name)
        if hasattr(prop, "route"):
            prop.route.service = service
            routes.append(prop.route)

    for child_service in service.children:
        child_include = get_include(child_service, service.prefix)
        if child_include:
            routes.append(child_include)

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
