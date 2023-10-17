import ieee_2030_5.hrefs as hrefs
from ieee_2030_5.client.client import IEEE2030_5_Client


def test_request_enddevice(first_client: IEEE2030_5_Client):
    ed = first_client.end_device()

    assert ed
    assert ed.DERListLink
    assert ed.RegistrationLink
    assert ed.changedTime
    # TODO Add the device category back into the end device.
    #assert ed.deviceCategory
    assert ed.DeviceInformationLink
    assert ed.DeviceStatusLink
    assert ed.href
    assert ed.FunctionSetAssignmentsListLink
    assert ed.lFDI
    assert ed.sFDI


def test_can_get_registration_link(first_client: IEEE2030_5_Client):
    ed = first_client.end_device()
    reg = first_client.registration(ed)

    assert reg
    assert reg.pIN == 111115
    assert reg.dateTimeRegistered


def test_can_get_fsa_link(first_client: IEEE2030_5_Client):

    fsa = first_client.function_set_assignment_list()

    assert fsa.FunctionSetAssignments
    assert 1 == fsa.results
    assert 1 == fsa.all


def test_can_get_der_link(first_client: IEEE2030_5_Client):

    der_list = first_client.der_list()

    assert 1 == der_list.all
    assert der_list.DER[0]
    assert 1 == der_list.results

    der = der_list.DER[0]
    assert der.DERAvailabilityLink
    assert der.DERCapabilityLink
    assert der.DERSettingsLink
    assert der.DERStatusLink
    assert der.href