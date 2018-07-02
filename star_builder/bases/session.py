import typing

from collections import namedtuple
from flask.sessions import SecureCookieSession, \
    SecureCookieSessionInterface

from .components import Component, Cookie, DummyFlaskApp


Session = typing.NewType("Session", SecureCookieSession)


class SessionComponent(Component):

    def __init__(self):
        self.dummy_request = namedtuple("Request", "cookies")
        self.session_interface = SecureCookieSessionInterface()

    def resolve(self,
                app: DummyFlaskApp,
                cookies: typing.Dict[str, Cookie]) -> Session:
            request = self.dummy_request(cookies=cookies)
            return self.session_interface.open_session(app, request)