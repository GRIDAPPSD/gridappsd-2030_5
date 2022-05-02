from typing import Optional

import pytest

from ieee_2030_5 import ServerConfiguration
from ieee_2030_5.certs import TLSRepository
from ieee_2030_5.client import IEEE2030_5_Client


def get_2030_5_client(tls_repo: TLSRepository, server_config: ServerConfiguration, client_device: str) -> Optional[IEEE2030_5_Client]:
    h = None
    tries = 0
    while not h:
        try:
            h = IEEE2030_5_Client(cafile=tls_repo.ca_cert_file,
                                  server_hostname=server_config.server_hostname,
                                  # need to be better about hard coding the path
                                  ssl_port=8443,
                                  keyfile=tls_repo.__get_key_file__(client_device),
                                  certfile=tls_repo.__get_cert_file__(client_device))
        except ConnectionRefusedError:
            if tries < 10:
                print("Refused! sleeping 0.5")
            else:
                raise

    return h


def test_basic_001():
    pytest.skip("DNS lookup not supported!")


def test_basic_002(server_startup):
    tls_repo, end_devices, server_cfg = server_startup

    dev0_config = server_cfg.devices[0]
    client = get_2030_5_client(tls_repo, server_cfg, dev0_config.id)
    dcap = client.request_device_capability()
    print(dcap)


def test_basic_003():
    raise NotImplementedError()


def test_basic_004():
    raise NotImplementedError()


def test_basic_005():
    raise NotImplementedError()


def test_basic_006():
    raise NotImplementedError()


def test_basic_007():
    raise NotImplementedError()


def test_basic_008():
    raise NotImplementedError()


def test_basic_009():
    raise NotImplementedError()


def test_basic_010():
    raise NotImplementedError()


def test_basic_011():
    raise NotImplementedError()


def test_basic_012():
    raise NotImplementedError()


def test_basic_013():
    raise NotImplementedError()


def test_basic_014():
    raise NotImplementedError()


def test_basic_015():
    raise NotImplementedError()


def test_basic_016():
    raise NotImplementedError()


def test_basic_017():
    raise NotImplementedError()


def test_basic_018():
    raise NotImplementedError()


def test_basic_019():
    raise NotImplementedError()


def test_basic_020():
    raise NotImplementedError()


def test_basic_021():
    raise NotImplementedError()


def test_basic_022():
    raise NotImplementedError()


def test_basic_023():
    raise NotImplementedError()


def test_basic_024():
    raise NotImplementedError()


def test_basic_025():
    raise NotImplementedError()


def test_basic_026():
    raise NotImplementedError()


def test_basic_027():
    raise NotImplementedError()


def test_basic_028():
    raise NotImplementedError()


def test_basic_029():
    raise NotImplementedError()
