apistar使用event hook来为请求、响应和异常增加勾子。但apistar不支持从on_request on_response中直接返回请求来改变请求响应路径。
apistellar对event hook进行了增强。
```python
from apistellar import Session, Hook, Return


class SessionHook(Hook):
    order = 10

    def on_request(self, session: Session):
        if not session.get("login"):
            Return({"error": "没有登陆"})
```
通过上述代码，可以实现在请求之初验证是否登录，并返回指定的响应信息。

同时，apistellar增加了event hook的自动发现机制，通过继承Hook，来自动发现所有自定义Hook。为event hook增加类属性order，可以调整event hook的优先级。
