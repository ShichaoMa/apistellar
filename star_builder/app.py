import logging

from apistar import ASyncApp, App

from .service import Service
from .components import ServiceComponent, SettingsComponent
from .helper import load_packages, routing, print_routing

__all__ = ["Application"]

logger = logging.getLogger("star_builder.app")


def application(template_dir=None,
                static_dir=None,
                packages=None,
                schema_url='/schema/',
                docs_url='/docs/',
                static_url='/static/',
                components=None,
                event_hooks=None,
                settings_path="settings",
                debug=True,
                async=True):
    """
       参数指定选择使用异步app还是同步app
       可以动态发现当前项目根目录下所有routes的service中的handler
    """
    load_packages(".")
    include = routing(Service, None)
    SettingsComponent.register_path(settings_path)
    components = [ServiceComponent(), SettingsComponent()] + (components or [])

    if include:
        routes = [include]
        print_routing(routes, callback=logger.debug)
    else:
        logger.info("Noting to route. ")
        routes = []

    app = (ASyncApp if async else App)(
        routes,
        template_dir=template_dir,
        static_dir=static_dir,
        packages=packages,
        schema_url=schema_url,
        docs_url=docs_url,
        static_url=static_url,
        components=components,
        event_hooks=event_hooks)

    app.debug = debug
    return app


Application = application
