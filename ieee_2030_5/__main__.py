import os
from argparse import ArgumentParser
import logging
from pathlib import Path
import socket
import sys
from typing import Dict, Tuple

import yaml

from ieee_2030_5.certs import TLSRepository
from ieee_2030_5.config import ServerConfiguration
from ieee_2030_5.flask_server import run_server
from ieee_2030_5.models import DeviceCategoryType
from ieee_2030_5.models.end_devices import EndDevices
from ieee_2030_5.server import get_group, get_groups, GroupLevel, Group

logging.basicConfig(level=logging.DEBUG)

_log = logging.getLogger(__name__)


def get_tls_repository(cfg: ServerConfiguration, create_certs: bool = True) -> TLSRepository:
    tlsrepo = TLSRepository(cfg.tls_repository,
                            cfg.openssl_cnf,
                            cfg.server_hostname,
                            clear=create_certs)
    if create_certs:
        already_represented = set()

        # registers the devices, but doesn't register the end devices here.
        for k in cfg.devices:
            if k in already_represented:
                _log.error(f"Already have {k.hostname} represented by {k.device_category_type}")
            else:
                already_represented.add(k)
                print(f"adding k: {k}")
                tlsrepo.create_cert(k.hostname)
    return tlsrepo


def get_end_devices(cfg: ServerConfiguration, tlsrepo: TLSRepository) -> Tuple[Dict[GroupLevel, Group], EndDevices]:
    grps = get_groups()
    devices = EndDevices()
    # Create the enddevice on the server on startup.
    #
    # The other option is enddevices_register_access_only which in effect
    # becomes a noop as the certificates should already be created for the system
    # or added through the web interface.
    if cfg.server_mode == "enddevices_create_on_start":
        for k in cfg.devices:
            device = devices.register(DeviceCategoryType[k.device_category_type],
                                      tlsrepo.lfdi(k.hostname))
            # TODO: Add the ability to use other groups
            get_group(level=GroupLevel.SubTransmission).add_end_device(device)
        # TODO: Only valid when we are adding to the subtransmission group.
        assert devices.num_devices == len(get_group(level=GroupLevel.SubTransmission).get_devices())
    return grps, devices


if __name__ == '__main__':
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
    #
    cfg_dict = yaml.safe_load(Path(opts.config).expanduser().resolve(strict=True).read_text())

    config = ServerConfiguration(**cfg_dict)

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
    tls_repo = get_tls_repository(config, create_certs)
    groups, end_devices = get_end_devices(config, tls_repo)

    try:
        run_server(config, tls_repo, enddevices=end_devices)
    except KeyboardInterrupt as ex:
        print("Shutting down server.")
