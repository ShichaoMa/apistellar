# apistellar WEB框架

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

# INSTALL
```
# python 3.6 required
pip install apistellar
```

# DOC
## 目录

- [Quick Start](https://github.com/ShichaoMa/apistellar/wiki/Quick-Start)
- [apistellar项目组成](https://github.com/ShichaoMa/apistellar/wiki/apistellar项目组成)
- [model的使用方法](https://github.com/ShichaoMa/apistellar/wiki/model的使用方法)
- [controller的使用方法](https://github.com/ShichaoMa/apistellar/wiki/controller的使用方法)
- [service的使用方法](https://github.com/ShichaoMa/apistellar/wiki/service的使用方法)
- [Session管理](https://github.com/ShichaoMa/apistellar/wiki/Session管理)
- [使用require实现简单session认证](https://github.com/ShichaoMa/apistellar/wiki/使用require实现简单session认证)
- [增强的EventHook](https://github.com/ShichaoMa/apistellar/wiki/增强的EventHook)
- [错误码处理](https://github.com/ShichaoMa/apistellar/wiki/错误码处理)
- [配置信息管理](https://github.com/ShichaoMa/apistellar/wiki/配置信息管理)
- [自定义项目构建任务](https://github.com/ShichaoMa/apistellar/wiki/自定义项目构建任务)
- [solo任务(离线任务)](https://github.com/ShichaoMa/apistellar/wiki/solo任务(离线任务))
- [使用集成的IPython进行异步代码的调试](https://github.com/ShichaoMa/apistellar/wiki/使用集成的IPython进行异步代码的调试)
- [大文件上传下载](https://github.com/ShichaoMa/apistellar/wiki/大文件上传下载)
- [使用websocket进行通讯](https://github.com/ShichaoMa/apistellar/wiki/使用websocket进行通讯)
- [使用apistellar测试插件pytest-apistellar进行单元测试](https://github.com/ShichaoMa/apistellar/wiki/使用apistellar测试插件pytest-apistellar进行单元测试)
- [model持久化方案](https://github.com/ShichaoMa/apistellar/wiki/model%E6%8C%81%E4%B9%85%E5%8C%96%E6%96%B9%E6%A1%88)
- [
API接口文档自动生成](https://github.com/ShichaoMa/apistellar/wiki/API%E6%8E%A5%E5%8F%A3%E6%96%87%E6%A1%A3%E8%87%AA%E5%8A%A8%E7%94%9F%E6%88%90)

参考资料

[asgi web框架 APIStar----终于等到你...](https://zhuanlan.zhihu.com/p/36297606)

[asgi协议](https://github.com/django/asgiref/blob/master/specs/www.rst)
