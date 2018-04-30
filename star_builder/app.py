import logging

from apistar import ASyncApp

from .helper import load_packages, routing
from .service import Service

__all__ = ["Application"]

logger = logging.getLogger("app")


class Application(ASyncApp):
    """
    可以动态发现当前项目根目录下所有routes的service中的handler
    """
    def __init__(self,
                 template_dir=None,
                 static_dir=None,
                 schema_url='/schema/',
                 static_url='/static/',
                 components=None,
                 event_hooks=None):
        load_packages(".")
        include = routing(Service, None)
        if include:
            routes = [include]
        else:
            logger.info("Noting to route. ")
            routes = []
        super(Application, self).__init__(
            routes,
            template_dir,
            static_dir,
            schema_url,
            static_url,
            components,
            event_hooks)
