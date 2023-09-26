import logging
from copy import deepcopy
from typing import Dict, List

from nicegui import ui

import ieee_2030_5.models as m

from ..pages import Pages, show_global_header
from ..session import get_der_list, send_der

_log = logging.getLogger(__name__)

page: Pages = Pages.DER

der_list: m.DERList = m.DERList()

current_der: m.DER = m.DER()

#program_list: m.DERProgramList() = get_program_list()


ui.refreshable
def render_select():
    
    der_selection = [p.description for p in der_list.DER]
    der_selection.insert(0, "NEW")
    
    with ui.row():
        with ui.column():
            if not current_der.description:
                ui.select(der_selection, label="DER", value=der_selection[0]).classes("w-64")
            else:
                ui.select(der_selection, label="DER", value=current_der.description).classes("w-64")
                
            if current_der.href:
                ui.label(f"Href: {current_der.href}")



@ui.refreshable
def render_form():
    with ui.row():
        ui.input("description").classes("w-64") \
            .bind_value(current_der, "description")
    ui.separator()
    
    with ui.row():
        with ui.column():
            pass
                
    with ui.row():
        with ui.column():
            pass

            
            
def revert_changes():
    pass

def validate_and_submit():
    """Validate the objects and submit them to the server.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    global der_base, der_default
    
    if append_new := current_der.href is None:
        ...
        
    der = send_der(current_der)
    
    assert isinstance(der, m.DER)
    
    if append_new:
        der_list.DER.append(der)
    
    render_select.refresh()
    
    ui.notify(f"{page.value.title} saved successfully")
    
        
@ui.page(page.value.uri)
def show_der():
    global der_list
    
    response = get_der_list()
    if response:
        der_list = response
        
        
    show_global_header(Pages.DER)
    render_select()
    render_form()
    
    ui.separator()
    with ui.row():
        ui.button("Store", on_click=validate_and_submit)
        ui.button("Revert", on_click=revert_changes)