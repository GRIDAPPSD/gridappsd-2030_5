import os
from argparse import ArgumentParser
import logging
from pathlib import Path
import socket
import sys

import yaml
from icecream import ic

from ieee_2030_5.certs import TLSRepository
from ieee_2030_5.config import ServerConfiguration
from ieee_2030_5.flask_server import run_server
from ieee_2030_5.models.end_devices import EndDevices

logging.basicConfig(level=logging.DEBUG)

# from ieee_2030_5 import ConfigObj, TLSRepository
#from IEEE2030_5.server import run_server
# from ieee_2030_5.flask_server import run_server

_log = logging.getLogger(__name__)

if __name__ == '__main__':
    parser = ArgumentParser()

    parser.add_argument(dest="config", help="Configuration file for the server.")
    parser.add_argument("--no-validate", action="store_true",
                        help="Allows faster startup since the resolving of addresses is not done!")
    parser.add_argument("--no-create-certs", action="store_true",
                        help="If specified certificates for for client and server will not be created.")
    opts = parser.parse_args()

    os.environ["IEEE_2030_5_CONFIG_FILE"] = str(Path(opts.config).expanduser().resolve(strict=True))
    #
    cfg = yaml.safe_load(Path(opts.config).expanduser().resolve(strict=True).read_text())

    config = ServerConfiguration(**cfg)

    assert config.tls_repository
    assert len(config.devices) > 0
    assert config.server_hostname
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
    tls_repo = TLSRepository(config.tls_repository, config.openssl_cnf, config.server_hostname,
                             clear=create_certs)
    if create_certs:
        # registers the devices, but doesn't create the end devices here.
        for k in config.devices:
            tls_repo.create_cert(k.hostname)

    # Create the enddevice on the server on startup.
    #
    # The other option is enddevices_register_access_only which in effect
    # becomes a noop as the certificates should already be created for the system
    # or added through the web interface.
    if config.server_mode == "enddevices_create_on_start":
        # TODO Make the .yml file include a device type from the accepted list in DeviceCategoryType
        pass
        #for k in config.devices:



    try:
        run_server(config, tls_repo)
    except Exception as ex:
        print(ex)
