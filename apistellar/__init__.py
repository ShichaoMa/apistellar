"""
PYTEST_DONT_REWRITE
"""
from apistellar.app import Application, show_routes

from apistellar.build import main
from apistellar.build.tasks import Task

from apistellar.bases.service import Service
from apistellar.bases.hooks import Hook, Return
from apistellar.bases.components import Component
from apistellar.bases.controller import Controller
from apistellar.bases.response import FileResponse
from apistellar.bases.model_factory import ModelFactory
from apistellar.bases.entities import Session, Cookie, FormParam, \
    FileStream, inject, SettingsMixin, UrlEncodeForm, MultiPartForm, \
    settings, init_settings

from apistellar.console import main as console

from apistellar.solo import Solo
from apistellar.solo.manager import SoloManager

from apistellar.persistence import DriverMixin, conn_manager, \
    conn_ignore, proxy, contextmanager

from apistellar.types import Type, AsyncType, PersistentType, \
    TypeEncoder, validators

from apistellar.route import route, get, post, delete, put, options, websocket

from apistellar.helper import redirect, require, return_wrapped

__version__ = "1.2.0"          
