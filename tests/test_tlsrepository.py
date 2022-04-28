import shutil
from pathlib import Path
from tempfile import mkdtemp

import pytest

from IEEE2030_5.certs import TLSRepository


@pytest.fixture
def tls_repo() -> TLSRepository:
    tmp = mkdtemp(prefix="/tmp/tmpcerts")
    assert Path(tmp).exists()

    try:
        tls = TLSRepository(
            repo_dir=tmp,
        # Default openssl.cnf is two directories up from this test.
            openssl_cnffile=Path(__file__).parent.parent.joinpath("openssl.cnf"),
            serverhost="serverhostname")

        yield tls

    finally:
        pass    #shutil.rmtree(tmp, ignore_errors=True)


def test_tls_creates_ca_and_server_keys(tls_repo):
    assert Path(tls_repo.ca_cert_file).exists()
    assert Path(tls_repo.ca_key_file).exists()
    assert Path(tls_repo.server_key_file).exists()
    assert Path(tls_repo.server_cert_file).exists()


def test_tls_creates_client_cert_and_key(tls_repo):
    tls_repo.create_cert("foo")
    assert tls_repo.fingerprint("foo")

    # Note using internal api this may change!
    assert Path(tls_repo.__get_key_file__("foo")).exists()
    assert Path(tls_repo.__get_cert_file__("foo")).exists()
