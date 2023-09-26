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
    CONTROLS = PageContext('controls', 'DER Controls', '/controls')
    DEFAULT_CONTROLS = PageContext('default_controls', 'Default DER Controls', '/default_controls')
    ENDDEVICES = PageContext('enddevices', 'End Devices', '/enddevices')
    PROGRAMS = PageContext('programs', 'DER Programs', '/programs')
    FSA = PageContext('fsa', 'Function Set Assignments', '/fsa')
    DER = PageContext('der', 'DER', '/der')
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
from .der import show_der
from .enddevices import show_enddevices
from .fsa import show_fsa
from .programs import show_programs

Pages.CERTS.value.module = show_certs
Pages.CONTROLS.value.module = show_controls
Pages.CURVES.value.module = show_curves
Pages.ENDDEVICES.value.module = show_enddevices
Pages.PROGRAMS.value.module = show_programs
Pages.FSA.value.module = show_fsa
Pages.DER.value.module = show_der

# def load_pages():
#     import glob
#     from os.path import basename, dirname, isfile, join
#     modules = glob.glob(join(dirname(__file__), "*.py"))
#     __all__ = [ basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]
    