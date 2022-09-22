import os
import shutil
import sys
from pathlib import Path
from tempfile import mkdtemp
from typing import Tuple

import pytest
# should now be at root
import yaml

from ieee_2030_5.__main__ import get_tls_repository, ServerThread
from ieee_2030_5.certs import TLSRepository
from ieee_2030_5.client import IEEE2030_5_Client
from ieee_2030_5.config import ServerConfiguration
from ieee_2030_5.flask_server import build_server
from ieee_2030_5.server.server_constructs import EndDevices, initialize_2030_5

parent_path = Path(__file__).parent.parent

if str(parent_path) not in sys.path:
    sys.path.insert(0, str(parent_path))

SERVER_CONFIG_FILE = Path(__file__).parent.joinpath("fixtures/server-config.yml")
assert SERVER_CONFIG_FILE.exists()

TLS_REPO: TLSRepository
SERVER_CFG: ServerConfiguration


@pytest.fixture(scope="module")
def server_startup() -> Tuple[TLSRepository, EndDevices, ServerConfiguration]:
    global TLS_REPO, SERVER_CFG

    cfg_out = yaml.safe_load(SERVER_CONFIG_FILE.read_text())

    cwd = os.getcwd()
    root = Path(__file__).parent.parent
    os.chdir(str(root))
    config_server = ServerConfiguration(**cfg_out)

    tls_repository = get_tls_repository(config_server)
    end_devices = initialize_2030_5(config_server, tls_repository)

    server = build_server(config=config_server,
                          tlsrepo=tls_repository,
                          enddevices=end_devices)

    TLS_REPO = tls_repository
    SERVER_CFG = config_server

    thread = ServerThread(server)
    thread.start()

    yield tls_repository, end_devices, config_server

    thread.shutdown()
    thread.join(timeout=5)
    thread = None
    os.chdir(cwd)
    shutil.rmtree(config_server.tls_repository, ignore_errors=True)


@pytest.fixture()
def tls_repository() -> TLSRepository:
    yield TLS_REPO


@pytest.fixture()
def server_config() -> ServerConfiguration:
    yield SERVER_CFG


@pytest.fixture()
def first_client(server_startup) -> IEEE2030_5_Client:
    repo, devices, servercfg = server_startup

    host, port = servercfg.server_hostname.split(":")
    dev = devices.get_end_device_data(0)
    certfile, keyfile = repo.get_file_pair(dev.mRID)
    client = IEEE2030_5_Client(server_hostname=host,
                               server_ssl_port=port,
                               cafile=repo.ca_cert_file,
                               keyfile=Path(keyfile),
                               certfile=Path(certfile))

    yield client

    client.disconnect()


@pytest.fixture
def new_tls_repository() -> TLSRepository:
    root = Path(__file__).parent
    tmp = mkdtemp(prefix="/tmp/tmpcerts")
    assert Path(tmp).exists()

    print(Path(__file__).parent.parent.joinpath("openssl.cnf"))

    try:
        tls = TLSRepository(
            repo_dir=tmp,
            # Default openssl.cnf is two directories up from this test.
            openssl_cnffile_template=Path(__file__).parent.parent.joinpath("openssl.cnf"),
            serverhost="serverhostname")

        yield tls

    finally:
        shutil.rmtree(tmp)
