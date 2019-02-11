有的时候我们可能需要进行离线任务开发，离线任务的执行有可能依赖于现有的web项目模块。离线任务做为一个独立的程序运行，并且共用web模块中定义的model, service等等，这是我们这节所要介绍的内容。

从0.5.0开始，apistellar支持了solo任务的创建。

下面让我们开始创建一个solo任务吧。

首先我们进入一个已存在的web项目的开始目录(web_app.py所在目录），执行如下命令：
```bash
➜  blog git:(dev_star) ✗ apistar-create solo searcher
/Users/mashichao/projects/py3/blog/blog/solo_app.py已存在，是否覆盖y/n?n
searcher 已创建。
➜  blog git:(dev_star) ✗ apistar-create solo test1 test2
/Users/mashichao/projects/py3/blog/blog/solo_app.py已存在，是否覆盖y/n?n
/Users/mashichao/projects/py3/blog/blog/solo_app.py已存在，是否覆盖y/n?n
test1、test2 已创建。
```
可以一次创建多个solo任务，但solo_app是共用的。

让我们看一下执行选项。
```bash
➜  blog git:(dev_star) ✗ python solo_app.py -h
usage: solo_app.py [-h] {searcher,test1,test2,import} ...

独立任务程序构建工具

positional arguments:
  {searcher,test1,test2,import}
                        创建独立任务服务类型.
    searcher
    test1
    test2
    import

optional arguments:
  -h, --help            显示帮助信息并退出.
Command 'searcher'
usage: solo_app.py searcher [-h] [--settings SETTINGS]

Command 'test1'
usage: solo_app.py test1 [-h] [--settings SETTINGS]

Command 'test2'
usage: solo_app.py test2 [-h] [--settings SETTINGS]

Command 'import'
usage: solo_app.py import [-h] [--settings SETTINGS] paths [paths ...]
```
生成的solo任务类定义在任务同名包的__init__.py中。格式如下：
```python
from apistellar import Solo


class Searcher(Solo):

    async def setup(self):
        """
        初始化
        :return:
        """

    async def run(self):
        """
        业务逻辑
        :return:
        """

    async def teardown(self):
        """
        回收资源
        :return:
        """

    @classmethod
    def enrich_parser(cls, sub_parser):
        """
        自定义命令行参数，若定义了，则可通过__init__获取
        注意在__init__中使用kwargs来保留其它参数，并调用父类的__init__
        :param sub_parser:
        :return:
        """

```
我们可以按注释提示编写相应代码，如下所示。
```python
from apistellar import Solo

from ..lib import Sqlite
from ..article.article import Article


class Searcher(Solo):

    def __init__(self, id, **kwargs):
        super(Searcher, self).__init__(**kwargs)
        self.id = id

    async def setup(self, sqlite: Sqlite):
        """
        初始化
        :return:
        """
        Article.init(sqlite=sqlite)

    async def run(self):
        """
        业务逻辑
        :return:
        """
        article = Article()
        article.id = self.id
        await article.load()
        print(article.article)

    async def teardown(self):
        """
        回收资源
        :return:
        """

    @classmethod
    def enrich_parser(cls, sub_parser):
        """
        自定义命令行参数，若定义了，则可通过__init__获取
        注意在__init__中使用kwargs来保留其它参数，并调用父类的__init__
        :param sub_parser:
        :return:
        """
        sub_parser.add_argument("-i", "--id", help="文件的主键")


```
然后我们执行
```bash
➜  blog git:(dev_star) ✗ python solo_app.py searcher -i 20170710214424
2018/07/08 16:25:05.202 manager.py[line:121] INFO: Starting worker [66469]
[comment]: <> (![](https://core-electronics.com.au/media/kbase/raspberry-pi-workshop-cover.png))
### 使用 vi 编辑文件，增加下列配置项`vi /etc/dhcpcd.conf`



    # 指定接口 eth0
    interface eth0
    # 指定静态IP，/24表示子网掩码为 255.255.255.0
    static ip_address=192.168.1.20/24
    # 路由器/网关IP地址
    static routers=192.168.1.1
    # 手动自定义DNS服务器
    static domain_name_servers=114.114.114.114


### 修改完成后，按esc键后输入 :wq 保存。重启树莓派就生效了



    sudo reboot



2018/07/08 16:25:05.208 manager.py[line:152] WARNING: Stopping [66469]
➜  blog git:(dev_star) ✗
```