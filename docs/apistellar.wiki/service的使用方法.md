service通常定义在模块根目录的service.py中。

service用来编写复杂的业务逻辑，这一个service的完整例子
```python
import os
import asyncio
import zipfile
import markdown
import html2text

from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
from apistellar import FileResponse, Service, inject, SettingsMixin

from .article import Article
from ..lib.html_cut import Cuter
from .article_exporter import ArticleExporter
from ..utils import get_cut_file_name, project_path, \
    get_id, format_articles, get_image


class ArticleService(Service, SettingsMixin):
    def __init__(self):
        # 之前cutter使用注入的方式实现，感觉被过度设计了
        self.cuter = Cuter(
            self.settings.get("PHANTOMJS_PATH"),
            os.path.join(project_path, "cut_html.js"))
        self.executor = ThreadPoolExecutor()

    async def get(self, id):
        """
        获取文章对象，并渲染文章正文
        :param id:
        :return:
        """
        article = Article(id=id)
        await article.load()
        format_article_body = markdown.markdown(
            article.article,
            extensions=['markdown.extensions.extra'])
        _, articles = format_articles([article.to_dict()])
        article = articles.pop()
        article["article"] = format_article_body
        return article

    async def export(self, article_list, code, url):
        """
        导出文章或文章列表，生成压缩包
        :param article_list:
        :param code:
        :param url:
        :return:
        """
        zip_file = BytesIO()
        zf = zipfile.ZipFile(zip_file, "w")
        for article in article_list:
            zf.writestr(*await ArticleExporter(article, code, url).export())

        zf.close()
        zip_file.seek(0)
        body = zip_file.read()
        zip_file.close()
        return FileResponse(body, filename=f"{get_id()}.zip")

    async def modify(self, article, img_url):
        """
        修改文章
        :param article:
        :param img_url:
        :return:
        """
        h2t = html2text.HTML2Text()
        h2t.ignore_links = False
        h2t.ignore_images = False
        article.article = "[comment]: <image> (![](%s))\n%s" % (
            img_url, h2t.handle(article.article)
        )
        await article.update()

    async def update(self, article):
        """
        更新文章
        :param article:
        :return:
        """
        await article.update()

    async def delete(self, article):
        """
        删除文章
        :param article:
        :return:
        """
        await article.remove()

    async def about(self, id):
        """
        返回或者生成关于我和我的联系方式文章模板
        :param id:
        :return:
        """
        article = Article()
        await article.load(id=id)
        if not article:
            article.id = id
            article.author = self.settings.get("AUTHOR")
            article.tags = [id]
            article.description = id
            article.feature = False
            article.article = id
            article.title = id
            article.show = False
            article.format()
            await article.save()

        article = article.to_dict()
        article["first_img"] = get_image(article["article"])
        article["article"] = markdown.markdown(
            article["article"], extensions=['markdown.extensions.extra'])
        return article

    async def show(self, searchField, _from, size, fulltext):
        """
        首页展示
        :param searchField:
        :param _from:
        :param size:
        :param fulltext:
        :return:
        """
        articles = await Article.search(
            searchField, _from=_from, size=size, fulltext=fulltext, show=True)
        feature_articles = await Article.search(
            searchField, _from=_from, size=size,
            fulltext=fulltext, feature=True, show=True)

        tags = [article.tags for article in
                await Article.load_list(None, projection=["tags"], show=True)]
        count = len(tags)
        tags, articles = format_articles(
            [article.to_dict() for article in articles], tags=tags)
        _, feature_articles = format_articles(
            [article.to_dict() for article in feature_articles])
        return {
            "count": count,
            "articles": articles,
            "feature_articles": feature_articles,
            "tags": [i for i in
                     sorted(tags.items(), key=lambda x: x[1], reverse=True)]}

    async def cut(self, url, top, left, width, height):
        """
        按指定位置尺寸切网页
        :param url:
        :param top:
        :param left:
        :param width:
        :param height:
        :return:
        """
        save_name = get_cut_file_name(
            project_path, url, top, left, width, height)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self.executor,
            self.cuter.cut,
            url, save_name, top, left, width, height)
        return save_name

```
Service是一个component，我们可以通过这种语法来动态注入一些属性。
可以重写service的__init__方法，并在初始化对象时，加入一些有用参数。service创建对象是隐式完成的，我们使用时直接注入就可以。
