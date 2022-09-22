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


@pytest.fixture(scope="session", autouse=True)
def create_certs_for_clients():
    root = Path(__file__).parent.parent
    cfg = yaml.safe_load(Path(SERVER_CONFIG_FILE).read_text())
    cwd = os.getcwd()
    os.chdir(str(root))
    config = ServerConfiguration(**cfg)
    tls_repo = TLSRepository(config.tls_repository,
                             config.openssl_cnf,
                             config.server_hostname)
    pair = tls_repo.get_file_pair("dev1")
    assert Path(pair[0]).exists()
    assert Path(pair[1]).exists()

    yield
    os.chdir(cwd)
    shutil.rmtree(config.tls_repository, ignore_errors=True)


@pytest.fixture(scope="module")
def server_startup() -> Tuple[TLSRepository, EndDevices, ServerConfiguration]:
    global TLS_REPO, SERVER_CFG

    def start_server_internal(config_path: str):
        """
        This function will start the server without certificate creation.  It is
        assumed that the outer function will do that before calling this function
        via the multiprocess.Process call.
        """
        import logging
        logging.basicConfig(filename="servertest.log", level=logging.DEBUG)
        try:
            cfg = yaml.safe_load(Path(config_path).read_text())
            cwd = os.getcwd()
            os.chdir(str(SERVER_CONFIG_FILE.parent))
            config = ServerConfiguration(**cfg)
            os.chdir(cwd)
            tls_repo = TLSRepository(config.tls_repository,
                                     config.openssl_cnf,
                                     config.server_hostname,
                                     clear=False)
            ed = initialize_2030_5(config, tls_repo)

            build_server(config, tls_repo, enddevices=ed)
        except KeyboardInterrupt as ex:
            print("Shutting down server.")

    cfg_out = yaml.safe_load(SERVER_CONFIG_FILE.read_text())

    cwd = os.getcwd()
    os.chdir(str(SERVER_CONFIG_FILE.parent))
    config_server = ServerConfiguration(**cfg_out)
    os.chdir(cwd)
    tls_repository = get_tls_repository(config_server)
    end_devices = initialize_2030_5(config_server, tls_repository)

    server = build_server(config=config_server,
                          tlsrepo=tls_repository,
                          enddevices=end_devices)
    #
    # proc = Process(target=start_server_internal, args=(SERVER_CONFIG_FILE,), daemon=True)
    # proc.start()
    #
    # time.sleep(2)
    #
    TLS_REPO = tls_repository
    SERVER_CFG = config_server

    thread = ServerThread(server)
    thread.start()

    yield tls_repository, end_devices, config_server

    thread.shutdown()
    thread.join(timeout=5)
    thread = None
    print("After join")


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
def tls_repo() -> TLSRepository:
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
        pass  # shutil.rmtree(tmp, ignore_errors=True)
