import os

from argparse import ArgumentParser
import logging
from pathlib import Path
import socket
import sys
from typing import Dict, Tuple
from urllib.parse import urlparse

import yaml

from ieee_2030_5.certs import TLSRepository
from ieee_2030_5.config import ServerConfiguration
from ieee_2030_5.flask_server import run_server
from ieee_2030_5.server.server_constructs import initialize_2030_5

logging.basicConfig(level=logging.DEBUG)

_log = logging.getLogger(__name__)


def get_tls_repository(cfg: ServerConfiguration, create_certificates_for_devices: bool = True) -> TLSRepository:
    tlsrepo = TLSRepository(cfg.tls_repository,
                            cfg.openssl_cnf,
                            cfg.server_hostname,
                            cfg.proxy_hostname,
                            clear=create_certificates_for_devices)
    if create_certificates_for_devices:
        already_represented = set()

        # registers the devices, but doesn't initialize_device the end devices here.
        for k in cfg.devices:
            if k in already_represented:
                _log.error(f"Already have {k.id} represented by {k.device_category_type}")
            else:
                already_represented.add(k)
                tlsrepo.create_cert(k.id)
    return tlsrepo

#
# def get_end_devices(cfg: ServerConfiguration, tlsrepo: TLSRepository) -> Tuple[Dict[GroupLevel, Group], EndDevices]:
#     grps = get_groups()
#     devices = EndDevices()
#     # Create the enddevice on the server on startup.
#     #
#     # The other option is enddevices_register_access_only which in effect
#     # becomes a noop as the certificates should already be created for the system
#     # or added through the web interface.
#     if cfg.server_mode == "enddevices_create_on_start":
#         for k in cfg.devices:
#             device = devices.initialize_device(device_config=k, lfid=tlsrepo.lfdi(k.id))
#             # TODO: Add the ability to use other groups
#             # TODO: By default each device will have it's own named group enabling direct communication
#             # TODO: See Section 5.2.3 of CSIP Implementation Guide.
#             get_group(level=GroupLevel.NonTopology, name=k.id).add_end_device(device)
#
#
#         devices.initialize_groups()
#         # TODO: Only valid when we are adding to the subtransmission group.
#         #assert devices.num_devices == len(get_group(level=GroupLevel.NonTopology).get_devices())
#     return grps, devices


def _main():
    parser = ArgumentParser()

    parser.add_argument(dest="config", help="Configuration file for the server.")
    parser.add_argument("--no-validate",
                        action="store_true",
                        help="Allows faster startup since the resolving of addresses is not done!")
    parser.add_argument(
        "--no-create-certs",
        action="store_true",
        help="If specified certificates for for client and server will not be created.")
    opts = parser.parse_args()

    os.environ["IEEE_2030_5_CONFIG_FILE"] = str(
        Path(opts.config).expanduser().resolve(strict=True))

    cfg_dict = yaml.safe_load(Path(opts.config).expanduser().resolve(strict=True).read_text())

    config = ServerConfiguration(**cfg_dict)

    assert config.tls_repository
    assert len(config.devices) > 0
    assert config.server_hostname
    unknown = []
    # Only check for resolvability if not passed --no-validate
    if not opts.no_validate:
        _log.debug("Validating hostnames and/or ip of devices are resolvable.")
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
    tls_repo = get_tls_repository(config, create_certs)

    end_devices = initialize_2030_5(config, tls_repo)

    def build_address_tuple(hostname: str) -> Tuple[str, int]:
        """Create a Tuple[str, int] from the passed hostname.

        The hostname can be formatted using https://server:port or server:port

        :param: hostname
        """
        hostname = urlparse(hostname)

        if hostname.scheme:
            hostname = (hostname.hostname, hostname.port)
        else:
            hostname = hostname.path.split(":")
            hostname = (hostname[0], int(hostname[1]))
        return hostname

    try:
        run_server(config, tls_repo, enddevices=end_devices, debug=True)
        # server_process = Process(target=run_server,
        #                          kwargs=dict(config=config, tlsrepo=tls_repo, enddevices=end_devices, debug=True),
        #                          daemon=True)
        # server_process.start()
        # process = None
        # if config.proxy_hostname:
        #     proxy_host = build_address_tuple(config.proxy_hostname)
        #     server_host = build_address_tuple(config.server_hostname)
        #     process = Process(target=start_proxy,
        #                       kwargs=dict(proxy_target=proxy_host, server_address=server_host, tls_repo=tls_repo),
        #                       daemon=True)
        #     process.start()
        #
        # while True:
        #     time.sleep(0.1)

    except KeyboardInterrupt as ex:
        print("Shutting down server.")


if __name__ == '__main__':
    _main()
