# APIStar 项目及服务模块集成构建工具
star-builder是基于apistar的web构建工具，同时增强了apistar的功能，使用star-builder可以轻松构建适合生产环境的web项目。
star_builder部分灵感参考ruby on rails
除了apistar本身的特性以外，star_builder增加如下几点高级用法：

- CSM架构，将控制层，业务层，模型层完全分离，耦合性降至最低。
- 模板式定制各类模型，轻松扩展模型定义的模板类。
- 集成flask版的session实现。
- 自带一些event hook，轻松集成异常、session处理。
- 集成配置模块，集中管理所有配置信息。
- 离线任务管理，同一web服务下的离线任务，轻松复用web模块定义的model, service等等可注入对象。模板一键创建。
- 集成IPython交互式命令行工具，自动注入model, service等对象。提供异步代码执行能力，轻松调试各模块。


# INSTALL
```
# python 3.6+ required
pip install star_builder
```

# DOC
## 目录

- [Quick Start](https://github.com/ShichaoMa/star_builder/wiki/Quick-Start)
- [star_builder项目组成](https://github.com/ShichaoMa/star_builder/wiki/star_builder项目组成)
- [model的使用方法](https://github.com/ShichaoMa/star_builder/wiki/model的使用方法)
- [model component的使用方法](https://github.com/ShichaoMa/star_builder/wiki/model-component的使用方法)
- [controller的使用方法](https://github.com/ShichaoMa/star_builder/wiki/controller的使用方法)
- [service的使用方法](https://github.com/ShichaoMa/star_builder/wiki/service的使用方法)
- [Session管理](https://github.com/ShichaoMa/star_builder/wiki/Session管理)
- [使用require实现简单session认证](https://github.com/ShichaoMa/star_builder/wiki/使用require实现简单session认证)
- [增强的EventHook](https://github.com/ShichaoMa/star_builder/wiki/增强的EventHook)
- [错误码处理](https://github.com/ShichaoMa/star_builder/wiki/错误码处理)
- [配置信息管理](https://github.com/ShichaoMa/star_builder/wiki/配置信息管理)
- [自定义项目构建任务](https://github.com/ShichaoMa/star_builder/wiki/自定义项目构建任务)
- [solo任务(离线任务)](https://github.com/ShichaoMa/star_builder/wiki/solo任务(离线任务))
- [使用集成的IPython进行异步代码的调试](https://github.com/ShichaoMa/star_builder/wiki/使用集成的IPython进行异步代码的调试)

参考资料

[asgi web框架 APIStar----终于等到你...](https://zhuanlan.zhihu.com/p/36297606)
