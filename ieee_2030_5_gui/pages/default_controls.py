import logging
from copy import deepcopy
from typing import Dict, List

from nicegui import ui

import ieee_2030_5.models as m

from ..pages import Pages, show_global_header
from ..session import get_control_list, get_curve_list, send_control

_log = logging.getLogger(__name__)

# Curves and Curve Type are here only for read only purposes.
curve_list: m.DERCurveList = m.DERCurveList()
curve_type_filtered: Dict[m.CurveType, List[m.DERCurve]] = {} 

# This is the list of controls that are available.
controls = m.DERControlList()

# The currrent control binding for this form.
current_control = m.DERControl()
current_control.opModConnect = False
current_control.opModEnergize = False

# The current dercontrol and dercontrolbase are here for read/write purposes.
der_base = m.DERControlBase()
der_default = m.DefaultDERControl()

der_base.DERControlBase = der_default
current_control.DERControlBase = der_base

@ui.refreshable
def render_select():
    der_controls = [c.description for c in controls.DERControl]
    der_controls.insert(0, "NEW")
    with ui.row():
        with ui.column():
            if not current_control.description:
                ui.select(der_controls, label="Controls", value=der_controls[0]).classes("w-64")
            else:
                ui.select(der_controls, label="Controls", value=current_control.description).classes("w-64")
                
            if current_control.href:
                ui.label(f"Href: {current_control.href}")

        
def change_control(new_control: str):
    pass    

@ui.refreshable
def render_der_control_form():
    with ui.row():
        ui.input("description").classes("w-64") \
            .bind_value(current_control, "description")
    ui.separator()
    
    with ui.row():
        with ui.column().classes("pr-20"):
            ui.label("DERDefaultControl")
            
            esdelay_input = ui.input("setESDelay (hundredth of a second)") \
                .bind_value(der_default, "setESDelay")
            setESHighFreq = ui.input("setESHighFreq (hundredth of a hertz)") \
                .bind_value(der_default, "setESHighFreq")
            setESHighVolt = ui.input("setESHighVolt (hundredth of a volt)") \
                .bind_value(der_default, "setESHighVolt")
            setESLowFreq = ui.input("setESLowFreq (hundredth of a hertz)") \
                .bind_value(der_default, "setESLowFreq")
            setESLowVolt = ui.input("setESLowVolt (hundredth of a volt)") \
                .bind_value(der_default, "setESLowVolt")
            setESRampTms = ui.input("setESRampTms (hundredth of a second)") \
                .bind_value(der_default, "setESRampTms")
            setESRandomDelay = ui.input("setESRandomDelay (hundredth of a second)") \
                .bind_value(der_default, "setESRandomDelay")
            setGradW = ui.input("setGradW (hundredth of a watt)") \
                .bind_value(der_default, "setGradW")
            setSoftGradW = ui.input("setSoftGradW (hundredth of a watt)") \
                .bind_value(der_default, "setSoftGradW")
            
        with ui.column().classes("pr-20"):
            ui.label("DERControlBase")
            
            opModConnect = ui.checkbox("opModConnect") \
                .bind_value(der_base, "opModConnect")
            opModEnergize = ui.checkbox("opModEnergize") \
                .bind_value(der_base, "opModEnergize")
            opModFixedPFAbsorbW = ui.input("opModFixedPFAbsorbW") \
                .bind_value(der_base, "opModFixedPFAbsorbW")
            opModFixedPFAbsorbW = ui.input("opModFixedPFAbsorbW") \
                .bind_value(der_base, "opModFixedPFAbsorbW")
        
            opModFixedPFInjectW = ui.input("opModFixedPFInjectW") \
                .bind_value(der_base, "opModFixedPFInjectW")
                
            opModFixedVar = ui.input("opModFixedVar") \
                .bind_value(der_base, "opModFixedVar")
            opModFixedW = ui.input("opModFixedW") \
                .bind_value(der_base, "opModFixedW")
            opModFreqDroop = ui.input("opModFreqDroop") \
                .bind_value(der_base, "opModFreqDroop")
            
                        
            opModMaxLimW = ui.input("opModMaxLimW") \
                .bind_value(der_base, "opModMaxLimW")
            opModTargetVar = ui.input("opModTargetVar") \
                .bind_value(der_base, "opModTargetVar")
            opModTargetW = ui.input("opModTargetW") \
                .bind_value(der_base, "opModTargetW")
            opModVoltVar = ui.input("opModVoltVar") \
                .bind_value(der_base, "opModVoltVar")
            opModWattPF = ui.input("opModWattPF") \
                .bind_value(der_base, "opModWattPF")
                
            rampTms: ui.input("rampTms") \
                .bind_value(der_base, "rampTms")
            
        with ui.column().classes("pr-20"):
            ui.label("Curve Selection")
            
            pModFreqWatt = ui.select({v.href: v.description for v in curve_type_filtered[m.CurveType.opModFreqWatt]}, label="pModFreqWatt").classes("w-64") \
                .bind_value_from(der_base, "pModFreqWatt")
            pModFreqWatt.enabled = len(curve_type_filtered[m.CurveType.opModFreqWatt]) > 0
    
            
            opModHFRTMayTrip = ui.select({v.href: v.description for v in curve_type_filtered[m.CurveType.opModHFRTMayTrip]}, label="opModHFRTMayTrip").classes("w-64")\
                .bind_value_from(der_base, "opModHFRTMayTrip")
            opModHFRTMayTrip.enabled = len(curve_type_filtered[m.CurveType.opModHFRTMayTrip]) > 0
    
                
            opModHFRTMustTrip = ui.select({v.href: v.description for v in curve_type_filtered[m.CurveType.opModHFRTMustTrip]}, label="opModHFRTMustTrip").classes("w-64")\
                .bind_value_from(der_base, "opModHFRTMustTrip")
            opModHFRTMustTrip.enabled = len(curve_type_filtered[m.CurveType.opModHFRTMustTrip]) > 0
    
            opModHVRTMayTrip = ui.select({v.href: v.description for v in curve_type_filtered[m.CurveType.opModHVRTMayTrip]}, label="opModHVRTMayTrip").classes("w-64") \
                .bind_value_from(der_base, "opModHVRTMayTrip")
            opModHVRTMayTrip.enabled = len(curve_type_filtered[m.CurveType.opModHVRTMayTrip]) > 0
            
            opModHVRTMustTrip = ui.select({v.href: v.description for v in curve_type_filtered[m.CurveType.opModHVRTMustTrip]}, label="opModHVRTMustTrip").classes("w-64") \
                .bind_value_from(der_base, "opModHVRTMustTrip")
            opModHVRTMustTrip.enabled = len(curve_type_filtered[m.CurveType.opModHFRTMustTrip]) > 0
            
            opModHVRTMomentaryCessation = ui.select({v.href: v.description for v in curve_type_filtered[m.CurveType.opModHVRTMomentaryCessation]}, label="opModHVRTMomentaryCessation").classes("w-64") \
                .bind_value_from(der_base, "opModHVRTMomentaryCessation")
            opModHVRTMomentaryCessation.enabled = len(curve_type_filtered[m.CurveType.opModHVRTMomentaryCessation]) > 0
            
            opModLFRTMayTrip = ui.select({v.href: v.description for v in curve_type_filtered[m.CurveType.opModLFRTMayTrip]}, label="opModLFRTMayTrip").classes("w-64") \
                .bind_value_from(der_base, "opModLFRTMayTrip")
            opModLFRTMayTrip.enabled = len(curve_type_filtered[m.CurveType.opModLFRTMayTrip]) > 0
            
            opModLVRTMayTrip = ui.select({v.href: v.description for v in curve_type_filtered[m.CurveType.opModLVRTMayTrip]}, label="opModLVRTMayTrip").classes("w-64") \
                .bind_value_from(der_base, "opModLVRTMayTrip")
            opModLVRTMayTrip.enabled = len(curve_type_filtered[m.CurveType.opModLVRTMayTrip]) > 0
            
            opModLVRTMustTrip = ui.select({v.href: v.description for v in curve_type_filtered[m.CurveType.opModLVRTMustTrip]}, label="opModLVRTMustTrip").classes("w-64") \
                .bind_value_from(der_base, "opModLVRTMustTrip")
            opModLVRTMustTrip.enabled = len(curve_type_filtered[m.CurveType.opModLVRTMustTrip]) > 0
            
            opModLVRTMomentaryCessation = ui.select({v.href: v.description for v in curve_type_filtered[m.CurveType.opModLVRTMomentaryCessation]}, label="opModLVRTMomentaryCessation").classes("w-64") \
                .bind_value_from(der_base, "opModLVRTMomentaryCessation")
            opModLVRTMomentaryCessation.enabled = len(curve_type_filtered[m.CurveType.opModLVRTMomentaryCessation]) > 0
            
            
def revert_changes():
    pass

def validate_and_submit():
    """Validate the objects and submit them to the server.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    global der_base, der_default, current_control
    
    if append_new_control := current_control.href is None:
        ...
    
    
    current_control.DERControlBase = der_base
    control = send_control(current_control)
    
    assert isinstance(control, m.DERControl)
    
    if append_new_control:
        controls.DERControl.append(control)
    
    current_control = control
    render_select.refresh()
    #render_select.refresh()
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
    
    ui.notify("Control saved successfully")
    
        
@ui.page("/controls")
def show_controls():
    global curve_list, curve_type_filtered
    
    curve_response = get_curve_list()
    if curve_response:
        curve_list = curve_response
        curve_type_filtered.clear()
        for curve_type in m.CurveType:
            curve_type_filtered[curve_type] = [curve for curve in curve_list.DERCurve if curve.curveType == curve_type.name or curve.curveType == curve_type.value]
        
        
    show_global_header(Pages.CONTROLS)
    render_select()
    render_der_control_form()
    
    ui.separator()
    with ui.row():
        ui.button("Store", on_click=validate_and_submit)
        ui.button("Revert", on_click=revert_changes)