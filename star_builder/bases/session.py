import typing
from flask.sessions import SecureCookieSession


Session = typing.NewType("Session", SecureCookieSession)
