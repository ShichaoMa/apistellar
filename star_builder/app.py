from apistar import ASyncApp

from .helper import look_for_services, collect_route
from .service import Service

__all__ = ["Application"]


class Application(ASyncApp):
    """
    可以动态发现当前项目根目录下所有routes的asgi app
    """
    def __init__(self,
                 template_dir=None,
                 static_dir=None,
                 schema_url='/schema/',
                 static_url='/static/',
                 components=None,
                 event_hooks=None):
        look_for_services(".")
        routes = collect_route(Service)
        super(Application, self).__init__(routes,
                   template_dir,
                   static_dir,
                   schema_url,
                   static_url,
                   components,
                   event_hooks)
