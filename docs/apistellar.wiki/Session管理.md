原生的apistar并没有session支持，apistellar将flask的session实现融合到了apistar中，我们可以很轻松的使用session。

通过apistellar构建的项目，session是可以被直接注入的：
```python
from apistar import http, App
from apistellar.helper import redirect, return_wrapped
from apistellar import Controller, route, get, post, \
    Session, FormParam, SettingsMixin, require, UrlEncodeForm, MultiPartForm

from .article import Article
from blog.utils import project_path, decode
from .service import ArticleService


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

```
我们可以像使用flask中的session一样使用被注入的session。
session的一些参数可以在settings.py中配置。