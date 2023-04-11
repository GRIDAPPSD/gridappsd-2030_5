
from typing import List

import ieee_2030_5.models as m
from ieee_2030_5.client import IEEE2030_5_Client


def test_fsa_to_der_control(first_client: IEEE2030_5_Client):
    assert first_client is not None
    dcap: m.DeviceCapability = first_client.device_capability()
    assert dcap.EndDeviceListLink
    ed: m.EndDevice = first_client.end_device()
    assert ed
    assert ed.FunctionSetAssignmentsListLink
    assert ed.FunctionSetAssignmentsListLink.href
    fsa: m.FunctionSetAssignments = first_client.function_set_assignment()
    assert fsa
    assert fsa.DERProgramListLink
    assert fsa.DERProgramListLink.href
    derp = first_client.der_program()
    assert derp
    assert derp.DefaultDERControlLink
    assert derp.ActiveDERControlListLink
    assert derp.DERControlListLink
    assert derp.DERCurveListLink
    


    
