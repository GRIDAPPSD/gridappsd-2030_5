#!/usr/bin/env python3

from enddevices import add_end_device, show_list
from nicegui import ui
from router import Router

from ieee_2030_5.utils import xml_to_dataclass

router = Router()

from session import backend_session, endpoint


@router.add('/')
async def show_one():
    ui.label('Content One').classes('text-2xl')

@router.add('/end-devices')
async def show_end_devices():
    # resp = requests.get("https://127.0.0.1:7443/admin/enddevices", 
    #                     cert=('/home/os2004/tls/certs/admin.pem', '/home/os2004/tls/private/admin.pem'),
    #                     verify="/home/os2004/tls/certs/ca.pem")
    resp = backend_session.get(endpoint("enddevices"))
    enddevices = xml_to_dataclass(resp.text)
    show_list(enddevices)
    
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
    ui.label('Content Three').classes('text-2xl')


@ui.page('/')  # normal index page (eg. the entry point of the app)
@ui.page('/{_:path}')  # all other pages will be handled by the router but must be registered to also show the SPA index page
async def main():
    
    with ui.header(elevated=True).style('background-color: #3874c8').classes('items-center justify-between'):
        ui.label('HEADER')

    with ui.left_drawer(top_corner=True, bottom_corner=True).style('background-color: #d7e3f4'):
        with ui.column():
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