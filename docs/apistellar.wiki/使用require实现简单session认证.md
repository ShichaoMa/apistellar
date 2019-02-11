apistellar提供了一个require装饰器来实现简单认证
```
def require(
        container_cls=Session,
        judge=lambda x: x.user,
        error="Login required!"):
    """
    装饰一个可被注入的函数，注入container_cls的实例，
    并调用judge判断其是否符合条件，否则抛出异常，
    异常信息为error。
    :param container_cls:
    :param judge:
    :param error:
    :return:
    """
```
正如注释所示，我们可以用来验证session中的user属性是否为真，否则认为用户没有登录。container_cls必须是可注入的。此装饰器可以被用到action或hook的三种on_方法中。require装饰器必须是最里层的装饰器。