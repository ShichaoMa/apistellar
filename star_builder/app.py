import logging

from apistar import ASyncApp

from .helper import load_packages, routing, print_routing
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
                 packages=None,
                 schema_url='/schema/',
                 docs_url='/docs/',
                 static_url='/static/',
                 components=None,
                 event_hooks=None, debug=True):
        load_packages(".")
        include = routing(Service, None)

        if include:
            routes = [include]
            print_routing(routes, callback=logger.debug)
        else:
            logger.info("Noting to route. ")
            routes = []

        super(Application, self).__init__(
            routes,
            template_dir=template_dir,
            static_dir=static_dir,
            packages=packages,
            schema_url=schema_url,
            docs_url=docs_url,
            static_url=static_url,
            components=components,
            event_hooks=event_hooks)
        self.debug = debug
