from pathlib import Path

import pytest


def test_comm_002(first_client):
    capability = first_client.device_capability()

    edev = first_client.end_devices()
    assert edev

    #time = client.request(capability.TimeLink.href)
    #assert time

    print(capability.EndDeviceListLink.href)


def test_comm_003(client):
    raise NotImplementedError()


def test_comm_004(client):
    raise NotImplementedError()
