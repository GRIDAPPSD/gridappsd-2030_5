from __future__ import annotations

import ieee_2030_5.models as m
from ieee_2030_5.client.client import IEEE2030_5_Client


def test_control_event_create_activate_deactivate(first_client_data):
    assert first_client_data.dcap
    assert first_client_data.edev
    assert first_client_data.derlist
    assert first_client_data.client

    # First DER in the list
    der: m.DER = first_client_data.derlist.DER[0]
    assert isinstance(der, m.DER)

    client: IEEE2030_5_Client = first_client_data.client
    assert isinstance(client, IEEE2030_5_Client)

    program: m.DERProgram = client.get(der.CurrentDERProgramLink.href)
    assert isinstance(program, m.DERProgram)