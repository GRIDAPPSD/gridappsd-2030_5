from pathlib import Path


def test_tls_creates_ca_and_server_keys(new_tls_repository):
    assert Path(new_tls_repository.ca_cert_file).exists()
    assert Path(new_tls_repository.ca_key_file).exists()
    assert Path(new_tls_repository.server_key_file).exists()
    assert Path(new_tls_repository.server_cert_file).exists()


def test_tls_creates_client_cert_and_key(new_tls_repository):
    new_tls_repository.create_cert("foo")
    assert new_tls_repository.fingerprint("foo")

    # Note using internal api this may change!
    assert Path(new_tls_repository.__get_key_file__("foo")).exists()
    assert Path(new_tls_repository.__get_cert_file__("foo")).exists()
