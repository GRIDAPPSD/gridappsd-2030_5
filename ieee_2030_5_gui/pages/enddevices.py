import logging
from copy import deepcopy
from pprint import pformat
from typing import Any, Dict, List

from nicegui import ui

import ieee_2030_5.models as m

from ..pages import Pages, show_global_header
from ..session import get_enddevice_list, send_enddevice

_log = logging.getLogger(__name__)



enddevice_list: m.EndDeviceList = m.EndDeviceList()

default_enddevice: m.EndDevice = m.EndDevice(enabled=True, postRate=900)
current_enddevice: m.EndDevice = m.EndDevice(enabled=True, postRate=900)

class CurrentValueDict(dict):
    def __setitem__(self, __key: Any, __value: Any) -> None:
        return super().__setitem__(__key, __value)
    
    def __getitem__(self, __key: Any) -> Any:
        return super().__getitem__(__key)

current_enddevice = CurrentValueDict(current_enddevice.__dict__)


# Readonly list of controls for the program.
control_list = m.DERControlList()


@ui.refreshable
def render_select():
    
    end_device_hrefs = [p.href for p in enddevice_list.EndDevice]
    end_device_hrefs.insert(0, "NEW")
    
    with ui.row():
        with ui.column():
            if not current_enddevice.href:
                ui.select(end_device_hrefs, label="Programs", value=end_device_hrefs[0],
                          on_change=lambda e: change_select(e.value)).classes("w-64")
            else:
                ui.select(end_device_hrefs, label="Programs", value=current_enddevice.href,
                          on_change=lambda e: change_select(e.value)).classes("w-64")

def change_select(selected_value: str):
    global current_enddevice
    
    if selected_value in (None, "NEW"):
        _log.info(selected_value)
        current_enddevice = deepcopy(default_enddevice)
    else:
        current_enddevice = next(filter(lambda x: x.href == selected_value, enddevice_list.EndDevice))
        _log.info(selected_value)
        
    _log.debug(pformat(current_enddevice.__dict__))
    render_enddevice_form.refresh()

@ui.refreshable
def render_enddevice_form():
    
    with ui.row():
        with ui.column().classes("pr-20"):
            deviceCategory = ui.select({v.value: v.name for i, v in enumerate(m.DeviceCategoryType)}, 
                                       label="Device Category").classes("w-96") \
                .bind_value(current_enddevice, "deviceCategory", 
                            #forward=lambda x: x,
                            backward=lambda x: m.DeviceCategoryType(current_enddevice.deviceCategory).value)
                #.bind_value(current_enddevice, "deviceCategory")
            enabled = ui.checkbox("Enabled").bind_value(current_enddevice, "enabled")
            postRate = ui.number("postRate").bind_value(current_enddevice, "postRate")
        
        with ui.column():
            lfdi = ui.label(f"lFDI: {current_enddevice.lFDI}").bind_visibility(current_enddevice, 
                                                                        forward=lambda x: current_enddevice.href is None,
                                                                        backward=lambda x: current_enddevice.href is not None)
            
            sfdi = ui.label(f"sFDI: {current_enddevice.sFDI}").bind_visibility(current_enddevice, 
                                                                        forward=lambda x: current_enddevice.href is None,
                                                                        backward=lambda x: current_enddevice.href is not None)
            
        # TODO deal with function set url here
        # ui.select(names, multiple=True, value=names[:2], label='with chips') \
        #   .classes('w-64').props('use-chips')
            
def revert_changes():
    pass

def validate_and_submit():
    """Validate the objects and submit them to the server.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    global enddevice_list
    
    if append_new := current_enddevice.href is None:
        ...
        
    enddevice = send_enddevice(current_enddevice)
    
    assert isinstance(enddevice, m.EndDevice)
    
    if append_new:
        enddevice_list.EndDevice.append(enddevice)
    
    render_select.refresh()
    # global curve_data_points, current_curve
    # current_curve.CurveData = curve_data_points
    
    # if append_new_curve := current_curve.href is None:
    #     ...
    
    # # POST or PUT the curve to the server     
    # dc = send_control(current_curve)
    
    # assert isinstance(dc, m.DERCurve)
    
    # # update the variables for state
    # curve_data_points = dc.CurveData
    # current_curve = dc
    
    # # IF its post then we append to the curve list
    # if append_new_curve:
    #     curve_list.DERCurve.append(dc)
    
    # render_select.refresh()
    
    ui.notify("End Device saved successfully")
    
        
@ui.page(Pages.ENDDEVICES.value.uri)
def show_enddevices():
    global enddevice_list
    
    response = get_enddevice_list()
    if response:
        enddevice_list = response
        
        
    show_global_header(Pages.CONTROLS)
    render_select()
    render_enddevice_form()
    
    ui.separator()
    with ui.row():
        ui.button("Store", on_click=validate_and_submit)
        ui.button("Revert", on_click=revert_changes)