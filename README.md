# apistellar WEB框架

## Badge

### GitHub

[![GitHub followers](https://img.shields.io/github/followers/shichaoma.svg?label=github%20follow)](https://github.com/shichao.ma)
[![GitHub repo size in bytes](https://img.shields.io/github/repo-size/shichaoma/apistellar.svg)](https://github.com/shichaoma/apistellar)
[![GitHub stars](https://img.shields.io/github/stars/shichaoma/apistellar.svg?label=github%20stars)](https://github.com/shichaoma/apistellar)
[![GitHub release](https://img.shields.io/github/release/shichaoma/apistellar.svg)](https://github.com/shichaoma/apistellar/releases)
[![Github commits (since latest release)](https://img.shields.io/github/commits-since/shichaoma/apistellar/latest.svg)](https://github.com/shichaoma/apistellar)

[![Github All Releases](https://img.shields.io/github/downloads/shichaoma/apistellar/total.svg)](https://github.com/shichaoma/apistellar/releases)
[![GitHub Release Date](https://img.shields.io/github/release-date/shichaoma/apistellar.svg)](https://github.com/shichaoma/apistellar/releases)

### PyPi

[![PyPI](https://img.shields.io/pypi/v/apistellar.svg)](https://pypi.org/project/apistellar/)
[![PyPI - Wheel](https://img.shields.io/pypi/wheel/apistellar.svg)](https://pypi.org/project/apistellar/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/apistellar.svg)](https://pypi.org/project/apistellar/)
[![PyPI - Format](https://img.shields.io/pypi/format/apistellar.svg)](https://pypi.org/project/apistellar/)
[![PyPI - Implementation](https://img.shields.io/pypi/implementation/apistellar.svg)](https://pypi.org/project/apistellar/)
[![PyPI - Status](https://img.shields.io/pypi/status/apistellar.svg)](https://pypi.org/project/apistellar/)

## Desc

apistellar是基于apistar的web构建工具，同时增强了apistar的功能，使用apistellar可以轻松构建适合生产环境的web项目。

apistellar部分设计灵感参考ruby on rails

除了apistar本身的特性以外，apistellar增加如下几点高级用法：

- CSM架构，将控制层，业务层，模型层完全分离，耦合性降至最低。
- 模板式定制各类模型，轻松扩展模型定义的模板类。
- 适配sphinx注释语法，使用构建命令一键生成api文档。
- 集成flask版的session实现。
- 自带一些event hook，轻松集成异常、session处理。
- 集成配置模块，集中管理所有配置信息。
- 离线任务管理，同一web服务下的离线任务，轻松复用web模块定义的model, service等等可注入对象。模板一键创建。
- 集成IPython交互式命令行工具，自动注入model, service等对象。提供异步代码执行能力，轻松调试各模块。
- 提供上传文件流对象，对大文件上传完美支持。
- Apistar作者在uvicorn中提供了websocket支持，但是未集成到apistar中，apistellar对二者进行了集成，完美支持websocket。

## Install
```
# python 3.6 required
pip install apistellar
```

## Doc
### 目录

1. [Quick Start](https://github.com/ShichaoMa/apistellar/wiki/Quick-Start)
2. [apistellar项目组成](https://github.com/ShichaoMa/apistellar/wiki/apistellar项目组成)
3. [model的使用方法](https://github.com/ShichaoMa/apistellar/wiki/model的使用方法)
4. [controller的使用方法](https://github.com/ShichaoMa/apistellar/wiki/controller的使用方法)
5. [service的使用方法](https://github.com/ShichaoMa/apistellar/wiki/service的使用方法)
6. [Session管理](https://github.com/ShichaoMa/apistellar/wiki/Session管理)
7. [使用require实现简单session认证](https://github.com/ShichaoMa/apistellar/wiki/使用require实现简单session认证)
8. [增强的EventHook](https://github.com/ShichaoMa/apistellar/wiki/增强的EventHook)
9. [错误码处理](https://github.com/ShichaoMa/apistellar/wiki/错误码处理)
10. [配置信息管理](https://github.com/ShichaoMa/apistellar/wiki/配置信息管理)
11. [自定义项目构建任务](https://github.com/ShichaoMa/apistellar/wiki/自定义项目构建任务)
12. [solo任务(离线任务)](https://github.com/ShichaoMa/apistellar/wiki/solo任务(离线任务))
13. [使用集成的IPython进行异步代码的调试](https://github.com/ShichaoMa/apistellar/wiki/使用集成的IPython进行异步代码的调试)
14. [大文件上传下载](https://github.com/ShichaoMa/apistellar/wiki/大文件上传下载)
15. [使用websocket进行通讯](https://github.com/ShichaoMa/apistellar/wiki/使用websocket进行通讯)
16. [使用apistellar测试插件pytest-apistellar进行单元测试](https://github.com/ShichaoMa/apistellar/wiki/使用apistellar测试插件pytest-apistellar进行单元测试)
17. [model持久化方案](https://github.com/ShichaoMa/apistellar/wiki/model%E6%8C%81%E4%B9%85%E5%8C%96%E6%96%B9%E6%A1%88)
18. [API接口文档自动生成](https://github.com/ShichaoMa/apistellar/wiki/API接口文档自动生成)
19. [RESTFul RPC客户端驱动包一键生成](https://github.com/ShichaoMa/apistellar/wiki/RESTFul-RPC客户端驱动包一键生成)

参考资料

- [asgi web框架 APIStar----终于等到你...](https://zhuanlan.zhihu.com/p/36297606)
- [妈妈再也不用担心我不写文档了，RESTful API文档一键生成！](https://zhuanlan.zhihu.com/p/55784077)
- [RESTful服务构建利器apistellar深度剖析](https://zhuanlan.zhihu.com/p/41843954)
- [asgi协议](https://github.com/django/asgiref/blob/master/specs/www.rst)
