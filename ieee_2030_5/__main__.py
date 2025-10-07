# -------------------------------------------------------------------------------
# Copyright (c) 2022, Battelle Memorial Institute All rights reserved.
# Battelle Memorial Institute (hereinafter Battelle) hereby grants permission to any person or entity
# lawfully obtaining a copy of this software and associated documentation files (hereinafter the
# Software) to redistribute and use the Software in source and binary forms, with or without modification.
# Such person or entity may use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and may permit others to do so, subject to the following conditions:
# Redistributions of source code must retain the above copyright notice, this list of conditions and the
# following disclaimers.
# Redistributions in binary form must reproduce the above copyright notice, this list of conditions and
# the following disclaimer in the documentation and/or other materials provided with the distribution.
# Other than as used herein, neither the name Battelle Memorial Institute or Battelle may be used in any
# form whatsoever without the express written consent of Battelle.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL
# BATTELLE OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
# GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
# AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
# OF THE POSSIBILITY OF SUCH DAMAGE.
# General disclaimer for use with OSS licenses
#
# This material was prepared as an account of work sponsored by an agency of the United States Government.
# Neither the United States Government nor the United States Department of Energy, nor Battelle, nor any
# of their employees, nor any jurisdiction or organization that has cooperated in the development of these
# materials, makes any warranty, express or implied, or assumes any legal liability or responsibility for
# the accuracy, completeness, or usefulness or any information, apparatus, product, software, or process
# disclosed, or represents that its use would not infringe privately owned rights.
#
# Reference herein to any specific commercial product, process, or service by trade name, trademark, manufacturer,
# or otherwise does not necessarily constitute or imply its endorsement, recommendation, or favoring by the United
# States Government or any agency thereof, or Battelle Memorial Institute. The views and opinions of authors expressed
# herein do not necessarily state or reflect those of the United States Government or any agency thereof.
#
# PACIFIC NORTHWEST NATIONAL LABORATORY operated by BATTELLE for the
# UNITED STATES DEPARTMENT OF ENERGY under Contract DE-AC05-76RL01830
# -------------------------------------------------------------------------------
import contextlib
import logging
import logging.config
import os
import shutil
import sys
import threading
import time
from argparse import ArgumentParser
from dataclasses import asdict
from pathlib import Path

import yaml
from werkzeug.serving import BaseWSGIServer

import ieee_2030_5.hrefs as hrefs
from ieee_2030_5.certs import TLSRepository
from ieee_2030_5.config import InvalidConfigFile, ServerConfiguration
from ieee_2030_5.data.indexer import add_href

# Import GridAPPSDAdapter lazily to avoid early database initialization

# Configure metrics if available (optional)
try:
    from prometheus_client import Counter, Summary, start_http_server

    METRICS_AVAILABLE = True
    REQUEST_COUNT = Counter("ieee_2030_5_request_count", "Count of IEEE 2030.5 requests")
    REQUEST_LATENCY = Summary("ieee_2030_5_request_latency_seconds", "Latency of IEEE 2030.5 requests")
except ImportError:
    METRICS_AVAILABLE = False

# Global logger
_log = logging.getLogger("ieee_2030_5")


class ServerThread(threading.Thread):
    """Thread for running the IEEE 2030.5 server."""

    def __init__(self, server: BaseWSGIServer):
        threading.Thread.__init__(self, daemon=True)
        self.server = server
        self.running = True

    def run(self):
        _log.info(f"Starting server on {self.server.host}:{self.server.port}")

        # Start metrics server if available
        if METRICS_AVAILABLE:
            try:
                metrics_port = int(os.environ.get("IEEE_2030_5_METRICS_PORT", 9630))
                start_http_server(metrics_port)
                _log.info(f"Started metrics server on port {metrics_port}")
            except Exception as e:
                _log.warning(f"Failed to start metrics server: {e}")

        try:
            self.server.serve_forever()
        except Exception as e:
            if self.running:
                _log.error(f"Server error: {e}")

    def shutdown(self):
        """Gracefully shut down the server."""
        _log.info("Shutting down server...")
        self.running = False
        try:
            self.server.shutdown()
        except Exception as e:
            _log.error(f"Error shutting down server: {e}")


@contextlib.contextmanager
def tls_repository_context(cfg: ServerConfiguration, create_certificates: bool = True):
    """Context manager for TLS repository."""
    tlsrepo = get_tls_repository(cfg, create_certificates_for_devices=create_certificates)
    try:
        yield tlsrepo
    finally:
        _log.debug("Cleaning up TLS repository")


def get_tls_repository(cfg: ServerConfiguration, create_certificates_for_devices: bool = True) -> TLSRepository:
    """Initialize and return a TLS repository."""
    _log.info(f"Initializing TLS repository at {cfg.tls_repository}")
    _log.debug(f"Proxy enabled: {cfg.proxy_enabled}, Proxy host: {cfg.proxy_hostname}")

    tlsrepo = TLSRepository(
        cfg.tls_repository,
        cfg.openssl_cnf,
        cfg.server_hostname,
        proxyhost=cfg.proxy_hostname if cfg.proxy_enabled else None,
        clear=create_certificates_for_devices,
        generate_admin_cert=cfg.generate_admin_cert,
    )

    if create_certificates_for_devices:
        already_represented = set()
        # Registers the devices, but doesn't initialize_device the end devices here.
        for k in cfg.devices:
            if tlsrepo.has_device(k.id):
                already_represented.add(k)
            else:
                _log.debug(f"Creating certificate for device {k.id}")
                tlsrepo.create_cert(k.id)

    return tlsrepo


def should_stop() -> bool:
    """Check if the server should stop."""
    return Path("server.stop").exists()


def make_stop_file():
    """Create a file to signal server stop."""
    with open("server.stop", "w", encoding="ascii"):
        pass


def remove_stop_file():
    """Remove the server stop signal file."""
    pth = Path("server.stop")
    if pth.exists():
        os.remove(pth)


def get_default_logger_config(log_level: str | int = "INFO", log_file: str = "ieee_2030_5_server.log") -> dict:
    """Get a default logger configuration."""
    if isinstance(log_level, int):
        log_level = logging.getLevelName(log_level)
    return {
        "version": 1,
        "formatters": {
            "default": {"format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"},
            "brief": {"datefmt": "%H:%M:%S", "format": "%(levelname)-8s; %(name)s; %(message)s;"},
            "single-line": {
                "datefmt": "%H:%M:%S",
                "format": "%(levelname)-8s; %(asctime)s; %(name)s; %(module)s:%(funcName)s;%(lineno)d: %(message)s",
            },
            "colorized": {
                "datefmt": "%H:%M:%S",
                "()": "ieee_2030_5.utils.ColorizedFormatter",
                "format": "%(levelname)-8s; %(asctime)s; %(name)s; %(module)s:%(funcName)s;%(lineno)d: %(message)s",
            },
        },
        "handlers": {
            "console": {
                "level": log_level,
                "class": "logging.StreamHandler",
                "formatter": "colorized",
            },
            "file": {
                "level": log_level,
                "class": "logging.FileHandler",
                "formatter": "single-line",
                "filename": log_file,
                "mode": "w",  # Use 'w' mode to recreate the log file each time
            },
        },
        "loggers": {
            "": {  # root logger
                "level": log_level,
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "ieee_2030_5.persistance.points": {  # Points logger
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "ieee_2030_5.adapters.base": {  # Points logger
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False,
            },
            "ieee_2030_5.server.server_constructs": {  # Server constructs logger
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "werkzeug": {  # Flask/Werkzeug logger
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "ieee_2030_5": {  # Our package logger
                "level": log_level,
                "handlers": ["console", "file"],
                "propagate": False,  # Don't propagate to the root logger
            },
            "watchdog": {"level": "INFO", "handlers": ["console"], "propagate": False},
        },
    }


def clear_all_data(config: ServerConfiguration | None = None):
    """Clear all data, databases, and logs for a fresh start."""
    _log.info("=" * 60)
    _log.info("CLEARING ALL DATA FOR FRESH START")
    _log.info("=" * 60)

    # Storage directories
    storage_paths = []
    if config and config.storage_path:
        storage_paths.append(Path(config.storage_path))
    storage_paths.append(Path("data_store"))

    for storage_path in storage_paths:
        if storage_path.exists():
            _log.info(f"Removing storage directory: {storage_path}")
            try:
                shutil.rmtree(storage_path)
            except Exception as e:
                _log.warning(f"Failed to remove {storage_path}: {e}")

    # User data directory (contains ZODB and SQLite databases)
    data_store_userdir = Path("~/.ieee_2030_5_data").expanduser()
    if data_store_userdir.exists():
        _log.info(f"Removing user data directory: {data_store_userdir}")
        try:
            shutil.rmtree(data_store_userdir)
        except Exception as e:
            _log.warning(f"Failed to remove {data_store_userdir}: {e}")

    # Debug client traffic logs
    debug_traffic_dir = Path("debug_client_traffic")
    if debug_traffic_dir.exists():
        _log.info(f"Removing debug client traffic logs: {debug_traffic_dir}")
        try:
            shutil.rmtree(debug_traffic_dir)
        except Exception as e:
            _log.warning(f"Failed to remove {debug_traffic_dir}: {e}")

    # Server log files
    log_files = [Path("ieee_2030_5_server.log"), Path("server.log"), Path("proxy.log"), Path("gridappsd.log")]

    for log_file in log_files:
        if log_file.exists():
            _log.info(f"Removing log file: {log_file}")
            try:
                log_file.unlink()
            except Exception as e:
                _log.warning(f"Failed to remove {log_file}: {e}")

    # Flask session data
    flask_session_dir = Path("flask_session")
    if flask_session_dir.exists():
        _log.info(f"Removing Flask session data: {flask_session_dir}")
        try:
            shutil.rmtree(flask_session_dir)
        except Exception as e:
            _log.warning(f"Failed to remove {flask_session_dir}: {e}")

    # Custom database path if specified
    if config and config.database_path:
        db_path = Path(config.database_path).expanduser()
        # Handle both file and directory database backends
        if db_path.exists():
            _log.info(f"Removing database: {db_path}")
            try:
                if db_path.is_dir():
                    shutil.rmtree(db_path)
                else:
                    db_path.unlink()
            except Exception as e:
                _log.warning(f"Failed to remove {db_path}: {e}")

        # Also remove any associated files (like SQLite journal files)
        db_parent = db_path.parent
        if db_parent.exists():
            for related_file in db_parent.glob(f"{db_path.stem}*"):
                _log.info(f"Removing related database file: {related_file}")
                try:
                    related_file.unlink()
                except Exception as e:
                    _log.warning(f"Failed to remove {related_file}: {e}")

    # Stop file if it exists
    stop_file = Path("server.stop")
    if stop_file.exists():
        _log.info("Removing server stop file")
        try:
            stop_file.unlink()
        except Exception as e:
            _log.warning(f"Failed to remove stop file: {e}")

    _log.info("=" * 60)
    _log.info("Data clearing complete!")
    _log.info("=" * 60)


def setup_storage(config: ServerConfiguration):
    """Set up and prepare storage for the server."""
    # Initialize the data storage for the adapters
    if config.storage_path is None:
        config.storage_path = Path("data_store")
    else:
        config.storage_path = Path(config.storage_path)

    # Cleanse means we want to reload the storage each time the server
    # is run. Note this is dependent on the adapter being filestore
    # not database. I will have to modify later to deal with that.
    if config.cleanse_storage and config.storage_path.exists():
        _log.info(f"Removing storage directory {config.storage_path}")
        shutil.rmtree(config.storage_path)

    data_store_userdir = Path("~/.ieee_2030_5_data").expanduser()
    if config.cleanse_storage and data_store_userdir.exists():
        _log.info(f"Removing user data directory {data_store_userdir}")
        shutil.rmtree(data_store_userdir)

    # Create storage directory if it doesn't exist
    if not config.storage_path.exists():
        _log.info(f"Creating storage directory {config.storage_path}")
        config.storage_path.mkdir(parents=True, exist_ok=True)


def _main():
    """Main entry point for the IEEE 2030.5 server."""
    global _log

    # Parse command line arguments
    parser = ArgumentParser(description="IEEE 2030.5 Server")
    parser.add_argument(dest="config", help="Configuration file for the server.")
    parser.add_argument(
        "--create-certs", action="store_true", help="If specified, certificates for client and server will be created."
    )
    parser.add_argument("--debug", action="store_true", help="Debug level of the server")
    parser.add_argument(
        "--production", action="store_true", default=False, help="Run the server in a threaded environment."
    )
    parser.add_argument("--lfdi", help="Use lfdi mode allows a single lfdi to be connected to on an http connection")
    parser.add_argument(
        "--show-lfdi", action="store_true", help="Show all of the lfdi for the generated certificates and exit."
    )
    parser.add_argument(
        "--simulation_id", help="When running as a service the simulation_id must be passed for it to run in this mode."
    )
    parser.add_argument(
        "--metrics-port", type=int, default=9630, help="Port for metrics server (if prometheus_client is installed)"
    )
    parser.add_argument(
        "--num-threads", type=int, default=4, help="Number of threads to use for the server (requires --production)"
    )
    parser.add_argument("--with-proxy", action="store_true", help="Enable proxy mode")
    parser.add_argument("--proxy-debug", action="store_true", help="Enable proxy debug logging")
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear all data and logs for a fresh start (databases, debug logs, storage)",
    )
    parser.add_argument(
        "--log-file", type=str, help="Output log to specified file instead of default ieee_2030_5_server.log"
    )
    parser.add_argument("--admin-http-port", type=int, default=5001, help="Port for HTTP admin access (default: 5001)")
    parser.add_argument("--dual-server", action="store_true", help="Run both HTTPS (API) and HTTP (admin) servers")

    opts = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if opts.debug else logging.INFO

    # Set up metrics if available
    if METRICS_AVAILABLE:
        os.environ["IEEE_2030_5_METRICS_PORT"] = str(opts.metrics_port)

    # Configure logging
    log_file = opts.log_file if opts.log_file else "ieee_2030_5_server.log"
    # Check if external logging config file exists
    logging_config_path = Path("logging_config.yml")
    if logging_config_path.exists():

        try:
            with open(logging_config_path) as f:
                log_config = yaml.safe_load(f)
            _log_early = logging.getLogger("ieee_2030_5")
            _log_early.info(f"Using external logging configuration from {logging_config_path}")
        except Exception as e:
            print(f"Failed to load logging config from {logging_config_path}: {e}")
            log_config = get_default_logger_config(log_level, log_file)
    else:
        log_config = get_default_logger_config(log_level, log_file)

    # Remove all existing handlers before configuring
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.config.dictConfig(log_config)
    logging.getLogger("watchdog.observers.inotify_buffer").setLevel(logging.INFO)
    _log = logging.getLogger("ieee_2030_5")

    # Handle --clear flag before server startup
    if opts.clear:
        # Load config to get database paths
        config = None
        try:
            config_path = Path(opts.config).expanduser().resolve(strict=True)
            cfg_dict = yaml.safe_load(config_path.read_text())
            config = ServerConfiguration(**cfg_dict)
        except Exception as e:
            _log.warning(f"Could not load config for clearing: {e}")

        clear_all_data(config)
        _log.info("Data cleared successfully! Continuing with server startup...")

    _log.info("Starting IEEE 2030.5 server")

    # Set environment variables
    config_path = Path(opts.config).expanduser().resolve(strict=True)
    os.environ["IEEE_2030_5_CONFIG_FILE"] = str(config_path)

    # Load configuration
    try:
        _log.info(f"Loading configuration from {config_path}")
        cfg_dict = yaml.safe_load(config_path.read_text())
        config = ServerConfiguration(**cfg_dict)
    except Exception as e:
        _log.error(f"Failed to load configuration: {e}")
        raise InvalidConfigFile(f"Failed to load configuration: {e}") from e

    if opts.with_proxy:
        config.proxy_enabled = True
    if opts.proxy_debug:
        config.proxy_debug = True

    # Set service environment variables
    if config.service_name:
        os.environ["GRIDAPPSD_SERVICE_NAME"] = config.service_name

    if config.simulation_id:
        os.environ["GRIDAPPSD_SIMULATION_ID"] = config.simulation_id

    if opts.simulation_id:
        os.environ["GRIDAPPSD_SIMULATION_ID"] = opts.simulation_id
        config.simulation_id = opts.simulation_id

    if config.lfdi_mode == "lfdi_mode_from_file":
        os.environ["IEEE_2030_5_CERT_FROM_COMBINED_FILE"] = "1"

    # Validate configuration
    assert config.tls_repository, "TLS repository not specified in configuration"
    assert config.server_hostname, "Server hostname not specified in configuration"

    def format_config_value(value):
        """Format configuration values for display."""
        if isinstance(value, dict):
            if not value:  # Empty dict
                return "{}"
            # Format dict as key=value pairs
            items = [f"{k}={v}" for k, v in value.items()]
            return "{" + ", ".join(items) + "}"
        elif isinstance(value, list):
            if not value:  # Empty list
                return "[]"
            return f"[{len(value)} items]"
        else:
            return str(value)

    config_table = ["Configuration", "-" * 60, f"{'Key':<30} | {'Value'}", "-" * 60]
    config_table.extend([f"{key:<30} | {format_config_value(value)}" for key, value in sorted(asdict(config).items())])
    config_table.append("-" * 60)
    _log.info("\n".join(config_table))

    _log.info("Configuration")
    for key, value in sorted(asdict(config).items()):
        _log.info(f"Config '{key}': {value}")

    # Configure the point store backend before any database operations
    from ieee_2030_5.persistance.points import configure_point_store

    configure_point_store(backend=config.database_backend, db_path=config.database_path)
    _log.info(f"Configured {config.database_backend} point store backend")

    # Add server configuration to URL registry
    add_href(hrefs.get_server_config_href(), config)

    # Set up TLS repository
    with tls_repository_context(config, create_certificates=opts.create_certs) as tls_repo:
        # Show LFDI if requested
        if opts.show_lfdi:
            for cn in config.devices:
                sys.stdout.write(f"{cn.id} {tls_repo.lfdi(cn.id)}\n")
            return 0

        # GridAPPSD integration
        gridappsd_adpt = None
        if config.gridappsd is not None:
            _log.info(f"Connecting to GridAPPSD at {config.gridappsd.address}:{config.gridappsd.port}")

            try:
                from gridappsd import GridAPPSD

                from ieee_2030_5.adapters.gridappsd_adapter import GridAPPSDAdapter

                gapps = GridAPPSD(
                    stomp_address=config.gridappsd.address,
                    stomp_port=config.gridappsd.port,
                    username=config.gridappsd.username,
                    password=config.gridappsd.password,
                )

                assert gapps.connected, "Failed to connect to GridAPPSD"

                gridappsd_adpt = GridAPPSDAdapter(gapps=gapps, gridappsd_configuration=config.gridappsd, tls=tls_repo)

                gridappsd_devices: list = []
                if opts.create_certs:
                    _log.info("Creating certificates for GridAPPSD devices")
                    gridappsd_devices = gridappsd_adpt.create_2030_5_device_certificates_and_configurations()
                else:
                    _log.info("Getting device configurations from GridAPPSD")
                    gridappsd_devices = gridappsd_adpt.get_device_configurations()

                config.devices.extend(gridappsd_devices)
                _log.info(f"Added {len(gridappsd_devices)} devices from GridAPPSD")
            except Exception as e:
                _log.error(f"Failed to initialize GridAPPSD adapter: {e}")
                if opts.debug:
                    import traceback

                    traceback.print_exc()

        # Set LFDI client mode if specified
        if opts.lfdi:
            _log.info(f"Running in single client LFDI mode with LFDI {opts.lfdi}")
            config.lfdi_client = opts.lfdi

        # Set up storage
        setup_storage(config)

        # Initialize the IEEE 2030.5 server
        # Initialize adapters before server initialization
        from ieee_2030_5.adapters.base import initialize_adapters
        from ieee_2030_5.server.server_constructs import initialize_2030_5

        initialize_adapters()
        _log.info("Adapters initialized for server startup")

        _log.info("Initializing IEEE 2030.5 server")
        initialize_2030_5(config, tls_repo)

        # Start GridAPPSD publishing if available
        if gridappsd_adpt:
            _log.info("Starting GridAPPSD publishing")
            gridappsd_adpt.start_publishing()

            # Enable message bus monitoring
            try:
                from ieee_2030_5.monitoring import get_message_monitor, patch_gridappsd_adapter

                patch_gridappsd_adapter()
                monitor = get_message_monitor()
                monitor.enable()
                _log.info("GridAPPS-D message bus monitoring enabled")
            except Exception as e:
                _log.warning(f"Could not enable message bus monitoring: {e}")

        # Run the server
        from ieee_2030_5.flask_server import build_server, run_dual_server, run_server

        if opts.production:
            _log.info(f"Running in production mode with {opts.num_threads} threads")

            # Create and configure the server
            server = build_server(config, tls_repo)

            # Start the server in a thread
            thread = ServerThread(server)
            thread.start()

            # Monitor for stop signal
            try:
                remove_stop_file()
                _log.info("Server is running. Press Ctrl+C to stop.")

                while not should_stop() and thread.is_alive():
                    time.sleep(0.5)

                if not thread.is_alive():
                    _log.error("Server thread died unexpectedly")

            except KeyboardInterrupt:
                _log.info("Keyboard interrupt received")

            finally:
                _log.info("Shutting down server")
                if thread.is_alive():
                    thread.shutdown()
                    thread.join(timeout=5.0)

                if thread.is_alive():
                    _log.warning("Server did not shut down cleanly")
        else:
            # Development mode - run directly
            if opts.dual_server or getattr(config, "dual_server_enabled", False):
                # Use command line arg if provided, otherwise use config value
                admin_port = opts.admin_http_port if opts.dual_server else getattr(config, "admin_http_port", 5001)
                _log.info(f"Running in development mode with dual servers (HTTPS + HTTP admin on port {admin_port})")
                try:
                    run_dual_server(
                        config,
                        tls_repo,
                        admin_http_port=admin_port,
                        debug=opts.debug,
                        use_reloader=False,
                        use_debugger=opts.debug,
                        threaded=True,
                    )  # Enable threading for better performance
                except KeyboardInterrupt:
                    _log.info("Keyboard interrupt received")
                except Exception as e:
                    _log.error(f"Dual server error: {e}")
                    if opts.debug:
                        import traceback

                        traceback.print_exc()
            else:
                _log.info("Running in development mode")
                try:
                    run_server(
                        config, tls_repo, debug=opts.debug, use_reloader=False, use_debugger=opts.debug, threaded=True
                    )  # Enable threading for better performance
                except KeyboardInterrupt:
                    _log.info("Keyboard interrupt received")
                except Exception as e:
                    _log.error(f"Server error: {e}")
                    if opts.debug:
                        import traceback

                        traceback.print_exc()
                finally:
                    _log.info("Server shutdown complete")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(_main())
    except InvalidConfigFile as ex:
        print(ex.args[0], file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        _log.info("Interrupted by user")
        sys.exit(0)
    # except Exception as ex:
    #     if _log:
    #         _log.exception("Unhandled exception")
    #     else:
    #         print(f"Error: {ex}", file=sys.stderr)
    #     sys.exit(1)
