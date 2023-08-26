from dataclasses import dataclass
from enum import Enum
from typing import Callable

from nicegui import ui


@dataclass
class PageContext:
    name: str
    title: str
    uri: str
    module: Callable = None
    
    

class Pages(Enum):
    HOME = PageContext('home', 'Home', '/')
    CERTS = PageContext('certs', 'Certificates', '/certs')
    CURVES = PageContext('curves', 'Curves', '/curves')
    CONTROLS = PageContext('controls', 'Controls', '/controls')
    DEVICES = PageContext('devices', 'Devices', '/devices')
    PROGRAMS = PageContext('programs', 'Programs', '/programs')
    # LOGIN = 'login'
    # LOGOUT = 'logout'
    # SETTINGS = 'settings'
    # USERS = 'users'


def show_global_header(page: PageContext):
    
    with ui.header(elevated=True).style('background-color: #3874c8'): #.classes('justify-between'):
        for index, pg in enumerate(Pages):
            link = ui.link(pg.value.title, pg.value.uri).style('color: white')
            if pg.value == page:
                link.style('font-weight: bold')

from .certs import show_certs
from .controls import show_controls
from .curves import show_curves

Pages.CERTS.value.module = show_certs
Pages.CONTROLS.value.module = show_controls
Pages.CURVES.value.module = show_curves

# def load_pages():
#     import glob
#     from os.path import basename, dirname, isfile, join
#     modules = glob.glob(join(dirname(__file__), "*.py"))
#     __all__ = [ basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]
    