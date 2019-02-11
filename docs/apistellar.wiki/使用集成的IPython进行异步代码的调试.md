apistellar提供IPython集成，并赋予了在IPython中执行异步代码的能力。可以通过同步的方式调试异步代码。

使用apistar-console进行IPython
```python
➜  blog git:(master) ✗ apistar-console
Python 3.6.5 (default, Apr  5 2018, 11:02:32)
Type 'copyright', 'credits' or 'license' for more information
IPython 6.4.0 -- An enhanced Interactive Python. Type '?' for help.

In [1]: from apistar import http
In [2]: from blog.article.article import Article
# 创建一个Mocker对象
In [3]: mocker = Mocker()
# 添加mock，可以多次添加
In [4]: mocker.add_mock(http.RequestData, {"title": "24424"})
# mock
In [5]: mock(mocker)
注入一个article对象
In [6]: article = inject(Article)
# article可以为post请求体接参
In [7]: article
Out[7]: <Article(title='24424')>
# 清除mock数据
In [8]: self.clear()
# 重新mock
In [9]: mocker = Mocker()
In [10]: mocker.add_mock(http.RequestData, {"id": "20170710214424"})
In [11]: mock(mocker)
In [12]: article = inject(Article)
In [13]: article
Out[13]: <Article(id='20170710214424')>
# 从数据库中获取article的全部数据
In [14]: await(article.load())
Out[14]: <Article(id='20170710214424', description='树莓派配置静态ip', tags='raspberry', article='[comment]: <> (![](https://core-electronics.com.au/media/kbase/raspberry-pi-workshop-cover.png))\n### 使用 vi 编辑文件，增加下列配置项`vi /etc/dhcpcd.conf`\n\n    \n    \n    # 指定接口 eth0\n    interface eth0\n    # 指定静态IP，/24表示子网掩码为 255.255.255.0\n    static ip_address=192.168.1.20/24\n    # 路由器/网关IP地址\n    static routers=192.168.1.1\n    # 手动自定义DNS服务器\n    static domain_name_servers=114.114.114.114\n    \n\n### 修改完成后，按esc键后输入 :wq 保存。重启树莓派就生效了\n\n    \n    \n    sudo reboot\n    \n\n', author='夏洛之枫', title='树莓派手动指定静态IP和DNS', feature=1, created_at=1499694264, updated_at=1512737246, show=1)>
# 打印article中的article字段
In [15]: print(article.article)
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




In [16]: exit
```