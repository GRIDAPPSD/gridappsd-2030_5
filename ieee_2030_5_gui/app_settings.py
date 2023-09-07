"""

"""
import logging
import os
from contextvars import ContextVar
from pathlib import Path
from typing import Optional

import yaml

from ieee_2030_5.certs import TLSRepository
from ieee_2030_5.config import ServerConfiguration

_log = logging.getLogger(__name__)

cfg_file = Path(os.environ.get("CONFIG_FILE")).expanduser().resolve(strict=True)

if not cfg_file.exists():
    raise FileNotFoundError(f"Config file {cfg_file} does not exist")

_log.debug(f"Loading config from {cfg_file}")
cfg_dict = yaml.safe_load(cfg_file.read_text())

_server_config = ServerConfiguration(**cfg_dict)
_tls_repo = TLSRepository(_server_config.tls_repository,
                            _server_config.openssl_cnf,
                            _server_config.server_hostname,
                            _server_config.proxy_hostname,
                            clear=False)

_log.debug(f"Loading context vars for tls and server config")
tls_repo_var = ContextVar("tls_repo_var", default=_tls_repo)
server_config_var = ContextVar("server_config_var", default=_server_config)

def get_tls_repo() -> TLSRepository:
    tls_repo = tls_repo_var.get()
    assert tls_repo, "TLS Repo not loaded"
    return tls_repo

def get_server_config() -> ServerConfiguration:
    server_config = server_config_var.get()
    assert server_config, "Server config not loaded"
    return server_config


