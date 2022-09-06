from pathlib import Path


def test_starting_server_using_fixture(server_startup):
    tls_repo, end_devices, server_config = server_startup
    assert tls_repo
    assert end_devices
    assert server_config


    # assert server_config.server_hostname.strip() == Path("/etc/hostname").read_text().strip()
