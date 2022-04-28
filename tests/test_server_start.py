def test_starting_server_using_fixture(server_startup):
    tls_repo, end_devices = server_startup
    assert tls_repo
    assert end_devices
