from pathlib import Path

import pytest

from IEEE2030_5.client import IEEE2030_5_Client

SERVER_CA_CERT = Path("~/tls/certs/ca.crt").expanduser().resolve()
CLIENT_KEYFILE = Path("~/tls/private/dev1.me.com.pem").expanduser().resolve()
CLIENT_CERTFILE = Path("~/tls/certs/dev1.me.com.crt").expanduser().resolve()


@pytest.fixture()
def client() -> IEEE2030_5_Client:
    yield IEEE2030_5_Client(server_hostname="me.com",
                            cafile=SERVER_CA_CERT,
                            ssl_port=8000,
                            keyfile=CLIENT_KEYFILE,
                            certfile=CLIENT_CERTFILE)


def test_comm_002(client):
    capability = client.request_device_capability()

    edev = client.request_edev_list()

    #time = client.request(capability.TimeLink.href)
    #assert time

    print(capability.EndDeviceListLink.href)


def test_comm_003(client):
    raise NotImplementedError()


def test_comm_004(client):
    raise NotImplementedError()
