service通常定义在模块根目录的service.py中。

service用来编写复杂的业务逻辑，这一个service的完整例子[article/service.py](https://github.com/ShichaoMa/blog/blob/master/src/blog/blog/article/service.py)

service可以选择继承于Service基类，这样我们可以通过左移语法来动态注入一些属性。可注入的service对象创建过程是隐式完成的，我们使用时直接注入就可以。尖当然，我们推荐在controller层直接实例化一个Service对象，虽然这样做注入会失效，但更多情况下Service不应该依赖于请求上下文。
