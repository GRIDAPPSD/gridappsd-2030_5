import logging
from copy import deepcopy
from typing import Dict, List

from nicegui import ui

import ieee_2030_5.models as m

from ..pages import Pages, show_global_header
from ..session import get_fsa_list, get_program_list, send_fsa

_log = logging.getLogger(__name__)

page: Pages = Pages.FSA

fsa_list: m.FunctionSetAssignmentsList = m.FunctionSetAssignmentsList()

current_fsa: m.FunctionSetAssignments = m.FunctionSetAssignments()

program_list: m.DERProgramList() = get_program_list()


ui.refreshable
def render_select():
    
    fsa_selection = [p.description for p in fsa_list.FunctionSetAssignments]
    fsa_selection.insert(0, "NEW")
    
    with ui.row():
        with ui.column():
            if not current_fsa.description:
                ui.select(fsa_selection, label="Function Set Assignments", value=fsa_selection[0]).classes("w-64")
            else:
                ui.select(fsa_selection, label="Function Set Assignments", value=current_fsa.description).classes("w-64")
                
            if current_fsa.href:
                ui.label(f"Href: {current_fsa.href}")



@ui.refreshable
def render_form():
    with ui.row():
        ui.input("description").classes("w-64") \
            .bind_value(current_fsa, "description")
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
    
    if append_new := current_fsa.href is None:
        ...
        
    fsa = send_fsa(current_fsa)
    
    assert isinstance(fsa, m.FunctionSetAssignments)
    
    if append_new:
        fsa_list.FunctionSetAssignments.append(fsa)
    
    render_select.refresh()
    
    ui.notify(f"{page.value.title} saved successfully")
    
        
@ui.page(page.value.uri)
def show_fsa():
    global fsa_list
    
    response = get_fsa_list()
    if response:
        fsa_list = response
        
        
    show_global_header(Pages.FSA)
    render_select()
    render_form()
    
    ui.separator()
    with ui.row():
        ui.button("Store", on_click=validate_and_submit)
        ui.button("Revert", on_click=revert_changes)