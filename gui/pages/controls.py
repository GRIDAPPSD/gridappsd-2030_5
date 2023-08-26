import logging

from nicegui import ui
from pages import Pages, show_global_header
from session import get_default_controls

import ieee_2030_5.models as m

_log = logging.getLogger(__name__)



der_base = m.DERControlBase()
der_default = m.DefaultDERControl()

def render_default_der_control():
    with ui.column():
        with ui.card():
            with ui.column():
                ui.label("DERDefaultControl")
                with ui.row():
                    esdelay_input = ui.input("setESDelay (hundredth of a second)")
                with ui.row():
                    setESHighFreq = ui.input("setESHighFreq (hundredth of a hertz)")
                with ui.row():
                    setESHighVolt = ui.input("setESHighVolt (hundredth of a volt)")
                with ui.row():
                    setESLowFreq = ui.input("setESLowFreq (hundredth of a hertz)")
                with ui.row():
                    setESLowVolt = ui.input("setESLowVolt (hundredth of a volt)")
                with ui.row():
                    setESRampTms = ui.input("setESRampTms (hundredth of a second)")
                with ui.row():
                    setESRandomDelay = ui.input("setESRandomDelay (hundredth of a second)")
                with ui.row():
                    setGradW = ui.input("setGradW (hundredth of a watt)")
                with ui.row():
                    setSoftGradW = ui.input("setSoftGradW (hundredth of a watt)")
    with ui.column().classes("clear float"):
        with ui.card():
            with ui.column():
                ui.label("DERControlBase")
                
                with ui.row():
                    opModConnect = ui.checkbox("opModConnect")
                with ui.row():
                    opModEnergize = ui.checkbox("opModEnergize")
                with ui.row():
                    opModFixedPFAbsorbW = ui.input("opModFixedPFAbsorbW")
                with ui.row():
                    opModFixedPFAbsorbW = ui.input("opModFixedPFAbsorbW")
                
                with ui.row():
                    opModFixedPFInjectW = ui.input("opModFixedPFInjectW")
                with ui.row():
                    opModFixedVar = ui.input("opModFixedVar")
                with ui.row():
                    opModFixedW = ui.input("opModFixedW")
                with ui.row():
                    opModFreqDroop = ui.input("opModFreqDroop")
                # with ui.row():
                #     pModFreqWatt = ui.select("pModFreqWatt")
                # with ui.row():
                #     opModHFRTMayTrip = ui.select("opModHFRTMayTrip")
                # with ui.row():
                #     opModHFRTMustTrip = ui.select("opModHFRTMustTrip")
                
                # with ui.row():
                #     opModHVRTMayTrip = ui.select("opModHVRTMayTrip")
                # with ui.row():
                #     opModHVRTMomentaryCessation = ui.select("opModHVRTMomentaryCessation")
                # with ui.row():
                #     opModHVRTMustTrip = ui.select("opModHVRTMustTrip")
                # with ui.row():
                #     opModLFRTMayTrip = ui.select("opModLFRTMayTrip")
                # with ui.row():
                #     opModLVRTMayTrip = ui.select("opModLVRTMayTrip")
                # with ui.row():
                #     opModLVRTMayTrip = ui.select("opModLVRTMayTrip")
                # with ui.row():
                #     opModLVRTMomentaryCessation = ui.select("opModLVRTMomentaryCessation")
                # with ui.row():
                #     opModLVRTMustTrip = ui.select("opModLVRTMustTrip")                                                                      
                with ui.row():
                    opModMaxLimW = ui.input("opModMaxLimW")
                # with ui.row():
                #     opModTargetVar = ui.select("opModTargetVar")
                # with ui.row():
                #     opModTargetW = ui.select("opModTargetW")
                # with ui.row():
                #     opModVoltVar = ui.select("opModVoltVar")
                # with ui.row():
                #     opModWattPF = ui.select("opModWattPF")
                    
                with ui.row():
                    rampTms: ui.input("rampTms")
        
@ui.page("/controls")
def show_controls():
    show_global_header(Pages.CONTROLS)
    render_default_der_control()