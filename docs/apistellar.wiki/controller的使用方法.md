controller通常定义在模块根目录controller.py中。

controller层主要定义了对外的接口。
```python
@route("", name="article")
class ArticleController(Controller, SettingsMixin):
    """
    文章相关的api
    """
    def __init__(self):
        # 通过在controller中初始化service会失去service的注入功能，
        # service全局唯一，无法随请求的改变而改变。
        # 但好处是不用每次请求重新创建service对象了。
        # 对于不需要注入属性能service可以使用此方案。
        self.service = ArticleService()

    @get("/import")
    async def _import(self, app: App, session: Session):
        """
        导入文章
        :param app:
        :param session:
        :return: 导入文章页面
        """
        if not session.get("login"):
            return app.render_template("login.html", ref="import")
        else:
            return app.render_template("import.html", success="")

    @post("/check")
    async def check(self,
                    app: App,
                    article: Article,
                    username: FormParam,
                    password: FormParam,
                    ref: FormParam,
                    session: Session) -> str:
        """
        检查用户名和密码是否正确
        :param app:
        :param article:
        :ex article:
        ```json
        {"title": "xxx"}
        ```
        :type article: form
        :param username: 用户名
        :ex username: `test`
        :param password: 密码
        :ex password: `12345`
        :param ref: 从哪里跳过来的
        :param session:
        :return: 返回网页
        """
        # article由于没有经过format会带有多余的信息
        if username == self.settings["USERNAME"] and \
                password == self.settings["PASSWORD"]:
            session["login"] = f'{username}:{password}'
            if ref == "edit" and hasattr(article, "id"):
                article = await article.load()
            if ref:
                return app.render_template(
                    f"{ref}.html", success="", **article.to_dict())
            else:
                return redirect(app.reverse_url("view:welcome:index"))
        else:
            return app.render_template(
                "login.html", **article.to_dict())

```
controller中使用了两种装饰器方法

route：指定了该controller当前的uri，如果controller继承自其它controller，uri也会被连接。
get, post等：指定了该方法是一个Http 方法请求绑定的视图函数，第一个参数是url，同时会连接上controller的uri，省略的话url为/{方法名}。一个方法可以使用多个http请求方法装饰器。

controller中的action方法一般会调用注入的service对象，来完成复杂的业务逻辑。