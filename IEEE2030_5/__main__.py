from argparse import ArgumentParser
import logging

from pathlib import Path

import yaml

logging.basicConfig(level=logging.DEBUG)

from IEEE2030_5 import ConfigObj, TLSRepository
from IEEE2030_5.server import run_server

_log = logging.getLogger(__name__)

if __name__ == '__main__':
    parser = ArgumentParser()

    parser.add_argument(dest="config", help="Configuration file for the server.")
    opts = parser.parse_args()

    with open(Path(opts.config).resolve()) as fp:
        config = ConfigObj(yaml.safe_load(fp.read()))

    assert config.tls_repository
    assert len(config.devices) > 0
    assert config.server
    _log.debug("Validating hostnames of devices")
    for i in range(len(config.devices)):
        assert config.devices[i].hostname

    tls_repo = TLSRepository(config.tls_repository, config.openssl_cnf, config.server, clear=True)
    for k in config.devices:
        tls_repo.create_cert(k.hostname)

    run_server(config, tls_repo)
