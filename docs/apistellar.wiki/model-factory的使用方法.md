### 定义model factory
model同model factory通常定义在模块根目录下以model命名的文件中。
```python
class ArticleFactory(ModelFactory):
    model = Article

    async def product(self, 
                      form: RequestData,
                      id: QueryParam,
                      settings: FrozenSettings) -> Article:
        params = {}
        if not form:
            form = {}

        file = form.get("article")
        if hasattr(file, "read"):
            params["article"] = decode(file.read())
        else:
            params["article"] = file

        params["id"] = form.get("id") or id
        params["author"] = form.get("author") or settings.AUTHOR
        params["title"] = form.get("title") or \
                          file and file.filename.replace(".md", "")
        params["feature"] = eval(form.get("feature") or "False")
        params["description"] = form.get("description") or ""
        params["tags"] = form.get("tags") or ""
        return Article(params)
```
当Controller中的action的参数列表声明自己需要model时，会查找可以生产相应类型的Factory，并调用将生产结果注入。我们可以在product函数中创建并返回model对象。本质上Factory也是一个Component，product方法类似controller中的action，会根据参数列表从其它component中获取必要的参数。系统自带的可注入类型大都位于apistar.http中。同时还包括当前的controller，所有的service， 所有的Factory product方法的返回值，FrozenSettings, Mongo, Session, Cookie等等。当我们使用Factory创建一个model的时候，需要使用类属性model指明我们要为创建哪种类型的model。同时，Factory还会为model注入必须的属性：如
```python
class Article(Type):
    sqlite = inject << Sqlite
    TABLE = "articles"
    ...
```
上述声明方式，Factory会为Article类注入sqlite。以便在Article中实现CURD时使用。

这样定义的好处在于。某次请求可能都带来了id参数，需要将其转换成Article对象，比如/upload, /modify。model对象的创建被解耦到了Factory中。代码更易维护。

当然，我们还可以定义复杂一点的。
```python
class ArticleListFactory(ModelFactory):
    model = Article

    async def product(self,
                      ids: QueryParam,
                      _from: QueryParam,
                      size: QueryParam) -> typing.List[Article]:
        if ids:
            ids = ids.split(",")
        else:
            ids = []
        return await Article.load_list(ids, _from, size)
```
上述组件返回了一个 typing.List[Article] ，需要的action会将其引入。