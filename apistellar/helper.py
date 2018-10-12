import os
import json
import time
import glob
import email
import types
import inspect

from functools import reduce, wraps
from collections.abc import Mapping
from asyncio import Future, get_event_loop
from argparse import Action, _SubParsersAction

from apistar import Include, Route
from apistar.http import PathParams, Response
from apistar.server.asgi import ASGIReceive, ASGIScope, ASGISend

from werkzeug._compat import string_types
from werkzeug.utils import escape, text_type
from werkzeug.http import dump_cookie, dump_header, parse_set_header


def get_real_method(obj, name):
    """
    IPython bug fix.
    """
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


def enhance_response(resp):

    def set_cookie(self, key, value='', max_age=None, expires=None,
                   path='/', domain=None, secure=False, httponly=False,
                   samesite=None):
        """Sets a cookie. The parameters are the same as in the cookie `Morsel`
        object in the Python standard library but it accepts unicode data, too.

        A warning is raised if the size of the cookie header exceeds
        :attr:`max_cookie_size`, but the header will still be set.

        :param key: the key (name) of the cookie to be set.
        :param value: the value of the cookie.
        :param max_age: should be a number of seconds, or `None` (default) if
                        the cookie should last only as long as the client's
                        browser session.
        :param expires: should be a `datetime` object or UNIX timestamp.
        :param path: limits the cookie to a given path, per default it will
                     span the whole domain.
        :param domain: if you want to set a cross-domain cookie.  For example,
                       ``domain=".example.com"`` will set a cookie that is
                       readable by the domain ``www.example.com``,
                       ``foo.example.com`` etc.  Otherwise, a cookie will only
                       be readable by the domain that set it.
        :param secure: If `True`, the cookie will only be available via HTTPS
        :param httponly: disallow JavaScript to access the cookie.  This is an
                         extension to the cookie standard and probably not
                         supported by all browsers.
        :param samesite: Limits the scope of the cookie such that it will only
                         be attached to requests if those requests are
                         "same-site".
        """
        self.headers['Set-Cookie'] = dump_cookie(
            key,
            value=value,
            max_age=max_age,
            expires=expires,
            path=path,
            domain=domain,
            secure=secure,
            httponly=httponly,
            charset=self.charset,
            max_size=self.max_cookie_size,
            samesite=samesite
        )

    def delete_cookie(self, key, path='/', domain=None):
        """Delete a cookie.  Fails silently if key doesn't exist.

        :param key: the key (name) of the cookie to be deleted.
        :param path: if the cookie that should be deleted was limited to a
                     path, the path has to be defined here.
        :param domain: if the cookie that should be deleted was limited to a
                       domain, that domain has to be defined here.
        """
        self.set_cookie(key, expires=0, max_age=0, path=path, domain=domain)

    setattr(resp, "set_cookie", set_cookie)
    setattr(resp, "delete_cookie", delete_cookie)
    setattr(resp, "max_cookie_size", 4093)

    def _set_property(name, doc=None):
        def fget(self):
            def on_update(header_set):
                if not header_set and name in self.headers:
                    del self.headers[name]
                elif header_set:
                    self.headers[name] = header_set.to_header()

            return parse_set_header(self.headers.get(name), on_update)

        def fset(self, value):
            if not value:
                del self.headers[name]
            elif isinstance(value, string_types):
                self.headers[name] = value
            else:
                self.headers[name] = dump_header(value)

        return property(fget, fset, doc=doc)

    setattr(resp, "vary", _set_property(
        "vary", doc='''
         The Vary field value indicates the set of request-header fields that
         fully determines, while the response is fresh, whether a cache is
         permitted to use the response to reply to a subsequent request
         without revalidation.'''))


def find_children(cls, initialize=True, kwargs=None):
    """
    获取所有(component)的子类或其实例。
    :param cls: 父类
    :param initialize: 是否生成实例
    :param kwargs: 若初始化，关键字参数
    :return:
    """
    def _load(cs):
        children = []
        for c in cs:
            children.append(c)
            children.extend(_load(c.__subclasses__()))
        return children

    if initialize:
        kwargs = kwargs or dict()
    return [c(**kwargs) if initialize else c for c in _load(cls.__subclasses__())]


def logging_format(method, parttern, name, ca_name):
    return f"Route method: {method}, url: {parttern} to {name}."


def print_routing(routes, write=print, format=logging_format):
    for route, parents in walk_route(routes):
        name = reduce(lambda x, y: f"{x}:{y.name}", parents[1:], "view")\
               + ":" + route.name
        cont = route.controller.__class__
        ca_name = f"{cont.__module__}:{cont.__name__}#{route.handler.__name__}"
        pattern = reduce(
            lambda x, y: x.rstrip('/') + y.url, parents, "").rstrip("/")\
                  + route.url
        write(format(route.method, pattern, name, ca_name))


def walk_route(routes, parents=None):
    for route in routes:
        if parents is None:
            current_parents = []
        else:
            current_parents = parents[:]
        if isinstance(route, Include):
            current_parents.append(route)
            yield from walk_route(route.routes, current_parents)
        else:
            yield route, parents


def load_packages(current_path):
    """
    加载当前路径下的所有package，使得其中的Vontroller子类得以激活
    加载一个包时，如果包下面有子包，只需要导入子包，父包也会一起
    被加载。项目约定Controller子类必须定义在包中(__init__.py)。
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


def routing(controller):
    """
    获取当前Controller下所有route及其子Controller组成的Include
    :param controller:
    :return:
    """
    if not hasattr(controller, "prefix"):
        raise RuntimeError(f"{controller} is not routed! ")
    routes = []
    instance = controller()
    for name in vars(controller).keys():
        prop = getattr(controller, name)
        if hasattr(prop, "routes"):
            for route in prop.routes:
                route.controller = instance
            routes.extend(prop.routes)

    for child_controller in controller.__subclasses__():
        child_include = routing(child_controller)
        if child_include:
            routes.append(child_include)

    if routes:
        return Include(controller.prefix, controller.name, routes)


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


async def file_iter_range(fp, offset, bytes, maxread=1024*1024):
    """
    Yield chunks from a range in a file. No chunk is bigger than maxread.
    :param fp:
    :param offset:
    :param bytes:
    :param maxread:
    :return:
    """
    await fp.seek(offset)
    while bytes > 0:
        part = await fp.read(min(bytes, maxread))
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


class HookReturn(Exception):
    pass


def redirect(location, code=302, Response=None):
    """Returns a response object (a ASGI application) that, if called,
    redirects the client to the target location.  Supported codes are 301,
    302, 303, 305, and 307.  300 is not supported because it's not a real
    redirect and 304 because it's the answer for a request with a request
    with defined If-Modified-Since headers.

    .. versionadded:: 0.6
       The location can now be a unicode string that is encoded using
       the :func:`iri_to_uri` function.

    .. versionadded:: 0.10
        The class used for the Response object can now be passed in.

    :param location: the location the response should redirect to.
    :param code: the redirect status code. defaults to 302.
    :param class Response: a Response class to use when instantiating a
        response. The default is :class:`werkzeug.wrappers.Response` if
        unspecified.
    """
    if Response is None:
        from apistar.http import HTMLResponse as Response

    display_location = escape(location)
    if isinstance(location, text_type):
        # Safe conversion is necessary here as we might redirect
        # to a broken URI scheme (for instance itms-services).
        from werkzeug.urls import iri_to_uri
        location = iri_to_uri(location, safe_conversion=True)
    response = Response(
        '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">\n'
        '<title>Redirecting...</title>\n'
        '<h1>Redirecting...</h1>\n'
        '<p>You should be redirected automatically to target URL: '
        '<a href="%s">%s</a>.  If not click the link.' %
        (escape(location), display_location),
        headers={"Location": location},
        status_code=code)
    return response


class ChildrenFactory(object):

    def __init__(self, father, kwargs=None):
        self.father = father
        self.kwargs = kwargs or {}
        self.found = dict()

    def install(self, **kwargs):
        self.found.clear()
        self.kwargs.update(kwargs)

    def _get_mapping(self):
        return {getattr(child, "name", child.__name__.lower()): child
                for child in find_children(self.father, False)}

    def __contains__(self, item):
        result = item in self.found
        if result is False:
            result = item in self._get_mapping()
        return result

    def get(self, item, default=None):
        try:
            return self[item]
        except KeyError:
            return default

    def __getitem__(self, item):
        child = self.found.get(item)
        if child is None:
            mapping = self._get_mapping()
            child = mapping[item](**self.kwargs)
            self.found[item] = child
        return child

    def __setitem__(self, item, value):
        self.found[item] = value


def require(
        container_cls,
        judge=lambda container: container.user,
        error="Login required!"):
    """
    装饰一个可被注入的函数，注入container_cls的实例，
    并调用judge判断其是否符合条件，否则抛出异常，
    异常信息为error。
    :param container_cls:
    :param judge:
    :param error:
    :return:
    """
    def auth(func):
        args = inspect.getfullargspec(func).args
        args_def = ", ".join(args)
        func_def = """
@wraps(func)
async def wrapper(__container, {}):
    from collections.abc import Awaitable
    assert judge(__container), (401, "{}")
    awaitable = func({})
    if isinstance(awaitable, Awaitable):
        return await awaitable
    return awaitable
        """.format(args_def, error, args_def)

        namespace = dict(__name__='entries_%s' % func.__name__)
        namespace["func"] = func
        namespace["wraps"] = wraps
        namespace["judge"] = judge
        exec(func_def, namespace)
        wrapper = namespace["wrapper"]
        new_func = types.FunctionType(
            wrapper.__code__,
            wrapper.__globals__,
            wrapper.__name__,
            func.__defaults__)
        new_func.__annotations__.update(func.__annotations__)
        new_func.__annotations__["__container"] = container_cls
        return new_func

    return auth


class MySelf(object):
    def __getattr__(self, item):
        return self

    def __getitem__(self, item):
        if item == 'type':
            return "http.request"
        if item == "server":
            return "", 80
        return self

    def __call__(self, *args, **kwargs):
        return self

    def __bool__(self):
        return False

    def __str__(self):
        return ""

    def __radd__(self, obj):
        return obj + type(obj)(self)

    def __iter__(self):
        return iter([])

    def __await__(self):
        loop = get_event_loop()
        future = loop.create_future()
        future.set_result(self)
        return future.__await__()

    __repr__ = __str__


async def add_success_callback(fut, callback):
    """
    这个方法的作用相当于future.set_done_callback。
    :param fut:
    :param callback:
    :return:
    """
    try:
        result = await fut
    except Exception as e:
        result = e
    callback(result)
    return result


class NotImplementedProp(object):
    """
    用来对子类需要实现的类属性进行占位
    """
    def __get__(self, instance, owner):
        return NotImplemented


class classproperty(object):
    """
    property只能用于实例方法到实例属性的转换，使用classproperty来支持类方法到类属性的转换
    """
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, owner):
        return self.func(owner)


def cache_classproperty(func):
    """
    缓存类属性，只计算一次
    :param func:
    :return:
    """
    @classproperty
    @wraps(func)
    def wrapper(*args, **kwargs):
        prop_name = "_" + func.__name__
        if prop_name not in args[0].__dict__:
            setattr(args[0], prop_name, func(*args, **kwargs))
        return args[0].__dict__[prop_name]
    return wrapper


# mock state
STATE = {
        'scope': MySelf(),
        'receive': MySelf(),
        'send': MySelf(),
        'exc': None,
        'path_params': MySelf(),
        'route': MySelf()
        }


INITIAL = {
            'scope': ASGIScope,
            'receive': ASGIReceive,
            'send': ASGISend,
            'exc': Exception,
            'path_params': PathParams,
            'route': Route,
            'response': Response,
        }
