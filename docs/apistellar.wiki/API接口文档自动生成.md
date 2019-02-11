从apistellar>=1.1.0开始，apistellar开始支持生成API接口文档。通过`apistar-create document -m 要为哪个项目模块生成文档 -l 文档所以路径 文档名称`来为一个项目创建API文档
# 用法
具体命令如下：
```
(blog) ➜  blog git:(master) ✗ apistar-create document -h
usage: apistar-create document [-h] [-t TEMPLATES] -m MODULE [-l LOCATION]
                               [-p PARSER]
                               name

positional arguments:
  name                  文档名称

optional arguments:
  -h, --help            show this help message and exit
  -t TEMPLATES, --templates TEMPLATES
                        模板路径.
  -m MODULE, --module MODULE
                        模块地址
  -l LOCATION, --location LOCATION
                        文章地址
  -p PARSER, --parser PARSER
                        parser模块地址
``` 
如上所示：
- -t为使用的模板路径，一般来说使用默认模板即可。
- -m为项目包地址，如我的博客项目，在项目根目录，通过`pip install -e .`安装之后，blog作为一个模块被安装到了python可搜索路径下，所以`-m blog`就可以指定为其生成文档。
- -l为生成的文档所在路径。
- -p为controller解析器类对应的路径，通过`module:class`的形式指定，一般来说使用默认解析器即可。
# 展示
在创建完文档之后，我们可以在指定文档路径下找到以`name`命名的文档文件夹, 如[blog-api文档](https://github.com/ShichaoMa/blog/tree/master/docs/我的博客API文档)
以每个controller为单位各自生成一个文档文件夹及文档文件，md和html格式各一份。同时还会在根目录生成一个index文件，用来索引文档。index.html会被自动打开，接下来我们就可以浏览文档了。
# 文档组成
接下来我们将以[blog-api文档](https://github.com/ShichaoMa/blog/blob/master/docs/我的博客API文档/article/%E6%96%87%E7%AB%A0%E7%9B%B8%E5%85%B3%E7%9A%84api.md)为例来讲解文档的语法及生成规范。

apistellar项目API文档主要分主两大部分：模型定义和接口定义
## 1.模型定义

### blog.article.article.Article
字段名|类型|是否必须|是否可为空值|默认值|描述|示例
:--|:--|:--|:--|:--|:--|:--
title|String|是|否||标题|
id|String|否|否|20190120000658|每篇文章的唯一id，日期字符串的形式表示|
tags|Tags|是|否||关键字|`["python", "apistellar"]`
description|String|否|否||描述信息|
author|String|否|否|夏洛之枫|作者信息|
feature|Boolean|否|否|False|是否为精品|
created_at|Timestamp|否|否|1547914018.668977|创建时间|
updated_at|Timestamp|否|否|1547914018.669005|更新时间|
show|Boolean|否|否|True|是否在文章列表中展示|
article|String|否|否||文章正文|

这部分主要声明了文档接口中可能会引用到的模型，这部分详细说明了模型的定义。其数据主要来源于该模型的各种字段参数和注释。代码中的模型是如下定义的：
```python
class Article(PersistentType, SqliteDriverMixin, SettingsMixin):
    """
    文章模型
    :param title: 标题
    :ex `我的主页`
    :param id: 每篇文章的唯一id，日期字符串的形式表示
    :param tags: 关键字
    :ex tags:
    `["python", "apistellar"]`
    :param description: 描述信息
    :param author: 作者信息
    :param feature: 是否为精品
    :ex feature: True/False
    :param updated_at: 更新时间
    :param created_at: 创建时间
    :param show: 是否在文章列表中展示
    :ex show: True/False
    :param article: 文章正文
    """
    TABLE = "articles"

    title = validators.String()
    id = validators.String(default=get_id)
    tags = Tags()
    description = validators.String(default="")
    author = validators.String(default=settings_wrapper.settings["AUTHOR"])
    feature = Boolean(default=False)
    created_at = Timestamp(default=datetime.datetime.now().timestamp)
    updated_at = Timestamp(default=datetime.datetime.now().timestamp)
    show = Boolean(default=True)
    article = validators.String(default=str)

```
`:param`样式为rst标准注释规范，使用pycharm会默认生成该样式的注释。而`:ex`样式为我定制的扩展注释，其后通过markdown语法反引号来指定一段示例。上述注释是可以省略的，但不推荐，完善的注释才能生成规范的文档。
需要注意的一点是，当字段的default属性等于一个工厂函数时，在生成文档时默认值一栏会被填充为工厂的返回值。

## 接口定义

接口定义部分描述了每个接口的具体信息，其中包括url、method、查询参数、路径参数、表单参数、json请求体、返回信息、返回响应码等模块。url和method一目了然，下面将分别介绍以上模块。
### 查询参数
查询参数是指一次请求，URL`?`号后面的参数如?a=1&b=2，通过在handler中指定`http.QueryParam`或`http.QueryParams`类型，来自动生成查询参数表格。如：
```python
    @get("/")
    def index(self, app: App, path: QueryParam) -> str:
        """
        首页
        :param app:
        :param path: 子路径
        :ex path:
        `"/article?a=3"`
```
上述handler在定义时指定了一个查询参数path，文档生成器会解析上述参数列表及注释生成如下文档：
#### URL: /
#### 方法: GET

#### 查询参数:
参数名|类型|是否必须|默认值|描述|示例
:--|:--|:--|:--|:--|:--
path|str|是||子路径|`"/article?a=3"`

而当handler在定义时使用了`http.QueryParams`时，如：
```python
    @post("/a/{+path}")
    def test(self, b: http.QueryParams, path: str):
        """
        测试
        :param b: 测试QueryParams
        :ex b:
        ```json
        {"a": 1, "b": 2}
        ```
        """
```
文档生成器会解析注释中的json，将其分解成两个参数并分别描述其性质。如：

#### URL: /a/{+path}
#### 方法: POST

#### 查询参数:
参数名|类型|是否必须|默认值|描述|示例
:--|:--|:--|:--|:--|:--
a|int|是|||`1`
b|int|是|||`2`

### 路径参数
路径参数决定了handler将从URL中提取部分路径作为参数。如：
```python
    @post("/a/{+path}")
    def test(self, path: str):
        """
        测试
        :param path: 传个地址
```
文档生成器会生成如下文档：
#### 路径参数:
参数名|类型|是否必须|默认值|描述|示例
:--|:--|:--|:--|:--|:--
path|path|是||传个地址|

### 表单参数
表单参数为form中的参数，其可通过指定`apistellar.FormParam`、`apistellar.FileStream`的形式接参。如：
```python
    @post("/a/{+path}")
    def test(self, name: FormParam):
        """
        测试
        :param name: 输入名字
        :ex name: `abcd`

```
其渲染出来的文档如下：
#### 表单参数:
参数名|类型|是否必须|默认值|描述|示例
:--|:--|:--|:--|:--|:--
name|str|是||输入名字|`abcd`

我们可能在上传文件时会使用`apistellar.FileStream`组件，如：
```python
    @post("/test/b")
    def test(self, stream: FileStream):
        """

        :param stream: 这一个文件流
        :return:
        """
```
其渲染出来的文档如下：
#### 表单参数:
参数名|类型|是否必须|默认值|描述|示例
:--|:--|:--|:--|:--|:--
`file1`, `file2`, ...|file|是||这一个文件流|

模型是可以用于form接参的，如：
```python
    @post("/check")
    async def check(self, article: Article):
        """
        检查用户名和密码是否正确
        :param article:
        :ex article:
        ```json
        {"title": "xxx"}
        ```
        :type article: form
```
其渲染出来的文档如下：
#### 表单参数:
参数名|类型|是否必须|默认值|描述|示例
:--|:--|:--|:--|:--|:--
article|blog.article.article.Article|是|||`{"title": "xxx"}`

注意，由于模型的接参机制是针对所有请求体的，所以`Content-Type=application/json`的请求也会被处理，因此`:type article: form`必须指定。否则，文档会被被识别为json请求体。
### json请求体
对于主打RESTful API WEB程序开发的apistellar，post json请求体的情况应该是最常见的，如：
```python
    @post("/a/{+path}")
    def test(self, data: http.RequestData):
        """
        测试
        :param data: post过来的参数集合
        :ex data:
        ```json
        {"a": 1}
        ```
        :ex data:
        ```json
        {"ab": 1}
        ```
        """
```
其渲染出来的文档如下：

#### json请求体

##### 请求描述
post过来的参数集合



##### 请求示例


###### 示例1

```json
        {"a": 1}
```


###### 示例2

```json
        {"ab": 1}
```
与上节类似，模型是可以用于json接参的，如：
```python
    @post("/a/{+path}")
    def test(self, data: Article):
        """
        测试
        :param data: post过来的参数集合
        """
```
渲染出的来的文档如下：
#### json请求体

##### 请求描述
post过来的参数集合

##### 模型类型
blog.article.article.Article


我们可以从模型定义部分找到相应的模型来了解模型约束。
### 返回信息
通过返回类型及注释可以生成用于描述返回信息的文档，如：
```python
    @post("/a/{+path}")
    @return_wrapped(error_info={1: "错误1", 2: "错误2"})
    def test(self, data: Article) -> typing.List[Article]:
        """
        测试
        :param data: post过来的参数集合
        :ex data:
        ```json
        {"a": 1}
        ```
        :ex data:
        ```json
        {"ab": 1}
        ```
        :return:
        ```json
        {"code": 0, "data": {"a": 1}}
        ```
        """
        return [data]
```
通过`:return:`来定义返回示例，` -> typing.List[Article]`指明了返回类型，`@return_wrapped()`存在的意义在于为返回值增加一层响应码信息，默认增加的格式为`{"code": 0, "data": 返回值}`，通过关键字参数`success_key_name`可以改变返回值的key名称`data`，通过关键字参数`success_code`可以改变成功时的响应码`0`，同时装饰器还支持`error_info`关键字参数，其指向一个异常响应码和异常信息字典，其存在的意义仅是用来生成返回码信息。下面是一个返回信息文档示例：
#### 返回信息
##### 返回类型
{"code": 0, "data": typing.List[blog.article.article.Article], "message": "xx"}



##### 返回示例


```json
        {"code": 0, "data": {"a": 1}}
```



#### 返回响应码
响应码|描述
:--|:--
0|返回成功
1|错误1
2|错误2