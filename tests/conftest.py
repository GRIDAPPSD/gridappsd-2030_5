from multiprocessing import Process
from pathlib import Path
import sys
from typing import Tuple

import pytest

# should now be at root
import yaml

from ieee_2030_5 import ServerConfiguration
from ieee_2030_5.__main__ import get_end_devices, get_tls_repository
from ieee_2030_5.certs import TLSRepository
from ieee_2030_5.flask_server import run_server
from ieee_2030_5.models.end_devices import EndDevices

parent_path = Path(__file__).parent.parent

if str(parent_path) not in sys.path:
    sys.path.insert(0, str(parent_path))

SERVER_CONFIG_FILE = Path(__file__).parent.joinpath("fixtures/server-config.yml")


@pytest.fixture(scope="module")
def server_startup() -> Tuple[TLSRepository, EndDevices]:
    def start_server_internal(config_path: str):
        """
        This function will start the server without certificate creation.  It is
        assumed that the outer function will do that before calling this function
        via the multiprocess.Process call.
        """
        try:
            cfg = yaml.safe_load(SERVER_CONFIG_FILE.read_text())

            config = ServerConfiguration(**cfg)
            tls_repo = TLSRepository(config.tls_repository,
                                     config.openssl_cnf,
                                     config.server_hostname,
                                     clear=False)
            groups, end_devices = get_end_devices(config)
            run_server(config, tls_repo, enddevices=end_devices)
        except KeyboardInterrupt as ex:
            print("Shutting down server.")

    cfg_out = yaml.safe_load(SERVER_CONFIG_FILE.read_text())

    config_server = ServerConfiguration(**cfg_out)
    tls_repository = get_tls_repository(config_server)
    groups, end_devices = get_end_devices(config_server, tls_repository)

    proc = Process(target=start_server_internal, args=(SERVER_CONFIG_FILE,), daemon=True)
    proc.start()

    yield tls_repository, end_devices

    proc.terminate()
    proc.join(timeout=5)
