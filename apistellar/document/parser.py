import re
import os
import json
import typing
import inspect

from functools import reduce
from collections import OrderedDict
from abc import ABC, abstractmethod

from toolkit import cache_method
from apistar import Include, http

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
    """
    用于解析rst风格的注释，并生成文档json，用于渲染文档
    """
    keywords = {
        'and',
        'as',
        'assert',
        'async',
        'await',
        'break',
        'class',
        'continue',
        'def',
        'del',
        'elif',
        'else',
        'except',
        'finally',
        'for',
        'from',
        'global',
        'if',
        'import',
        'in',
        'is',
        'lambda',
        'not',
        'or',
        'pass',
        'raise',
        'return',
        'try',
        'while',
        'with',
        'yield'}
    nums_mapping = {
        "0": "zero",
        "1": "one",
        "2": "two",
        "3": "three",
        "4": "four",
        "5": "five",
        "6": "six",
        "7": "seven",
        "8": "eight",
        "9": "nine"
    }

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
    # 支持哪几种注释类型
    types = ("ex", "param", "type", "return")
    regex_tail = f"(?=(?:{'|'.join('(?::%s)' % type for type in types)}|$))"

    def parse_docs(self, routes):
        docs = OrderedDict()

        for route, parents in self.walk_route(routes):
            ps = tuple(x.name for x in parents[1:])
            doc = docs.setdefault(ps, dict())
            doc.setdefault("parents", ps)
            doc["controller"] = self._get_controller_name(parents)
            doc_name = route.controller.__class__.__doc__
            doc_name = doc_name.strip() if doc_name else \
                route.controller.__class__.__name__
            doc.setdefault("doc_name", doc_name.strip())
            all_type_info = doc.setdefault("type_info", dict())
            interfaces = doc.setdefault("interfaces", list())
            info = self._extract_info(route, parents)
            all_type_info.update(info.pop("type_info", dict()))
            interfaces.append(info)
            doc.setdefault("file_path", os.path.join(*ps))
        return docs

    @classmethod
    def regex_format(cls, type, param_name, sub_reg="(.*?)"):
        return r":{} +{}:{}\s+?{}".format(
            type, param_name, sub_reg, cls.regex_tail)

    @staticmethod
    def _get_controller_name(parents):
        if len(parents) > 2:
            return reduce(lambda x, y: x + "_" + y.name, parents[1:])
        else:
            return parents[1].name

    @classmethod
    def _get_name(cls, route, endpoint):
        """
        找到一个可以唯一描述的名字，去掉非法字符，
        如果首字母是数字将其转换成英文，如果是关键字加个_
        :param route:
        :param endpoint:
        :return:
        """
        name = "_".join(endpoint.strip("/").split("/")) or route.handler.__name__
        name = "".join(re.findall(r"([\w_]+)", name))
        if name[0].isdigit():
            name = cls.nums_mapping[name[0]] + name[1:]
        if name in cls.keywords:
            name = name + "_"
        return name

    def _extract_info(self, route, parents):
        info = dict()
        handler = route.handler
        type_info = dict()
        endpoint = self._extract_pattern(route, parents)
        info["endpoint"] = endpoint
        info["name"] = self._get_name(route, endpoint)
        info["method"] = route.method
        info["comment"] = self._extract_comment(handler.__doc__)
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
                model_params = self._get_params_attr(param, handler.__doc__)
                # 用户指定了从表单中过来的model而不是json
                if model_params["type"] == "form":
                    model_params["type"] = self._get_module_class_name(
                        param.annotation)
                    self._inline_example(model_params)
                    form_params[param.name] = model_params
                else:
                    json_params = model_params
                    json_params["model_type"] = self._get_module_class_name(
                        param.annotation)
                self._enrich_type_info(sign.return_annotation, type_info)

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
            info["return_class"] = sign.return_annotation
            self._enrich_type_info(sign.return_annotation, type_info)

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
            info["return_wrapped"] = return_wrapped

            if "return_type" in info:
                info["return_type"] = '{"code": %s, "%s": %s, "message": "xx"}' \
                                      % (return_wrapped["success_code"],
                                         return_wrapped["success_key_name"],
                                         info["return_type"])
        return info

    def _is_type_like_class(self, cls):
        if hasattr(cls, "__args__"):
            for cls in cls.__args__:
                ret_val = self._is_type_like_class(cls)
                if ret_val:
                    return True
        else:
            return issubclass(cls, Type)

    def _enrich_type_info(self, cls, type_info):
        for cls, info in self._get_type_info(cls):
            if issubclass(cls, Type):
                type_info[self._get_module_class_name(cls)] = info

    @classmethod
    def _extract_param_desc(cls, docstring, param_name):
        regex = cls.regex_format(type="param", param_name=param_name)
        mth = re.search(regex, docstring, re.DOTALL)

        if mth:
            return mth.group(1).strip()

    @classmethod
    def _extract_param_type(cls, docstring, param_name):
        regex = cls.regex_format(type="type", param_name=param_name)
        mth = re.search(regex, docstring, re.DOTALL)

        if mth:
            return mth.group(1).strip()

    def _extract_param_example(self, docstring, param_name):
        regex = self.regex_format("ex", param_name, "(\s*?`+[^`]+?`+)")
        examples = [self._adjust_example(e) for e in re.findall(
            regex, docstring, re.DOTALL)]
        # 为短示例增加序号
        if len(examples) > 1 and "```" not in examples[0]:
            examples = ["%d. %s" % (i + 1, self._adjust_example(e))
                        for i, e in enumerate(examples)]
        return examples

    @classmethod
    def _extract_comment(cls, docstring):
        if not docstring:
            return ""

        mth = re.search(rf"^\s+(.*?){cls.regex_tail}", docstring, re.DOTALL)

        if mth:
            return mth.group(1).strip()

    def _get_params_attr(self, param, doc):
        attributes = dict()

        if param.default != inspect._empty:
            attributes["default"] = param.default
        attributes["type"] = self.param_annotation_mapping.get(
            param.annotation, param.annotation.__name__)

        if doc:
            attributes["type"] = self._extract_param_type(
                doc, param.name) or attributes["type"]
            desc = self._extract_param_desc(doc, param.name)
            if desc:
                attributes["desc"] = desc.strip()
            attributes["examples"] = self._extract_param_example(doc,
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

    @staticmethod
    def _get_module_class_name(cls):
        if isinstance(cls, (typing.GenericMeta, typing._Union)):
            return str(cls)
        elif issubclass(cls, Type):
            return f"{cls.__module__}.{cls.__name__}"
        else:
            return cls.__name__

    def _get_type_info(self, cls):
        if issubclass(cls, Type):
            type_info = self._extract_type_annotation(cls)
            yield cls, type_info
        elif hasattr(cls, "__args__"):
            for cls in getattr(cls, "__args__"):
                yield from self._get_type_info(cls)
        else:
            type_info = dict()
            yield cls, type_info

    @staticmethod
    def _extract_resp_info(return_wrapped):
        yield return_wrapped["success_code"], "返回成功"

        for item in (return_wrapped.get("error_info") or {}).items():
            yield item

    @staticmethod
    def _enrich_params_from_example(attributes, params, name):
        examples = attributes.get("examples")
        for example in examples:
            try:
                ex_data = json.loads(example.strip("`json"))

                for ex_name, ex in ex_data.items():
                    param = dict()
                    param.setdefault(
                        "examples", []).append(f"`{json.dumps(ex)}`")
                    param["type"] = type(ex).__name__
                    param["desc"] = attributes["desc"]
                    params[ex_name] = param
            except json.JSONDecodeError as e:
                print(f"Example format error "
                      f"of {attributes['endpoint']} :{name}")
                raise e

    @staticmethod
    def _inline_example(params):
        for index, ex in enumerate(params.get("examples", [])[:]):
            ex = '`' + ex.strip("`json").replace("\n", " ").strip() + '`'
            params.get("examples")[index] = ex
