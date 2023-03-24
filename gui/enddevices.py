from dataclasses import fields

from nicegui import ui

import ieee_2030_5.models as m

columns = [
    {'name': 'property', 'label': 'Property', 'field': 'property', 'required': False},
    {'value': 'value', 'label': 'Value', 'field': 'property', 'required': False},
]

def show_list(enddevices: m.EndDeviceList):
    if len(enddevices.EndDevice) == 0:
        ui.label(f"No EndDevice in list. all={enddevices.all}, results={enddevices.results}")
    else:
        
        for ed in enddevices.EndDevice:
            for fld in fields(ed):
                with ui.row():
                    value = getattr(ed, fld.name)
                    if value and fld.type in ('Optional[str]', 'str'):
                        if isinstance(value, str):
                            ui.label(f"{fld.name}, {value}, {fld.type}")    
                        else:
                            ui.label(f"{fld.name}, {value.decode('utf-8')}, {fld.type}")
                    # value = getattr(ed, fld.name)
                    # if value and value.decode('utf-8'):
                    #     ui.label(f"{fld.name} => {value.decode('utf-8')}")
       
def add_end_device():
    
    def submit_end_device(id, pin):
        ui.label(f"Posted {id} and {pin}")
    
    with ui.column():
        id = ui.input(label="Id")
        pin = ui.input(label="Pin")
        ui.button("Save", on_click=lambda a: submit_end_device(id.value, pin.value))