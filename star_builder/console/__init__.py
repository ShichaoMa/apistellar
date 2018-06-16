import asyncio

from IPython import embed
from IPython.core import formatters
from toolkit import cache_property

from apistar import Route
from apistar.http import PathParams, Response
from apistar.server.injector import ASyncInjector
from apistar.server.validation import VALIDATION_COMPONENTS
from apistar.server.asgi import ASGI_COMPONENTS, ASGIReceive,\
    ASGIScope, ASGISend

from ..solo.manager import MySelf
from ..bases.components import SettingsComponent
from ..helper import find_children, load_packages, get_real_method

# bug fix
formatters.get_real_method = get_real_method


class ConsoleManager(object):

    def __init__(self):
        load_packages(".")
        SettingsComponent.register_path("settings")
        initial_components = {
            'scope': ASGIScope,
            'receive': ASGIReceive,
            'send': ASGISend,
            'exc': Exception,
            'app': ConsoleManager,
            'path_params': PathParams,
            'route': Route,
            'response': Response,
        }
        self.state = {
            'scope': MySelf(),
            'receive': MySelf(),
            'send': MySelf(),
            'exc': None,
            'app': self,
            'path_params': MySelf(),
            'route': MySelf()
        }
        self.injector = ASyncInjector(
            list(ASGI_COMPONENTS + VALIDATION_COMPONENTS) + find_children(),
            initial_components)

    async def resolve(self, type):
        def wrapper(arg: type):
            return arg

        return await self.injector.run_async([wrapper], dict(self.state))

    def __getattr__(self, item):
        assert item in self.beans, f"{item} cannot inject!"
        return self.await(self.resolve(self.beans[item]))

    def __getitem__(self, item):
        assert item in self.beans, f"{item} cannot inject!"
        return self.await(self.resolve(self.beans[item]))

    @cache_property
    def beans(self):
        components = find_children(initialize=False)
        beans = dict()
        for component in components:
            type = component.resolve.__annotations__["return"]
            beans[type.__name__] = type
        return beans

    @staticmethod
    def await(awaitable):
        loop = asyncio.get_event_loop()
        task = loop.create_task(awaitable)
        loop.run_until_complete(task)
        return task.result()

    def start(self):
        await = self.await
        embed()


def main():
    ConsoleManager().start()
