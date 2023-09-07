import dataclasses
import json
import logging
from typing import List

from nicegui import ui

import ieee_2030_5.models as m
from ieee_2030_5.models.enums import CurveType, DERUnitRefType

from ..pages import Pages, show_global_header
from ..session import get_curve_list, send_curve

_log = logging.getLogger(__name__)

curve_data_points: List[m.CurveData] = [m.CurveData() for x in range(10)]
curve_list: m.DERCurveList = m.DERCurveList()
current_curve: m.DERCurve = m.DERCurve()
der_ref_type: DERUnitRefType = DERUnitRefType.NA
updating_curve: bool = False

@ui.refreshable
def render_select():
    with ui.row():
        der_curves = [c.description for c in curve_list.DERCurve]
        der_curves.insert(0, "NEW")
        if not current_curve.description:
            ui.select(der_curves, label="Curves", value=der_curves[0],
                      on_change=lambda e: change_der_curve(e.value)).classes("w-64")
        else:
            ui.select(der_curves, label="Curves", value=current_curve.description,
                      on_change=lambda e: change_der_curve(e.value)).classes("w-64")
        if current_curve.href:
            ui.label(f"Href: {current_curve.href}")

def change_der_curve_type(new_curve_type: DERUnitRefType):
    pass

def change_der_curve(new_curve_description: str):
    global curve_data_points, current_curve, der_ref_type, updating_curve
    
    updating_curve = True
    # Create a new item.
    if new_curve_description is None or new_curve_description == "NEW":
        current_curve = m.DERCurve()
        curve_data_points = []
        der_ref_type = DERUnitRefType.NA
    else:
        for curve in curve_list.DERCurve:
            if curve.description == new_curve_description:
                current_curve = curve
                curve_data_points = curve.CurveData
                break
            
    # We know this is a brand new curve so we create the max number of curve points
    # allowed so the user can enter data.
    if len(current_curve.CurveData) == 0:
        curve_data_points = [m.CurveData() for x in range(10)]
    else:
        # We know there is some data already so we want to keep that and then
        # add the maximum number of items availalbe.
        curve_data_points = [dataclasses.replace(x) for x in current_curve.CurveData]
        while len(curve_data_points) < 10:
            curve_data_points.append(m.CurveData())
    
    assert len(curve_data_points) == 10    
    render_curve_form.refresh()
    render_curve_data.refresh()
    updating_curve = False
    # render_curve_form()    
    # render_curve_data()

@ui.refreshable  
def render_curve_data():
    with ui.row():
        for i in range(10):
            with ui.column():
                ui.checkbox(f"excitation-{i}").bind_value(curve_data_points[i], "excitation")
                ui.number(f"x-value-{i}").props("size=10").bind_value(curve_data_points[i], "xvalue")
                ui.number(f"y-value-{i}").props("size=10").bind_value(curve_data_points[i], "yvalue")
                
def curve_type_refresh(select: ui.select):
    _log.debug(f"select: {select.value}")
    if current_curve.curveType != select.value:
        current_curve.curveType = select.value
        render_curve_form.refresh()
        
@ui.refreshable
def render_curve_form():
    _log.debug("Rendering curve form")
    with ui.row():
        with ui.column():            
            curveType = ui.select({curve_type.value: curve_type.name for index, curve_type in enumerate(CurveType)},
                                  label="Curve Type").classes("w-64").bind_value_from(current_curve, "curveType")
            curveType.on_value_change = lambda e: curve_type_refresh(curveType)
    with ui.row():
        with ui.column():
            mRID = ui.input('mRID').bind_value(current_curve, "mRID")
        with ui.column():
            description = ui.input('description').bind_value(current_curve, 'description')
        with ui.column():
            version = ui.input('version').bind_value(current_curve, "version")
            
    if current_curve.curveType == CurveType.opModVoltVar:
        with ui.row():
            if current_curve.autonomousVRefEnable is None:
                current_curve.autonomousVRefEnable = False
                
            with ui.column():
                autonomousVRefEnable = ui.checkbox("Enable", value=False).bind_value(current_curve, "autonomousVRefEnable")       
            with ui.column():
                autonomousVRefTimeConstant = ui.number("autonomousVRefTimeConstant").bind_value(current_curve, "autonomousVRefTimeConstant").classes("w-64") \
                                                                                    .bind_enabled(autonomousVRefEnable, "value")
                
    with ui.row():
        with ui.column():
            openLoopTms = ui.number("openLoopTms").bind_value(current_curve, "openLoopTms")
        with ui.column():
            rampDecTms = ui.number("rampDecTms").bind_value(current_curve, "rampDecTms")
        with ui.column():
            rampIncTms = ui.number("rampIncTms").bind_value(current_curve, "rampIncTms")
        with ui.column():
            rampPT1Tms = ui.number("rampPT1Tms").bind_value(current_curve, "rampPT1Tms")
        with ui.column():
            vRef = ui.input("vRef").bind_value(current_curve, "vRef")
    with ui.row():
        with ui.column():
            yRefType = ui.select({ v.value: v.name for index, v in enumerate(DERUnitRefType)},
                                 label="DER Unit Ref Type").bind_value(current_curve, "yRefType").classes("w-64")
        with ui.column():
            xMultiplier = ui.number("xMultiplier").bind_value(current_curve, "xMultiplier").classes("w-24")
        with ui.column():
            yMultiplier = ui.number("yMultiplier").bind_value(current_curve, "yMultiplier").classes("w-24")
        

    
data_row = None  

def render_object_data():
    global data_row, curve_data_points
    if data_row is None:
        data_row = ui.row()
    else:
        data_row.clear()
    with data_row:
        with ui.column():
            ui.label("Curve Data")
            for curve_data in curve_data_points:
                ui.markdown(f"""{dataclasses.asdict(curve_data)}""")
        with ui.column():
            ui.label("DER Curve")
            ui.markdown(f"""
```json
{json.dumps(dataclasses.asdict(current_curve), indent=4)}
```
""")
                
def revert_changes():
    pass

def validate_and_submit():
    """Validate the objects and submit them to the server.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    global curve_data_points, current_curve
    current_curve.CurveData = curve_data_points
    
    if append_new_curve := current_curve.href is None:
        ...
    
    # POST or PUT the curve to the server     
    dc = send_curve(current_curve)
    
    assert isinstance(dc, m.DERCurve)
    
    # update the variables for state
    curve_data_points = dc.CurveData
    current_curve = dc
    
    # IF its post then we append to the curve list
    if append_new_curve:
        curve_list.DERCurve.append(dc)
    
    render_select.refresh()
    
    ui.notify("Curve saved successfully")
    
    

@ui.page("/curves")
def show_curves():
    global curve_list
    curve_response = get_curve_list()
    if curve_response:
        curve_list = curve_response
    
    show_global_header(Pages.CURVES)
    
    render_select()
    ui.separator()
    render_curve_form()
    ui.separator()
    render_curve_data()
    
    
    with ui.row():
        ui.button("Store", on_click=validate_and_submit)
        ui.button("Revert", on_click=revert_changes)
        # Create a "newline style" separator
        ui.separator().clear()
    

    
    
    # excitation: boolean [0..1]
    # xvalue: Int32
    # yvalue: Int32