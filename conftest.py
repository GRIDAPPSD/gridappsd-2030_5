import os
import shutil
import sys
import time
from threading import Thread
import tempfile
from pathlib import Path

import pytest
import yaml

from IEEE2030_5 import TLSRepository, ConfigObj
from IEEE2030_5.flask_server import run_server

class TestClient:
    pass

class TestServer:
    pass


@pytest.fixture
def base_config():
    pth = Path(__file__).parent.joinpath("tests/fixtures/base_config.yml")
    if not pth.exists():
        raise ValueError(f"Can't find path {pth}")

    conf = yaml.safe_load(pth.read_text())
    conf["openssl_cnf"] = str(Path(__file__).parent.joinpath("openssl.cnf").resolve())

    yield conf

#
# @pytest.fixture
# def server(base_config):
#     tmp = tempfile.mkdtemp(prefix="/tmp/baseconf_")
#     base_config["tls_repository"] = tmp
#     base_config["openssl_cnf"] = Path(__file__).parent.joinpath("openssl.cnf").resolve()
#     config = ConfigObj(base_config)
#
#     tls_repo = TLSRepository(config.tls_repository, config.openssl_cnf, config.server)
#
#     for k in config.devices:
#         tls_repo.create_cert(k.hostname)
#
#     thread = Thread(target=run_server, args=(config, tls_repo))
#     try:
#         thread.daemon = True
#         thread.start()
#         assert thread.is_alive()
#         time.sleep(2)
#
#         yield config, tls_repo, thread
#
#     finally:
#         thread.join()
#

