from ieee_2030_5.client.client import IEEE2030_5_Client


def test_request_enddevice(first_client: IEEE2030_5_Client):
    ed = first_client.end_device()

    assert ed
    assert ed.DERListLink
    assert ed.RegistrationLink
    assert ed.changedTime
    # TODO Add the device category back into the end device.
    # assert ed.deviceCategory
    assert ed.DeviceInformationLink
    assert ed.DeviceStatusLink
    assert ed.href
    assert ed.FunctionSetAssignmentsListLink
    assert ed.lFDI
    assert ed.sFDI


def test_request_enddevice(first_client: IEEE2030_5_Client):
    ed = first_client.end_device()


def test_can_get_registration_link(first_client: IEEE2030_5_Client):
    ed = first_client.end_device()
    reg = first_client.registration(ed)

    assert reg
    assert reg.pIN == 111115
    assert reg.dateTimeRegistered


def test_can_get_fsa_link(first_client: IEEE2030_5_Client):
    fsa = first_client.function_set_assignment_list()

    assert fsa.FunctionSetAssignments
    assert fsa.results == 1
    assert fsa.all == 1


def test_can_get_der_link(first_client: IEEE2030_5_Client):
    der_list = first_client.der_list()

    assert der_list.all == 1
    assert der_list.DER[0]
    assert der_list.results == 1

    der = der_list.DER[0]
    assert der.DERAvailabilityLink
    assert der.DERCapabilityLink
    assert der.DERSettingsLink
    assert der.DERStatusLink
    assert der.href
