from argparse import ArgumentParser
import logging
from pathlib import Path
import socket
import sys

import yaml

logging.basicConfig(level=logging.DEBUG)

from IEEE2030_5 import ConfigObj, TLSRepository
#from IEEE2030_5.server import run_server
from IEEE2030_5.flask_server import run_server

_log = logging.getLogger(__name__)

if __name__ == '__main__':
    parser = ArgumentParser()

    parser.add_argument(dest="config", help="Configuration file for the server.")
    parser.add_argument("--no-validate", action="store_true",
                        help="Allows faster startup since the resolving of addresses is not done!")
    parser.add_argument("--no-create-certs", action="store_true",
                        help="If specified certificates for for client and server will not be created.")
    opts = parser.parse_args()

    with open(Path(opts.config).resolve()) as fp:
        config = ConfigObj(yaml.safe_load(fp.read()))

    assert config.tls_repository
    assert len(config.devices) > 0
    assert config.server
    unknown = []
    # Only check for resolvability if not passed --no-validate
    if not opts.no_validate:
        _log.debug("Validating hostnames of devices are resolvable.")
        for i in range(len(config.devices)):
            assert config.devices[i].hostname

            try:
                socket.gethostbyname(config.devices[i].hostname)
            except socket.gaierror:
                if hasattr(config.devices[i], "ip"):
                    try:
                        socket.gethostbyname(config.devices[i].ip)
                    except socket.gaierror:
                        unknown.append(config.devices[i].hostname)
                else:
                    unknown.append(config.devices[i].hostname)

    if unknown:
        _log.error("Couldn't resolve the following hostnames.")
        for host in unknown:
            _log.error(host)
        sys.exit(1)

    create_certs = not opts.no_create_certs
    tls_repo = TLSRepository(config.tls_repository, config.openssl_cnf, config.server,
                             clear=create_certs)
    if create_certs:
        for k in config.devices:
            tls_repo.create_cert(k.hostname)

    try:
        run_server(config, tls_repo)
    except Exception as ex:
        print(ex)
