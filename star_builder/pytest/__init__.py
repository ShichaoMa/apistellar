import pytest
import asyncio
import threading

from toolkit import free_port
from star_builder import Application
from uvicorn.main import Server, HttpToolsProtocol


def run_server(app, port=8080):
    """
    创建一个简单的server用来测试
    :param app:
    :param port:
    :return:
    """
    loop = asyncio.new_event_loop()
    protocol_class = HttpToolsProtocol

    server = Server(app, "127.0.0.1", port, loop, None, protocol_class)
    loop.run_until_complete(server.create_server())
    if server.server is not None:
        loop.create_task(server.tick())
        loop.run_forever()


@pytest.fixture(scope="module")
def create_server():
    def run(app):
        port = free_port()
        th = threading.Thread(target=run_server, args=(app, ), kwargs={"port": port})
        th.setDaemon(True)
        th.start()
        return port
    return run


@pytest.fixture(scope="module")
def normal_server_port(create_server):
    app = Application("test")
    return create_server(app)
