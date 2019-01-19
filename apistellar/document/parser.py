import re
import os
import json
import typing
import inspect

from functools import reduce
from collections import OrderedDict
from abc import ABC, abstractmethod

from toolkit import cache_method
from apistar import Include, Route, http

from apistellar.types import Type
from apistellar.bases.entities import FormParam, FileStream, \
    MultiPartForm, UrlEncodeForm


class DummyParam(object):
    def __init__(self, name, default, annotation):
        self.name = name
        if default is inspect._empty:
            self.default = default
        else:
            self.default = default() if callable(default) else default
        self.annotation = annotation


class Parser(ABC):

    @abstractmethod
    def parse_docs(self, routes):
        """
        通过route带来的信息，解析成接口文档信息
        :param routes:
        :return:
        """

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


class LogParser(Parser):

    def parse_docs(self, routes):
        for route, parents in self.walk_route(routes):
            name = reduce(lambda x, y: f"{x}:{y.name}", parents[1:], "view") \
                   + ":" + route.name
            cont = route.controller.__class__
            ca_name = f"{cont.__module__}:{cont.__name__}" \
                      f"#{route.handler.__name__}"
            pattern = self._extract_pattern(route, parents)
            yield route.method, pattern, name, ca_name


class RstDocParserDocParser(Parser):
    param_annotation_mapping = {
        http.QueryParam: "str",
        str: "str",
        int: "int",
        bool: "bool",
        float: "float",
        http.PathParam: "str",
        FormParam: "str",
        http.RequestData: "json",
        FileStream: "file",
        MultiPartForm: "file",
        UrlEncodeForm: "dict",
        http.QueryParams: "dict"
    }

    def parse_docs(self, routes):
        docs = OrderedDict()

        for route, parents in self.walk_route(routes):
            ps = tuple(x.name for x in parents[1:])
            doc = docs.setdefault(ps, dict())
            doc.setdefault("parents", ps)
            doc_name = route.controller.__class__.__doc__
            doc_name = doc_name.strip() if doc_name else \
                route.controller.__class__.__name__
            doc.setdefault("doc_name", doc_name.strip())
            all_type_info = doc.setdefault("type_info", dict())
            interfaces = doc.setdefault("interfaces", list())
            info = self._extract_info(route, parents)
            all_type_info.update(info.pop("type_info", dict()))
            interfaces.append(info)

            doc.setdefault("enumerate", enumerate)
            doc.setdefault("bool", bool)
            doc.setdefault("iter", self.iter_interface)
            doc.setdefault("len", len)
            doc.setdefault("map", map)
            doc.setdefault("file_path", os.path.join(*ps))
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
            attributes["example"] = self._extract_param_example(doc,
                                                                param.name)

        return attributes

    def _extract_return_example(self, docstring):
        if not docstring:
            return []

        return [self._adjust_example(e) for e in re.findall(
            r":return:\s+(.+?)\s*(?=(?:(?::return)|$))", docstring,
            re.DOTALL)]

    @cache_method()
    def _extract_type_annotation(self, cls):
        info = dict()

        for prop, validator in cls.validator.properties.items():
            param = DummyParam(
                prop, getattr(validator, "default", inspect._empty),
                validator.__class__)
            attributes = self._get_params_attr(param, cls.__doc__)
            attributes["allow_null"] = validator.allow_null
            info[prop] = attributes
        return info

    @staticmethod
    def _adjust_example(ex):
        ex = ex.strip()
        lines = ex.split("\n")
        if len(lines) > 1:
            lines[-1] = lines[-1].strip()
            ex = "\n".join(lines)
        return ex

    def _get_module_class_name(self, cls):
        if isinstance(cls, typing.GenericMeta):
            return str(cls)
        else:
            return f"{cls.__module__}.{cls.__name__}"

    def _get_type_info(self, cls, structure):
        if issubclass(cls, Type):
            type_info = self._extract_type_annotation(cls)
            structure[cls] = type_info
            yield self._get_module_class_name(cls), type_info
        elif hasattr(cls, "__args__"):
            child = structure.setdefault(cls, OrderedDict())
            for cls in getattr(cls, "__args__"):
                yield from self._get_type_info(cls, child)
        else:
            type_info = dict()
            structure[cls] = type_info
            yield self._get_module_class_name(cls), type_info

    @staticmethod
    def _extract_resp_info(return_wrapped):
        yield return_wrapped["success_code"], "返回成功"
        for item in (return_wrapped.get("error_info") or {}).items():
            yield item

    def _enrich_params_from_example(self, attributes, params, name):
        examples = attributes.get("example")

        for example in examples:
            try:
                ex_data = json.loads(example.strip("`json"))

                for ex_name, ex in ex_data.items():
                    exs = params.setdefault(
                        ex_name, dict()).setdefault("example", [])
                    params.setdefault(ex_name, dict())["type"] = type(
                        ex).__name__
                    exs.append(f"`{json.dumps(ex)}`")

            except json.JSONDecodeError as e:
                print(f"Example format error "
                      f"of {attributes['endpoint']} :{name}")
                raise e

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
                elif attributes["type"] == "file":
                    form_params["`file1`, `file2`, ..."] = attributes
                elif attributes["type"] == "dict":
                    if param.annotation is UrlEncodeForm:
                        ps = form_params
                    else:
                        ps = params
                    self._enrich_params_from_example(attributes, ps, name)
                else:
                    params[name] = attributes

            elif issubclass(param.annotation, Type):
                json_params = self._get_params_attr(param, handler.__doc__)
                json_params["model_type"] = self._get_module_class_name(
                    param.annotation)
                structure = dict()
                type_info.update(
                    self._get_type_info(param.annotation, structure))

        if params:
            info["params"] = params
        if form_params:
            info["form_params"] = form_params
        if path_params:
            info["path_params"] = path_params
        if json_params:
            info["json_params"] = json_params

        if sign.return_annotation is not inspect._empty:
            info["return_type"] = self._get_module_class_name(
                sign.return_annotation)
            structure = dict()
            type_info.update(
                self._get_type_info(sign.return_annotation, structure))
            # info["return_structure"] = structure

        return_ex = self._extract_return_example(handler.__doc__)
        for ret_ex in return_ex:
            if ret_ex.strip().startswith("`"):
                info.setdefault("return_example", []).append(ret_ex)
            else:
                info.setdefault("return_desc", []).append(ret_ex)
        info["type_info"] = type_info
        # 获取返回响应信息
        return_wrapped = getattr(handler, "__return_wrapped", None)

        if return_wrapped:
            info["resp_info"] = OrderedDict(
                self._extract_resp_info(return_wrapped))
            if "return_type" in info:
                info[
                    "return_type"] = '{"code": xx, "%s": %s, "message": "xx"}' % (
                    return_wrapped["success_key_name"], info["return_type"])
        return info
