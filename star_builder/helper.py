import os
import json
import time
import glob
import email

from asyncio import Future
from collections.abc import Mapping
from argparse import Action, _SubParsersAction

from apistar import Include

from .bases.components import Component


def bug_fix():
    from uvicorn.protocols.http import RequestResponseCycle

    async def receive(self):
        message = await self.receive_queue.get()
        self.protocol.buffer_size -= len(message.get('body', b''))
        if self.protocol.buffer_size <= 0 and message.get("more_body"):
            self.protocol.check_resume_reading()
        return message
    RequestResponseCycle.receive = receive


def get_real_method(obj, name):
    """
    IPython bug fix.
    """
    import types
    import inspect
    import ipdb;ipdb.set_trace()
    try:
        canary = getattr(obj, '_ipython_canary_method_should_not_exist_', None)
        if isinstance(canary, Future):
            canary.cancel()
    except Exception:
        return None

    if canary is not None:
        # It claimed to have an attribute it should never have
        return None

    try:
        m = getattr(obj, name, None)
        if isinstance(canary, Future):
            canary.cancel()
    except Exception:
        return None

    if inspect.isclass(obj) and not isinstance(m, types.MethodType):
        return None

    if callable(m):
        return m

    return None


def find_children(cls=Component, initialize=True):
    """
    获取所有(component)的子类或其实例。
    :param cls: 父类
    :param initialize: 是否生成实例
    :return:
    """
    def _load(cs):
        children = []
        for c in cs:
            children.append(c)
            children.extend(_load(c.__subclasses__()))
        return children

    loaded, unloaded = [], []
    for child in _load(cls.__subclasses__()):
        if initialize and getattr(child, "_instance", None):
            loaded.append(child._instance)
        else:
            unloaded.append(child)

    return [c() for c in unloaded] + loaded if initialize else unloaded


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
    instance = service()
    for name in vars(service).keys():
        prop = getattr(service, name)
        if hasattr(prop, "routes"):
            for route in prop.routes:
                route.service = instance
            routes.extend(prop.routes)

    for child_service in service.__subclasses__():
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


def parse_date(ims):
    """
    Parse rfc1123, rfc850 and asctime timestamps and return UTC epoch.
    """
    try:
        ts = email.utils.parsedate_tz(ims)
        return time.mktime(ts[:8] + (0,)) - (ts[9] or 0) - time.timezone
    except (TypeError, ValueError, IndexError, OverflowError):
        return None


def parse_range_header(header, maxlen=0):
    """
    Yield (start, end) ranges parsed from a HTTP Range header. Skip
        unsatisfiable ranges. The end index is non-inclusive.
    :param header:
    :param maxlen:
    :return:
    """
    if not header or header[:6] != 'bytes=': return
    ranges = [r.split('-', 1) for r in header[6:].split(',') if '-' in r]
    for start, end in ranges:
        try:
            if not start:  # bytes=-100    -> last 100 bytes
                start, end = max(0, maxlen-int(end)), maxlen
            elif not end:  # bytes=100-    -> all but the first 99 bytes
                start, end = int(start), maxlen
            else:          # bytes=100-200 -> bytes 100-200 (inclusive)
                start, end = int(start), min(int(end)+1, maxlen)
            if 0 <= start < end <= maxlen:
                yield start, end
        except ValueError:
            pass


def file_iter_range(fp, offset, bytes, maxread=1024*1024):
    """
    Yield chunks from a range in a file. No chunk is bigger than maxread.
    :param fp:
    :param offset:
    :param bytes:
    :param maxread:
    :return:
    """
    fp.seek(offset)
    while bytes > 0:
        part = fp.read(min(bytes, maxread))
        if not part: break
        bytes -= len(part)
        yield part


class TypeEncoder(json.JSONEncoder):
    options = {Mapping: dict}

    @classmethod
    def register(cls, type_mapping):
        cls.options.update(type_mapping)

    def default(self, obj):
        for key, val in self.options.items():
            if isinstance(obj, key):
                return val(obj)
        return json.JSONEncoder.default(self, obj)
