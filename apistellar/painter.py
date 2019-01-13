# -*- coding:utf-8 -*-
import re
import sys
import json
import typing
import inspect

from functools import reduce
from collections import OrderedDict
from abc import ABC, abstractmethod
from contextlib import contextmanager

from toolkit import cache_property, cache_method
from apistar import Include, Route, http

from apistellar.bases.entities import FormParam
from apistellar.bases.controller import Controller
from apistellar.helper import load_packages, routing
from apistellar.types import Type

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
        sys.path.insert(0, self.current_dir)
        load_packages(".")
        include = routing(Controller)
        routes = [include] if include else []
        return routes

    def walk_route(self, routes, parents=None):
        """
        遍历所有的include，找到route及其patient include
        :param routes:
        :param parents:
        :return:
        """
        for route in routes:
            if parents is None:
                current_parents = []
            else:
                current_parents = parents[:]
            if isinstance(route, Include):
                current_parents.append(route)
                yield from self.walk_route(route.routes, current_parents)
            else:
                yield route, parents

    @staticmethod
    def _extract_pattern(route, parents):
        return reduce(
            lambda x, y: x.rstrip('/') + y.url, parents, "").rstrip("/") \
               + route.url

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

    @contextmanager
    def paint(self):
        yield self.routes

        if not self.routes:
            self.write("Noting to route. ")
            return

        for route, parents in self.walk_route(self.routes):
            name = reduce(lambda x, y: f"{x}:{y.name}", parents[1:], "view") \
                   + ":" + route.name
            cont = route.controller.__class__
            ca_name = f"{cont.__module__}:{cont.__name__}" \
                      f"#{route.handler.__name__}"
            pattern = self._extract_pattern(route, parents)
            self.write(self.format(route.method, pattern, name, ca_name))


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
        super(ShowLogPainter, self).__init__(print, format, ".")


class DummyParam(object):
    def __init__(self, name, default, annotation):
        self.name = name
        if default is inspect._empty:
            self.default = default
        else:
            self.default = default() if callable(default) else default
        self.annotation = annotation


class DocPainter(Painter):
    """
    用来生成接口文档
    """
    param_annotation_mapping = {
        http.QueryParam: "str",
        str: "str",
        int: "int",
        bool: "bool",
        float: "float",
        http.PathParam: "str",
        FormParam: "str",
        http.RequestData: "json",
        http.QueryParams: "dict"
        }

    def paint(self):
        docs = OrderedDict()

        for route, parents in self.walk_route(self.routes):
            ps = tuple(x.name for x in parents[1:])
            doc = docs.setdefault(ps, dict())
            doc.setdefault("parents", ps)
            doc.setdefault("doc_name", route.controller.__class__.__doc__.strip())
            interfaces = doc.setdefault("interfaces", list())
            interfaces.append(self._extract_info(route, parents))
        return docs

    @staticmethod
    def iter_interface(interface):
        if "params" in interface:
            yield ("查询参数", interface["params"])

        if "path_params" in interface:
            yield ("路径参数", interface["path_params"])

        if "form_params" in interface:
            yield ("表单参数", interface["form_params"])

    @staticmethod
    def _extract_param_desc(docstring, param_name):
        mth = re.search(
            rf":param +{param_name}: (.*?)(?=((:ex)|(:param)|(:return)|$))",
            docstring, re.DOTALL)

        if mth:
            return mth.group(1)

    def _extract_param_example(self, docstring, param_name):
        examples = [self._adjust_example(e) for e in re.findall(
                rf":ex +{param_name}:\s+(`+[^`]+?`+)"
                rf"\s+(?=(?:(?::ex)|(?::param)|(?::return)|$))",
                docstring, re.DOTALL)]
        # 为短示例增加序号
        if len(examples) > 1 and "```" not in examples[0]:
            examples = ["%d. %s" % (i + 1, self._adjust_example(e))
                        for i, e in enumerate(examples)]
        return examples

    @staticmethod
    def _extract_comment(docstring):
        if not docstring:
            return ""

        mth = re.search(
            r"^\s+(.*?)(?=((:ex)|(:param)|(:return)|$))", docstring, re.DOTALL)

        if mth:
            return mth.group(1)

    def _get_params_attr(self, param, doc):
        attributes = dict()
        attributes["type"] = self.param_annotation_mapping.get(
            param.annotation, param.annotation.__name__)

        if param.default != inspect._empty:
            attributes["default"] = param.default

        if doc:
            desc = self._extract_param_desc(doc, param.name)
            if desc:
                attributes["desc"] = desc.strip()
            attributes["example"] = self._extract_param_example(doc, param.name)

        return attributes

    def _extract_return_example(self, docstring):
        if not docstring:
            return []

        return [self._adjust_example(e) for e in re.findall(
            r":return:\s+(`+[^`]+?`+)\s*(?=(?:(?::return)|$))",docstring, re.DOTALL)]

    @cache_method()
    def _extract_type_annotation(self, cls):
        info = dict()
        for prop, validator in cls.validator.properties.items():
            param = DummyParam(
                prop, getattr(validator, "default", inspect._empty),
                validator.__class__)
            info[prop] = self._get_params_attr(param, cls.__doc__)
        return info

    @staticmethod
    def _adjust_example(ex):
        ex = ex.strip()
        lines = ex.split("\n")
        if len(lines) > 1:
            lines[-1] = lines[-1].strip()
            ex = "\n".join(lines)
        return ex

    def _get_type_info(self, cls, structure):
        if issubclass(cls, Type):
            type_info = self._extract_type_annotation(cls)
            structure[cls] = type_info
            yield cls.__name__, type_info
        elif hasattr(cls, "__args__"):
            child = structure.setdefault(cls, OrderedDict())
            for cls in getattr(cls, "__args__"):
                yield from self._get_type_info(cls, child)
        else:
            type_info = dict()
            structure[cls] = type_info
            yield cls.__name__, type_info

    def _extract_info(self, route: Route, parents):
        info = dict()
        handler = route.handler
        type_info = dict()
        info["endpoint"] = self._extract_pattern(route, parents)
        info["method"] = route.method
        info["comment"] = self._extract_comment(handler.__doc__).strip()
        params, form_params, path_params = (OrderedDict() for i in range(3))
        json_params = None
        sign = inspect.signature(handler)
        path_names = {
            item.strip('{}').lstrip('+'): item.strip('{}')
            for item in re.findall('{[^}]*}', route.url)
        }
        for name, param in sign.parameters.items():
            if param.annotation in self.param_annotation_mapping.keys():
                attributes = self._get_params_attr(param, handler.__doc__)
                if name in path_names.keys():
                    if path_names[name].startswith("+"):
                        attributes["type"] = "path"
                    # path_params不能有默认参数
                    if "default" in attributes:
                        del attributes["default"]
                    path_params[name] = attributes
                elif param.annotation == FormParam:
                    form_params[name] = attributes
                elif attributes["type"] == "json":
                    json_params = attributes
                elif attributes["type"] == "dict":
                    emp = attributes.get("example")
                    if emp:
                        try:
                            params = json.loads(emp.strip("`"))
                        except json.JSONDecodeError as e:
                            print(f"Example format error of"
                                  f" {attributes['endpoint']} :{name}")
                            raise e

                        for pn, p in params.items():
                            params[pn] = {"example": f"`{json.dumps(p)}`"}
                else:
                    params[name] = attributes
            if issubclass(param.annotation, Type):
                structure = dict()
                type_info.update(self._get_type_info(param.annotation, structure))

        if params:
            info["params"] = params
        if form_params:
            info["form_params"] = form_params
        if path_params:
            info["path_params"] = path_params
        if json_params:
            info["json_params"] = json_params

        if sign.return_annotation is not inspect._empty:
            info["return_type"] = str(sign.return_annotation)
            structure = dict()
            type_info.update(self._get_type_info(sign.return_annotation, structure))
            info["return_structure"] = structure

        info["return_example"] = self._extract_return_example(handler.__doc__)
        info["type_info"] = type_info
        return info
