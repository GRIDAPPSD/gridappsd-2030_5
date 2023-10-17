from __future__ import annotations


def test_control_event_create_activate_deactivate(first_client_data):
    assert first_client_data.dcap
    assert first_client_data.edev
    assert first_client_data.derlist