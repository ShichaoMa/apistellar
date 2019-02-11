当今大多数公司进行业务开发时都使用微服务架构，通过apistellar创建的项目，可以一键为其生成基于http协议的PRC client。RPC生成与文档生成机制如出一辙，都是首先通过解析控制层的hanlder来获取接口信息，随后将接口信息渲染成文档或RPC client。

## 生成方法
```
usage: apistar-create rpc [-h] [-t TEMPLATES] -m MODULE [-l LOCATION]
                          [-p PARSER] [-b BASE] [-ct CONN_TIMEOUT]
                          [-rt READ_TIMEOUT]
                          name

positional arguments:
  name                  输出名称

optional arguments:
  -h, --help            show this help message and exit
  -t TEMPLATES, --templates TEMPLATES
                        模板路径.
  -m MODULE, --module MODULE
                        模块地址
  -l LOCATION, --location LOCATION
                        输出地址
  -p PARSER, --parser PARSER
                        parser模块地址
  -b BASE, --base BASE  rpc基类 eg：apistellar.helper:RestfulApi
  -ct CONN_TIMEOUT, --conn-timeout CONN_TIMEOUT
                        连接超时时间， 单位：秒
  -rt READ_TIMEOUT, --read-timeout READ_TIMEOUT
                        数据读取时间， 单位：秒
```
其中几个参数稍作解释：
- -b: 指定一个rpc继承基类，此基类需要提供一个名叫url的方法，接收URL地址中path部分，返回完整的带域名地址和协议的URL，该基类可以提供一些互环境相关的路径域名地址获取方法。
- -p: 和文档生成的解析器共用，不需要手动指定
通过`apistar-create rpc blog -m blog -l ../docs`指令可以一键生成blog项目的客户端驱动。
生成的目录结构如下：
```
.
|______init__.py
|____welcome.py
|____article.py
```
其中`__init__.py`中为多继承了各个模块类的项目类：
```python
# blog API
from .welcome import Welcome
from .article import Article


class Blog(Welcome, Article):
    pass
```
各模块类中定义了具体的调用逻辑，如`welcome.py`：
```python
# 欢迎页 PRC调用
import typing

from apistellar.helper import register
from aiohttp import ClientSession, FormData
from apistellar.helper import RestfulApi


class Welcome(RestfulApi):
    # 这个url会被连接上域名和注册的endpoint之后注入到方法中使用。
    url = None  # type: str
    session = None  # type: ClientSession

    @register("/", conn_timeout=10)
    async def index(self, path: str=None, cookies: dict=None):
        params = dict()
        if path is not None:
            params["path"] = path
        resp = await self.session.get(self.url, params=params)
        return await resp.read()

    @register("/upload_image", conn_timeout=10)
    async def upload_image(self, form_fields: typing.List[dict], cookies: dict=None):
        data = FormData()
        for meta in form_fields:
            data.add_field(meta["name"],
                           meta["value"],
                           filename=meta.get("filename"),
                           content_type=meta.get("content_type"))
        resp = await self.session.post(self.url, data=data)
        return await resp.read()

    @register("/a/{b}/{+path}", conn_timeout=10, have_path_params=True)
    async def a_b_path(self, path_params: dict, cookies: dict=None):
        resp = await self.session.post(self.url)
        return await resp.read()
```
驱动是使用aiohttp实现的，可以通过自定义task继承于APIRenderTask来实现不同的客户端。
## 驱动的用法
实例化驱动对象之后，可直接调用各接口方法
### 注册机制
每个接口方法都使用register来完成访问地址的组装和session对象的初时化，随后会被添加到self中。
register装饰器有以下几个参数可以设置：
- url: 对应的服务端的endpoint
- path: 在返回的响应数据中，如果是json格式，有用数据位置如`data.value`对应{"data": {"value": "有用的数据"}}，非json不需要填写。
- error_check: 在返回的响应数据中，如果是json格式，用来检查该json是否有效的回调函数，一般会配合响应码来检查。
- conn_timeout: 连接超时时间
- read_timeout: buffer读取(下载)的最大时间
- have_path_param: 是否有restful风格的路径参数
register的参数传递会在一键生成时根据命令行参数或解析出来的接口信息来生成。
### 接口参数说明
- http协议中的查询参数是以位置参数的形式存在的，类型限定为字符串。
- http协议中的Form表单是以字典列表的形式存在的，参数名为`form_fields`。
- http协议中的json请求体是以字典的形式存在的，参数名为`json`。
- restful的路径参数是以字典的形式存在的，参数名为`path_params`。由于组装url是在register装饰器中实现的，所以需要path_params没有被接口直接用到，但还是需要传入的。
- 同时还增加了一个关键字参数cookies，类型为字典，用来增加基于cookie的session认证。由于session初始化是在register装饰器中实现的，所以虽然cookie没有被接口函数直接用到，但还是需要传入的。
### 更多示例
[blog](https://github.com/ShichaoMa/blog/blob/master/docs/blog)