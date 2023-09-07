#!/usr/bin/env python3


from der_programs import program_add, programs_list
from enddevices import add_end_device, show_end_device, show_list
from nicegui import ui
from router import global_router as router
from session import backend_session, endpoint

import ieee_2030_5.models as m
from ieee_2030_5.utils import xml_to_dataclass

resp = backend_session.get(endpoint("enddevices"))
enddevices: m.EndDeviceList = xml_to_dataclass(resp.text)

@router.add('/')
async def show_one():
    ui.label('Content One').classes('text-2xl')
    

    

@router.add('/end-devices')
async def show_end_devices(index: int = None):
    # resp = requests.get("https://127.0.0.1:7443/admin/enddevices", 
    #                     cert=('/home/os2004/tls/certs/admin.pem', '/home/os2004/tls/private/admin.pem'),
    #                     verify="/home/os2004/tls/certs/ca.pem")
    resp = backend_session.get(endpoint("enddevices"))
    enddevices = xml_to_dataclass(resp.text)
    if index is None:
        for index, ed in enumerate(enddevices.EndDevice):
            router.add_route(f'/end-devices/{index}', lambda : show_end_devices(index))

        show_list(enddevices)
    else:
        show_end_device(enddevices.EndDevice[index])
    
@router.add('/end-devices/add')
async def add_enddevice():
    # resp = requests.get("https://127.0.0.1:7443/admin/enddevices", 
    #                     cert=('/home/os2004/tls/certs/admin.pem', '/home/os2004/tls/private/admin.pem'),
    #                     verify="/home/os2004/tls/certs/ca.pem")
    #enddevices = xml_to_dataclass(resp.text)
    #show_list(enddevices)
    add_end_device()
    
    


@router.add('/two')
async def show_two():
    ui.label('Content Two').classes('text-2xl')


@router.add('/three')
async def show_three():
    ui.label('Content Three').classes('text-4x1')


@ui.page('/')  # normal index page (eg. the entry point of the app)
@ui.page('/{_:path}')  # all other pages will be handled by the router but must be registered to also show the SPA index page
async def main():
    
    ed_tree = []
    der_tree = []
    derp_tree = []
    
    for edev_index, ed in enumerate(enddevices.EndDevice):
        ed_tree.append({'id': ed.href, 'label': f'End Device {edev_index}' })
        if ed.DERListLink:
            resp = backend_session.get(endpoint(f"/ders/{edev_index}"))
            if resp.ok:
                derlist = xml_to_dataclass(resp.text)
                for der_index, der in enumerate(derlist.DER):
                    der_tree.append({'id': der.href, 'label': f"DER {der_index}"})
    
    resp = backend_session.get(endpoint(f"/derp"))
    if resp.ok:
        derplist: m.DERProgramList = xml_to_dataclass(resp.text)
        
        for derp_index, derp in enumerate(derplist.DERProgram):
            derp_children = []
            if derp.DefaultDERControlLink:
                resp = backend_session.get(endpoint(f"/derp/{derp_index}/dderc"))
                def_ctrl: m.DefaultDERControl = xml_to_dataclass(resp.text)
                derp_children.append(dict(id=def_ctrl.href, label="Default DER Control"))
            
            #if derp.ActiveDERControlListLink:
            if derp.DERControlListLink:
                resp = backend_session.get(endpoint(f"/derp/{derp_index}/derc"))
                derp_ctl_list: m.DERControlList = xml_to_dataclass(resp.text)
                der_ctl_children = []
                for der_ctl_index, der_ctl in enumerate(derp_ctl_list.DERControl):
                    der_ctl_children.append(id=der_ctl.href, label=f"DERControl {der_ctl_index}")
                derp_children.append(dict(id=derp_ctl_list, label="DER Controls", children=der_ctl_children))
                
            derp_tree.append(dict(id=derp.href, label=f"DERP {derp_index}", children=derp_children))

    
    with ui.header(elevated=True).style('background-color: #3874c8').classes('items-center justify-between'):
        ui.label('HEADER')

    with ui.left_drawer().style('background-color: #d7e3f4'):
        
        with ui.column():
            ui.tree([
                    {'id': 'end_devices', 'label': 'End Devices', 'children': ed_tree},
                    {'id': 'der_programs', 'label': 'DER Programs', 'children': derp_tree},
                    {'id': 'usage_points', 'label': 'Usage Points'},
                    {'id': 'ders', 'label': 'DERs', 'children': der_tree},
                    {'id': 'curves', 'label': 'Curves'}
                ], label_key="label", node_key='id', on_select=lambda e: ui.notify(e.value)).classes('text-lg')
            ui.button("DER Programs", on_click=lambda: router.open(programs_list)).classes('w-64')
            ui.button("End Devices", on_click=lambda: router.open(show_end_devices)).classes('w-64')
            ui.button("Add End Device", on_click=lambda: router.open(add_enddevice)).classes('w-64')
            ui.button('One', on_click=lambda: router.open(show_one)).classes('w-64')
            ui.button('Two', on_click=lambda: router.open(show_two)).classes('w-64')
            ui.button('Three', on_click=lambda: router.open(show_three)).classes('w-64')
    
    with ui.footer().style('background-color: #3874c8'):
        ui.label('FOOTER')
    
        

    
    # this places the content which should be displayed
    router.frame().classes('w-full p-4 bg-gray-100')

ui.run()