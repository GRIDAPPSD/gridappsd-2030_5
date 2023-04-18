import random
import uuid
from datetime import datetime, timedelta

from nicegui import app, ui
from router import global_router as router
from session import backend_session, endpoint

import ieee_2030_5.models as m
from ieee_2030_5.utils import dataclass_to_xml, uuid_2030_5, xml_to_dataclass


def datachange(data, prop, x):
    if hasattr(x, "value"):
        value = x.value
    else:
        value = x
    setattr(data, prop, value)
    return getattr(data, prop)

def add_control_event(program_index: int):
    der_control = m.DERControl()
    
    
    def post_der_control():
        resp = backend_session.post(endpoint(f'/derp/{program_index}/derc'), dataclass_to_xml(der_control))
        if resp.ok:
            ui.open("/derp")
        
        
        
    with ui.column():
        with ui.row():
            der_control.mRID = uuid_2030_5()
            ui.input('mRID', value=der_control.mRID, on_change=lambda e: datachange(der_control, "mRID", e))
        with ui.row():
            currentdate = datetime.utcnow()
            fmtstring = '%Y-%m-%d %H:%M:%S'
            ui.label(f"Current time UTC: {currentdate.strftime(fmtstring)}")
        with ui.row():
            ui.input("Event Start Date Time", value=f"{(datetime.utcnow() + timedelta(seconds=90)).strftime(fmtstring)}", on_change=lambda e: datachange(der_control, "interval.start", e))
        
        with ui.row():            
            duration = ui.input("duration", on_change=lambda e: datachange(der_control, "interval.duration", int(e.value)))
        ui.button("Save", on_click=lambda: post_der_control())

@router.add('/derp')
def programs_list():
    resp = backend_session.get(endpoint('/derp'))
    derps: m.DERProgramList = xml_to_dataclass(resp.text)
        
    for index, derp in enumerate(derps.DERProgram):
        router.add_route(f"/derp/{index}/derc/add", lambda: add_control_event(index))
        with ui.row():
            with ui.column():
                ui.label(f"Description: {derp.description}")
                ui.label(f"mRID: {derp.mRID}")                
                ui.label(f"primacy: {derp.primacy}")
                
                if derp.ActiveDERControlListLink:
                    ui.label(derp.ActiveDERControlListLink.href)
                if derp.DefaultDERControlLink:
                    ui.label(derp.DefaultDERControlLink.href)
                if derp.DERControlListLink:
                    ui.label(derp.DERControlListLink.href)
                
                ui.button('Control Event', on_click=lambda: router.open(f"/derp/{index}/derc/add"))

    ui.button('Create New Program', on_click=lambda: router.open(f'/derp/add'))
    
@app.get('/derp/{max}')
def generate_random_number(max: int):
    with ui.column():
        ui.label("foo")
    #return {'min': 0, 'max': max, 'value': random.randint(0, max)}
  

@router.add('/derp/add')
def program_add():
    data = m.DERProgram()
    
    
    def create_derp():
        resp = backend_session.post(endpoint("derp"), data=dataclass_to_xml(data))
        if resp.ok:
            ui.open("/derp")
        
    with ui.column():
        ui.input("mRID", on_change=lambda x: datachange(data, "mRID", x))
        ui.input("description", on_change=lambda x: datachange(data, "description", x))
        ui.input("primacy", on_change=lambda x: datachange(data, "primacy", x))
        ui.button("Save", on_click=lambda: create_derp())

#ui.run()

