### 下面让我开始创建一个完整的web项目

创建一个项目
```
➜  py3 rm -rf erp
➜  py3
➜  py3 apistar-create project erp
erp 已创建。
➜  py3 cd erp
➜  erp find . -print | sed -e 's;[^/]*/;|____;g;s;____|; |;g'
.
|____requirements.txt
|____MANIFEST.in
|____README.md
|____setup.py
|____README.rst
|____erp
| |____web_app.py
| |____tasks.py
| |______init__.py
| |____settings.py
| |____templates
| |____erp
| | |______init__.py
```
创建两个service模块
```
➜  erp cd src/erp/erp
➜  erp apistar-create service -h
usage: apistar-create service [-h] [-t TEMPLATES] name [name ...]

positional arguments:
  name                  服务模块名称

optional arguments:
  -h, --help            show this help message and exit
  -t TEMPLATES, --templates TEMPLATES
                        模板路径.
➜  erp apistar-create service user group
user、group 已创建。
➜  erp find . -print | sed -e 's;[^/]*/;|____;g;s;____|; |;g'
.
|____group
| |____controller.py
| |____service.py
| |______init__.py
|______init__.py
|____user
| |____controller.py
| |____service.py
| |______init__.py
```
创建两个model
```
➜  erp apistar-create model -h
usage: apistar-create model [-h] [-t TEMPLATES] [-d DRIVER] -n NAME [-p PATH]
                            [-a]
                            [fields [fields ...]]

positional arguments:
  fields                字段 eg: id:integer

optional arguments:
  -h, --help            show this help message and exit
  -t TEMPLATES, --templates TEMPLATES
                        模板路径.
  -n NAME, --name NAME  models名称
  -p PATH, --path PATH  所属服务路径 eg: article/comment
  -a, --async           是否拥有异步获取属性的能力
➜  erp apistar-create model -n user -p user id:integer name:string created_at:datetime updated_at:datetime
user 已创建。
➜  erp apistar-create model -n group -p group id:integer name:string created_at:datetime updated_at:datetime
group 已创建。
➜  erp find . -print | sed -e 's;[^/]*/;|____;g;s;____|; |;g'
.
|____group
| |____service.py
| |______init__.py
| |____group.py
|______init__.py
|____user
| |____controller.py
| |____service.py
| |____user.py
| |______init__.py
```
一个包含两个服务模块的项目就创建好了。

打开user/controller.py
```
from apistar import http
from apistellar import Controller, route, get, post


@route("/user")
class UserController(Controller):
    pass
```
我们加入以下代码
```
from apistar import http
from apistellar import Controller, route, get, post

from .user import User


@route("/user")
class UserController(Controller):

    @get("/")
    def hello(name: http.QueryParam):
        return {"hello": name}
```
执行以下命令
```
➜  erp cd ..
➜  erp apistar-routes
Name                                     Method  URI Pattern                              Controller#Action
view:usercontroller:hello                GET     /user/                                   user:UserController#hello
```
启动程序
```
➜  erp python web_app.py
DEBUG:apistellar.app:Route method: GET, url: /user/ to view:usercontroller:hello.
DEBUG:asyncio:Using selector: KqueueSelector
* Uvicorn running on http://127.0.0.1:8000 🦄 (Press CTRL+C to quit)
INFO:root:Started worker [65783]
```
注：也可以使用gunicorn启动`gunicorn -w 1 -k uvicorn.workers.UvicornWorker erp.web_app:app --reload -b :8000`

执行以下命令
```
➜  erp curl "http://127.0.0.1:8000/user/?name=tom"
{"hello":"tom"}
```
