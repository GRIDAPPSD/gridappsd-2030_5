from dataclasses import dataclass
import os
import shutil
import sys
from pathlib import Path
from tempfile import mkdtemp
from typing import Tuple

import pytest
# should now be at root
import yaml

from ieee_2030_5.__main__ import ServerThread, get_tls_repository
import ieee_2030_5.models as m
import ieee_2030_5.adapters as adpt
from ieee_2030_5.certs import TLSRepository
from ieee_2030_5.client import IEEE2030_5_Client
from ieee_2030_5.config import ServerConfiguration
from ieee_2030_5.flask_server import build_server
from ieee_2030_5.server.server_constructs import initialize_2030_5
import os

parent_path = Path(__file__).parent.parent

if str(parent_path) not in sys.path:
    sys.path.insert(0, str(parent_path))

SERVER_CONFIG_FILE = Path(__file__).parent.joinpath("fixtures/server-config.yml")
assert SERVER_CONFIG_FILE.exists()
if Path("~/.ieee2030-5").expanduser().exists():
    shutil.rmtree(Path("$HOME/.ieee2030-5").expanduser())

TLS_REPO: TLSRepository
SERVER_CFG: ServerConfiguration


@dataclass
class ClientData:
    client: IEEE2030_5_Client
    dcap: m.DeviceCapability
    edev: m.EndDevice
    ders: m.DERList


@pytest.fixture
def ignore_adapter_load():
    os.environ['IEEE_ADAPTER_IGNORE_INITIAL_LOAD'] = '1'


@pytest.fixture(scope="function")
def create_project_dir() -> Path:
    """
    Create a temporary directory with a prefix of "/tmp/tmpproject" and yield the path to the directory.
    After the test that uses this fixture is done, the directory is deleted using `shutil.rmtree`.
    
    :return: Path to the temporary directory
    :rtype: Path
    """
    tmp = mkdtemp(prefix="/tmp/tmpproject")
    assert Path(tmp).exists()

    yield Path(tmp)

    shutil.rmtree(tmp)


@pytest.fixture(scope="function")
def server_startup(create_project_dir: Path) -> Tuple[TLSRepository, ServerConfiguration]:
    """
    Start up the server for testing. This fixture uses the `create_project_dir` fixture to create a temporary directory
    for the server to use. It then loads a YAML configuration file located at `fixtures/server-config.yml`, modifies it
    to use the temporary directory for TLS certificates and storage, and creates a `ServerConfiguration` object with the
    modified configuration. Finally, it returns a tuple containing a `TLSRepository` object and the `ServerConfiguration`
    object.
    
    :param create_project_dir: The `create_project_dir` fixture
    :type create_project_dir: fixture
    :return: A tuple containing a `TLSRepository` object and the `ServerConfiguration` object
    :rtype: Tuple[TLSRepository, ServerConfiguration]
    """
    global TLS_REPO, SERVER_CFG

    cfg_out = yaml.safe_load(SERVER_CONFIG_FILE.read_text())
    cfg_out["tls_repository"] = str(create_project_dir.joinpath("tls"))
    cfg_out["storage_path"] = str(create_project_dir.joinpath("storage"))

    cwd = os.getcwd()
    root = Path(__file__).parent.parent
    os.chdir(str(root))
    config_server = ServerConfiguration(**cfg_out)

    tls_repository = get_tls_repository(config_server)
    initialize_2030_5(config_server, tls_repository)

    server = build_server(config=config_server, tlsrepo=tls_repository)

    TLS_REPO = tls_repository
    SERVER_CFG = config_server

    thread = ServerThread(server)
    thread.start()

    yield tls_repository, config_server

    thread.shutdown()
    thread.join(timeout=5)
    thread = None
    os.chdir(cwd)
    shutil.rmtree(config_server.tls_repository, ignore_errors=True)


@pytest.fixture
def tls_repository() -> TLSRepository:
    yield TLS_REPO


@pytest.fixture
def server_config() -> ServerConfiguration:
    yield SERVER_CFG


@pytest.fixture
def first_client_data(first_client: IEEE2030_5_Client) -> ClientData:
    dcap: m.DeviceCapability = first_client.device_capability()
    edev: m.EndDevice = first_client.end_device()
    derlist: m.DERList = first_client.ders()

    yield ClientData(client=first_client, dcap=dcap, edev=edev, ders=derlist)


@pytest.fixture
def first_client(server_startup: Tuple[TLSRepository, ServerConfiguration]) -> IEEE2030_5_Client:
    """
    Fixture that creates an instance of `IEEE2030_5_Client` for the first device specified in the server configuration.
    The `server_startup` fixture is used to start up the server for testing, and the `TLSRepository` and
    `ServerConfiguration` objects are unpacked from the tuple that `server_startup` yields. The client is created with
    the hostname and SSL port of the server, the CA certificate file, and the key and certificate files for the first
    device specified in the server configuration. The client is yielded to the test function, and disconnected after
    the test function completes.
    
    :param server_startup: The `server_startup` fixture
    :type server_startup: fixture
    :return: An instance of `IEEE2030_5_Client` for the first device specified in the server configuration
    :rtype: IEEE2030_5_Client
    """
    repo, servercfg = server_startup

    host, port = servercfg.server_hostname.split(":")
    certfile, keyfile = repo.get_file_pair(servercfg.devices[0].id)
    client = IEEE2030_5_Client(server_hostname=host,
                               server_ssl_port=port,
                               cafile=repo.ca_cert_file,
                               keyfile=Path(keyfile),
                               certfile=Path(certfile))

    yield client

    client.disconnect()


@pytest.fixture
def admin_client(server_startup: Tuple[TLSRepository, ServerConfiguration]) -> IEEE2030_5_Client:
    """
    Fixture that creates an instance of `IEEE2030_5_Client` for the admin device. The `server_startup` fixture is used
    to start up the server for testing, and the `TLSRepository` and `ServerConfiguration` objects are unpacked from the
    tuple that `server_startup` yields. The client is created with the hostname and SSL port of the server, the CA
    certificate file, and the key and certificate files for the admin device. The client is yielded to the test
    function, and disconnected after the test function completes.
    
    :param server_startup: The `server_startup` fixture
    :type server_startup: fixture
    :return: An instance of `IEEE2030_5_Client` for the admin device
    :rtype: IEEE2030_5_Client
    """
    repo, servercfg = server_startup

    host, port = servercfg.server_hostname.split(":")
    certfile, keyfile = repo.get_file_pair("admin")
    client = IEEE2030_5_Client(server_hostname=host,
                               server_ssl_port=port,
                               cafile=repo.ca_cert_file,
                               keyfile=Path(keyfile),
                               certfile=Path(certfile))

    yield client

    client.disconnect()


@pytest.fixture
def new_tls_repository() -> TLSRepository:
    """
    Fixture that creates a new `TLSRepository` object with a temporary directory for storing TLS certificates. The
    `openssl.cnf` file located at the root of the project is used as a template for generating the certificate
    authority and device certificates. The `TLSRepository` object is yielded to the test function, and the temporary
    directory is deleted after the test function completes.
    
    :return: A new `TLSRepository` object
    :rtype: TLSRepository
    """
    root = Path(__file__).parent
    tmp = mkdtemp(prefix="/tmp/tmpcerts")
    assert Path(tmp).exists()

    print(Path(__file__).parent.parent.joinpath("openssl.cnf"))

    try:
        tls = TLSRepository(
            repo_dir=tmp,
            openssl_cnffile_template=Path(__file__).parent.parent.joinpath("openssl.cnf"),
            serverhost="serverhostname")

        yield tls
    except Exception as e:
        print(e)
        raise e

    finally:
        shutil.rmtree(tmp)
