import logging
from copy import deepcopy
from typing import Dict, List

from nicegui import ui

import ieee_2030_5.models as m

from ..pages import Pages, show_global_header
from ..session import get_control_list, get_program_list, send_program

_log = logging.getLogger(__name__)

page: Pages = Pages.PROGRAMS

programs: m.DERProgramList = m.DERProgramList()


current_primacy_type: m.PrimacyType = m.PrimacyType.InHomeManagementSystem
current_program: m.DERProgram = m.DERProgram(primacy=current_primacy_type.value,
                                             DefaultDERControlLink=m.DefaultDERControlLink(),
                                             ActiveDERControlListLink=m.ActiveDERControlListLink(),
                                             DERControlListLink=m.DERControlListLink())

# Readonly list of controls for the program.
control_list: m.DERControlList = get_control_list()

ui.refreshable
def render_select():
    
    der_programs = [p.description for p in programs.DERProgram]
    der_programs.insert(0, "NEW")
    
    with ui.row():
        with ui.column():
            if not current_program.description:
                ui.select(der_programs, label="Programs", value=der_programs[0]).classes("w-64")
            else:
                ui.select(der_programs, label="Programs", value=current_program.description).classes("w-64")
                
            if current_program.href:
                ui.label(f"Href: {current_program.href}")

def render_primacy_select():
    global current_primacy_type
    
    with ui.row():
        with ui.column():
            current_primacy_type = ui.select({v.value: v.name for i, v in enumerate(m.PrimacyType)}, label="Primacy").classes("w-96") \
                .bind_value(current_program, "primacy")
                
def render_default_control_select():
    der_controls = { p.href: p.description for p in control_list.DERControl}
    
    with ui.row():
        with ui.column():
            ui.select(der_controls, label="Default Control", value=current_program.DefaultDERControlLink.href).classes("w-64")
    
def change_control(new_control: str):
    pass    

@ui.refreshable
def render_form():
    if current_program.href:
        with ui.row():
            with ui.column():
                ui.label(f"Href: {current_program.href}")
                ui.label(f"MRID: {current_program.mRID}")
                ui.label(f"version: {current_program.version}")
    
    with ui.row():
        ui.input("description").classes("w-64") \
            .bind_value(current_program, "description")
    
    ui.separator()
    
    render_primacy_select()
    render_default_control_select()
                
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
    
    if append_new_program := current_program.href is None:
        ...
        
    program = send_program(current_program)
    
    assert isinstance(program, m.DERProgram)
    
    if append_new_program:
        program_list.DERProgram.append(program)
    
    render_select.refresh()
    
    ui.notify(f"{page.value.title} saved successfully")
    
        
@ui.page(page.value.uri)
def show_programs():
    global program_list
    
    program_response = get_program_list()
    if program_response:
        program_list = program_response

    show_global_header(Pages.CONTROLS)
    render_select()
    render_form()
    
    ui.separator()
    with ui.row():
        ui.button("Store", on_click=validate_and_submit)
        ui.button("Revert", on_click=revert_changes)