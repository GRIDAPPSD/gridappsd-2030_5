"""
IEEE 2030.5 Basic Proxy Server

This module implements a multi-threaded TLS proxy server that forwards client requests
to a backend IEEE 2030.5 server while preserving client certificate information.

The proxy acts as an intermediary between IEEE 2030.5 clients and servers, providing:
- Client certificate forwarding via HTTP headers (Nginx-style)
- Concurrent client support with HTTP/1.1 persistent connections
- Dynamic SSL/TLS context selection based on client certificates
- Proper error handling and logging for production environments
- Connection pooling and timeout management for optimal performance

Key Components:
- RequestForwarder: HTTP request handler for client requests
- ProxyServer: Multi-threaded server supporting concurrent clients
- HTTPSConnectionWithTimeout: Enhanced HTTPS client for backend connections
- Certificate management helpers for dynamic context creation

The proxy preserves the security model of IEEE 2030.5 by forwarding client certificates
as HTTP headers, allowing the backend server to authenticate clients while the proxy
handles TLS termination and connection multiplexing.

Typical Usage:
    python basic_proxy.py config.yml --debug

Author: GridAPPS-D Team
License: See LICENSE file
"""

from __future__ import annotations

import logging
import logging.handlers
import os
import socket
import ssl
import threading
import time
from dataclasses import dataclass
from http.client import HTTPSConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import OpenSSL
import yaml

from ieee_2030_5.certs import TLSRepository, lfdi_from_fingerprint, sfdi_from_lfdi
from ieee_2030_5.config import ServerConfiguration

# Global connection status tracker for publishing to GridAPPS-D
_connection_status_lock = threading.Lock()
_connection_status = {}  # {lfdi: {"client_address": (ip, port), "connect_time": datetime_str, "disconnect_time": None or datetime_str}}
_stomp_publisher = None  # Will be set when proxy starts if GridAPPS-D is configured


def _track_connection(lfdi: str, client_address: tuple, connected: bool):
    """
    Track client connection/disconnection for publishing to GridAPPS-D.

    Args:
        lfdi: Client identifier (LFDI or IP-based)
        client_address: Tuple of (ip, port)
        connected: True for connect, False for disconnect
    """
    from datetime import datetime

    with _connection_status_lock:
        now = datetime.now().isoformat()

        if connected:
            _connection_status[lfdi] = {
                "client_address": f"{client_address[0]}:{client_address[1]}",
                "connect_time": now,
                "disconnect_time": None,
                "lfdi": lfdi
            }
            _log.debug(f"Tracked connection for {lfdi[:16]}... from {client_address}")
        else:
            if lfdi in _connection_status:
                _connection_status[lfdi]["disconnect_time"] = now
                _log.debug(f"Tracked disconnection for {lfdi[:16]}...")

    # Immediately publish connection status on connect/disconnect
    if _stomp_publisher:
        _stomp_publisher.publish_now()


def _get_connection_status_snapshot() -> dict:
    """
    Get a snapshot of all connection statuses for publishing.

    Returns:
        Dictionary with connection status for all tracked clients
    """
    with _connection_status_lock:
        return {
            "timestamp": time.time(),
            "connections": dict(_connection_status)
        }


class GridAPPSDConnectionPublisher:
    """
    Publishes proxy client connection status to GridAPPS-D message bus.

    Publishes connection/disconnection events every minute to:
    /topic/goss.gridappsd.IEEE_2030_5_proxy.output
    """

    PUBLISH_TOPIC = "/topic/goss.gridappsd.IEEE_2030_5_proxy.output"
    PUBLISH_INTERVAL = 60  # seconds

    def __init__(self, gridappsd_address: str = "localhost", gridappsd_port: int = 61613,
                 username: str = "system", password: str = "manager"):
        """
        Initialize the publisher.

        Args:
            gridappsd_address: GridAPPS-D STOMP broker address
            gridappsd_port: GridAPPS-D STOMP broker port
            username: STOMP username
            password: STOMP password
        """
        self.gridappsd_address = gridappsd_address
        self.gridappsd_port = gridappsd_port
        self.username = username
        self.password = password
        self._stomp_conn = None
        self._running = False
        self._publish_thread = None

    def start(self):
        """Start the publisher thread."""
        if self._running:
            return

        self._running = True
        self._publish_thread = threading.Thread(target=self._publish_loop, daemon=True)
        self._publish_thread.start()
        _log.info(f"GridAPPS-D connection publisher started, publishing to {self.PUBLISH_TOPIC} every {self.PUBLISH_INTERVAL}s")

    def stop(self):
        """Stop the publisher thread."""
        self._running = False
        if self._stomp_conn:
            try:
                self._stomp_conn.disconnect()
            except Exception as e:
                _log.debug(f"Error disconnecting STOMP: {e}")
        _log.info("GridAPPS-D connection publisher stopped")

    def _connect_stomp(self) -> bool:
        """Connect to STOMP broker."""
        try:
            import stomp

            self._stomp_conn = stomp.Connection([(self.gridappsd_address, self.gridappsd_port)])
            self._stomp_conn.connect(self.username, self.password, wait=True)
            _log.debug(f"Connected to GridAPPS-D STOMP at {self.gridappsd_address}:{self.gridappsd_port}")
            return True
        except ImportError:
            _log.warning("stomp-py not installed, cannot publish to GridAPPS-D")
            return False
        except Exception as e:
            _log.warning(f"Failed to connect to GridAPPS-D STOMP: {e}")
            return False

    def _publish_loop(self):
        """Main publish loop - runs every minute."""
        import json

        while self._running:
            try:
                # Ensure connected
                if not self._stomp_conn or not self._stomp_conn.is_connected():
                    if not self._connect_stomp():
                        time.sleep(self.PUBLISH_INTERVAL)
                        continue

                # Get connection status snapshot
                status = _get_connection_status_snapshot()

                # Publish to topic
                message = json.dumps(status)
                self._stomp_conn.send(
                    destination=self.PUBLISH_TOPIC,
                    body=message,
                    content_type="application/json"
                )
                _log.debug(f"Published connection status: {len(status['connections'])} clients tracked")

            except Exception as e:
                _log.warning(f"Error publishing connection status: {e}")
                self._stomp_conn = None  # Force reconnect on next iteration

            # Wait for next publish interval
            time.sleep(self.PUBLISH_INTERVAL)

    def publish_now(self):
        """Immediately publish connection status (called on new connections)."""
        import json

        try:
            # Ensure connected
            if not self._stomp_conn or not self._stomp_conn.is_connected():
                if not self._connect_stomp():
                    _log.warning("Cannot publish immediately - not connected to GridAPPS-D")
                    return

            # Get connection status snapshot
            status = _get_connection_status_snapshot()

            # Publish to topic
            message = json.dumps(status)
            self._stomp_conn.send(
                destination=self.PUBLISH_TOPIC,
                body=message,
                content_type="application/json"
            )
            _log.info(f"Published connection status immediately: {len(status['connections'])} clients tracked")

        except Exception as e:
            _log.warning(f"Error publishing connection status immediately: {e}")


# Create a custom formatter that includes file name and line number
class DetailedFormatter(logging.Formatter):
    """
    Custom logging formatter that includes file name and line number information.

    This formatter enhances log messages by adding the source file name and line number
    where the log message was generated, making debugging easier in multi-file applications.

    Attributes:
        Standard logging.Formatter attributes plus:
        - file_info: Automatically added field containing "filename:lineno"

    Example output:
        2025-07-30 10:30:45,123 - basic_proxy.py:245 - ieee_2030_5.basic_proxy - INFO - Message
    """

    def format(self, record):
        """
        Format a log record with file information.

        Args:
            record: LogRecord object containing the log message and metadata

        Returns:
            str: Formatted log message string with file information
        """
        # Add file name and line number to the log message
        if hasattr(record, "pathname"):
            record.file_info = f"{os.path.basename(record.pathname)}:{record.lineno}"
        else:
            record.file_info = "unknown:0"
        return super().format(record)


# Setup root logger with the detailed formatter
def setup_logging(debug=False, use_syslog=False, syslog_facility="local0", log_file=None):
    """
    Configure the application logging system with enhanced formatting.

    Sets up console and/or syslog logging with detailed formatting that includes
    file names, line numbers, timestamps, and log levels. Clears any existing
    handlers to avoid duplicate log messages.

    Args:
        debug (bool, optional): If True, sets log level to DEBUG for verbose output.
                               If False, sets log level to INFO. Defaults to False.
        use_syslog (bool, optional): If True, adds syslog handler for system logging.
                                    Defaults to False.
        syslog_facility (str, optional): Syslog facility to use (e.g., 'local0', 'daemon').
                                        Defaults to 'local0'.
        log_file (str, optional): Path to log file. If specified, logs will be written
                                 to this file in addition to console. Defaults to None.

    Returns:
        logging.Logger: The configured root logger instance

    Syslog Integration:
        When syslog is enabled, log messages are sent to the system log daemon
        with the specified facility. This allows integration with system monitoring
        tools and centralized log management.

    Example:
        >>> logger = setup_logging(debug=True, use_syslog=True, log_file="/var/log/proxy.log")
        >>> logger.info("Logging configured successfully")
    """
    level = logging.DEBUG if debug else logging.INFO
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    console = logging.StreamHandler()
    console.setLevel(level)
    formatter = DetailedFormatter("%(asctime)s - %(file_info)s - %(name)s - %(levelname)s - %(message)s")
    console.setFormatter(formatter)
    root_logger.addHandler(console)

    # Add syslog handler if requested
    if use_syslog:
        try:
            # Map facility names to syslog constants
            facility_map = {
                "kern": logging.handlers.SysLogHandler.LOG_KERN,
                "user": logging.handlers.SysLogHandler.LOG_USER,
                "mail": logging.handlers.SysLogHandler.LOG_MAIL,
                "daemon": logging.handlers.SysLogHandler.LOG_DAEMON,
                "auth": logging.handlers.SysLogHandler.LOG_AUTH,
                "syslog": logging.handlers.SysLogHandler.LOG_SYSLOG,
                "lpr": logging.handlers.SysLogHandler.LOG_LPR,
                "news": logging.handlers.SysLogHandler.LOG_NEWS,
                "uucp": logging.handlers.SysLogHandler.LOG_UUCP,
                "cron": logging.handlers.SysLogHandler.LOG_CRON,
                "authpriv": logging.handlers.SysLogHandler.LOG_AUTHPRIV,
                "ftp": logging.handlers.SysLogHandler.LOG_FTP,
                "local0": logging.handlers.SysLogHandler.LOG_LOCAL0,
                "local1": logging.handlers.SysLogHandler.LOG_LOCAL1,
                "local2": logging.handlers.SysLogHandler.LOG_LOCAL2,
                "local3": logging.handlers.SysLogHandler.LOG_LOCAL3,
                "local4": logging.handlers.SysLogHandler.LOG_LOCAL4,
                "local5": logging.handlers.SysLogHandler.LOG_LOCAL5,
                "local6": logging.handlers.SysLogHandler.LOG_LOCAL6,
                "local7": logging.handlers.SysLogHandler.LOG_LOCAL7,
            }

            facility = facility_map.get(syslog_facility.lower(), logging.handlers.SysLogHandler.LOG_LOCAL0)

            # Try to connect to syslog daemon
            syslog_handler = logging.handlers.SysLogHandler(address="/dev/log", facility=facility)
            syslog_handler.setLevel(level)

            # Use a simpler format for syslog (syslog daemon adds timestamp)
            syslog_formatter = logging.Formatter(
                "ieee2030_5_proxy[%(process)d]: %(file_info)s - %(name)s - %(levelname)s - %(message)s"
            )
            syslog_handler.setFormatter(syslog_formatter)
            root_logger.addHandler(syslog_handler)

            # Log successful syslog setup after root_logger is configured
            temp_log = logging.getLogger(__name__)
            temp_log.info(f"Syslog logging enabled with facility: {syslog_facility}")

        except Exception as e:
            # Fall back to console-only logging if syslog fails
            temp_log = logging.getLogger(__name__)
            temp_log.warning(f"Failed to setup syslog logging: {e}. Continuing with console logging only.")

    # Add file handler if log file is specified
    if log_file:
        try:
            # Use 'w' mode to overwrite the file on each restart instead of appending
            file_handler = logging.FileHandler(log_file, mode='w')
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

            # Log successful file logging setup
            temp_log = logging.getLogger(__name__)
            temp_log.info(f"File logging enabled: {log_file} (file will be overwritten on restart)")
        except Exception as e:
            # Fall back to console/syslog logging if file setup fails
            temp_log = logging.getLogger(__name__)
            temp_log.warning(f"Failed to setup file logging: {e}. Continuing without file logging.")

    return root_logger


_log = logging.getLogger(__name__)


@dataclass
class ContextWithPaths:
    """
    Data class containing SSL context and associated certificate file paths.

    This class bundles an SSL context with the file paths of the certificates
    used to create it, providing a convenient way to track which certificates
    are being used for a particular connection.

    Attributes:
        context (ssl.SSLContext): Configured SSL context ready for use
        certpath (str): Absolute path to the certificate file used
        keypath (str): Absolute path to the private key file used

    Example:
        >>> ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        >>> ccp = ContextWithPaths(ctx, "/path/cert.pem", "/path/key.pem")
        >>> connection = HTTPSConnection(host, context=ccp.context)
    """

    context: ssl.SSLContext
    certpath: str
    keypath: str


class HTTPSConnectionWithTimeout(HTTPSConnection):
    """
    Enhanced HTTPSConnection with configurable timeouts and better error handling.

    Extends the standard HTTPSConnection to provide:
    - Separate connect and read timeouts for better control
    - Enhanced SSL error handling and logging
    - Context preservation for debugging
    - Graceful fallback mechanisms

    This class is optimized for use in proxy scenarios where connection reliability
    and timeout control are critical for maintaining good user experience.

    Attributes:
        timeout_connect (int): Socket connection timeout in seconds
        timeout_read (int): Socket read timeout in seconds
        context (ssl.SSLContext): SSL context for secure connections

    Example:
        >>> conn = HTTPSConnectionWithTimeout(
        ...     host="example.com", port=443,
        ...     context=ssl_context,
        ...     timeout_connect=10, timeout_read=30
        ... )
        >>> conn.connect()
        >>> conn.request("GET", "/path")
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize HTTPSConnection with custom timeout settings.

        Args:
            *args: Positional arguments passed to HTTPSConnection
            **kwargs: Keyword arguments, with special handling for:
                timeout_connect (int): Connection timeout in seconds (default: 30)
                timeout_read (int): Read timeout in seconds (default: 0 = no timeout)
                context (ssl.SSLContext): SSL context for the connection
        """
        # Set timeouts - 0 means no timeout (indefinite)
        self.timeout_connect = kwargs.pop("timeout_connect", 30)
        self.timeout_read = kwargs.pop("timeout_read", 0)  # Changed default from 30 to 0 (no timeout)

        # Save context explicitly as an instance attribute
        self.context = kwargs.get("context")

        _log.debug(
            f"Creating HTTPSConnection with timeouts: connect={self.timeout_connect}s, read={self.timeout_read}s"
        )
        super().__init__(*args, **kwargs)

    def connect(self):
        """
        Connect to the host and port with enhanced error handling.

        Establishes a socket connection, applies SSL context, and configures timeouts.
        Provides detailed logging for debugging connection issues in proxy scenarios.

        Raises:
            ssl.SSLError: For SSL-related connection failures
            socket.timeout: For connection timeout failures
            Exception: For other connection failures
        """
        _log.debug(f"Attempting to connect to {self.host}:{self.port}")
        try:
            # Use connect timeout
            self.sock = socket.create_connection((self.host, self.port), self.timeout_connect)
            _log.debug(f"Socket connected to {self.host}:{self.port}")

            if self._tunnel_host:
                _log.debug(f"Setting up tunnel to {self._tunnel_host}")
                self._tunnel()

            # Apply SSL context
            if hasattr(self, "context") and self.context:
                _log.debug("Wrapping socket with provided SSL context")
                self.sock = self.context.wrap_socket(self.sock, server_hostname=self.host)
                _log.debug(
                    f"SSL handshake complete, cipher: {self.sock.cipher() if hasattr(self.sock, 'cipher') else 'unknown'}"
                )
            else:
                # Fallback to default SSL
                _log.debug(f"Wrapping socket with default SSL (cert={self.cert_file}, key={self.key_file})")
                self.sock = ssl.wrap_socket(self.sock, keyfile=self.key_file, certfile=self.cert_file)

            # Set socket read timeout (None = blocking/infinite, not 0)
            # A timeout of 0 means non-blocking, which causes immediate read failures
            timeout = None if self.timeout_read == 0 else self.timeout_read
            self.sock.settimeout(timeout)
            _log.debug(f"Connection to {self.host}:{self.port} established successfully")

        except ssl.SSLError as e:
            _log.error(f"SSL Error connecting to {self.host}:{self.port}: {e}", exc_info=True)
            # Log SSL specific details if available
            if hasattr(e, "verify_message"):
                _log.error(f"SSL verification error: {e.verify_message}")
            raise
        except TimeoutError:
            _log.error(f"Connection timeout to {self.host}:{self.port} after {self.timeout_connect}s")
            raise
        except Exception as e:
            _log.error(f"Error connecting to {self.host}:{self.port}: {e}", exc_info=True)
            raise


class RequestForwarder(BaseHTTPRequestHandler):
    """
    HTTP request handler that forwards requests to a target server while maintaining client connections.

    This class implements a reverse proxy that:
    - Accepts client connections with TLS client certificates
    - Forwards requests to a backend IEEE 2030.5 server
    - Preserves client certificate information via HTTP headers
    - Supports HTTP/1.1 persistent connections for performance
    - Handles multiple concurrent clients safely

    The handler extracts client certificate information and forwards it as HTTP headers
    similar to how Nginx handles client certificates, allowing the backend server to
    perform certificate-based authentication.

    Key Features:
    - HTTP/1.1 keep-alive support for connection reuse
    - Dynamic SSL context selection based on client certificates
    - Comprehensive error handling and logging
    - Support for all standard HTTP methods
    - Client certificate forwarding via headers

    Attributes:
        protocol_version (str): HTTP protocol version (HTTP/1.1)
        timeout (int): Client connection timeout in seconds
        server (ProxyServer): Reference to the proxy server instance
    """

    # Use HTTP/1.1 to support persistent connections with clients
    protocol_version = "HTTP/1.1"

    # Set timeout for client connections - 0 means no timeout (indefinite)
    timeout = 0  # No timeout - never disconnect active connections

    # Type annotation for the server to ensure it has our required attributes
    server: ProxyServer

    # Class-level connection tracking registries
    _connection_lock = threading.Lock()  # Protect concurrent access to registries
    _connections_by_lfdi = {}  # {lfdi: {"conn_id": id, "handler": handler, "last_activity": time}}
    _backend_pool = {}  # {lfdi: backend_connection} - reuse backend connections per client
    _connection_attempts = {}  # {ip_address: [timestamp1, timestamp2, ...]} - for rate limiting

    def setup(self):
        """
        Set up the request handler with proper timeouts for concurrent clients.

        Initializes client connection timeouts and verifies that the server has
        all required attributes for proxy operation. This method is called
        automatically by the server framework before handling requests.

        Raises:
            RuntimeError: If server is missing required attributes (tls_repo, proxy_target)
        """
        super().setup()
        # Set client socket timeout to prevent hanging connections
        # Convert timeout=0 to None (blocking/infinite) to avoid non-blocking mode
        if hasattr(self.connection, "settimeout"):
            timeout = None if self.timeout == 0 else self.timeout
            self.connection.settimeout(timeout)
            _log.debug(f"Set client connection timeout to {self.timeout}s for {self.client_address}")

        # Verify server has required attributes
        if not hasattr(self.server, "tls_repo"):
            _log.error(f"Server {type(self.server)} does not have tls_repo attribute")
            raise RuntimeError("Server missing tls_repo attribute")
        if not hasattr(self.server, "proxy_target"):
            _log.error(f"Server {type(self.server)} does not have proxy_target attribute")
            raise RuntimeError("Server missing proxy_target attribute")

        _log.debug(f"RequestForwarder setup complete for {self.client_address}")

    def _extract_client_lfdi(self) -> str | None:
        """
        Extract LFDI (Long Form Device Identifier) from client TLS certificate.

        Returns the SHA-256 hash of the client certificate as the LFDI, or None if
        no certificate is available. Falls back to IP address if certificate unavailable.

        Returns:
            str: LFDI hex string, IP address, or None
        """
        try:
            # Try to get peer certificate from TLS connection
            if hasattr(self.connection, 'getpeercert') and callable(self.connection.getpeercert):
                cert_binary = self.connection.getpeercert(binary_form=True)
                if cert_binary:
                    # Calculate SHA-256 hash of certificate (this is the LFDI)
                    import hashlib
                    lfdi = hashlib.sha256(cert_binary).hexdigest()
                    _log.debug(f"Extracted LFDI from certificate: {lfdi[:16]}...")
                    return lfdi

            # Fallback: use IP address as identifier if no certificate
            ip_address = self.client_address[0]
            _log.debug(f"No certificate available, using IP as identifier: {ip_address}")
            return f"ip_{ip_address}"

        except Exception as e:
            _log.warning(f"Error extracting client LFDI: {e}")
            # Last resort: use IP address
            return f"ip_{self.client_address[0]}"

    def _check_rate_limit(self) -> bool:
        """
        Check if client IP has exceeded rate limit for connection attempts.

        Uses sliding window approach: allows burst of connections, then rate limits.
        Configured for 20 connections per minute per IP by default.

        Returns:
            bool: True if allowed, False if rate limit exceeded
        """
        max_per_minute = 20  # Allow 20 connections per minute
        window = 60  # 60 second window

        ip_address = self.client_address[0]
        now = time.time()

        with self._connection_lock:
            # Get or create attempt list for this IP
            if ip_address not in self._connection_attempts:
                self._connection_attempts[ip_address] = []

            attempts = self._connection_attempts[ip_address]

            # Remove old attempts outside the time window
            attempts[:] = [t for t in attempts if now - t < window]

            # Check if limit exceeded
            if len(attempts) >= max_per_minute:
                _log.warning(f"Rate limit exceeded for {ip_address}: {len(attempts)} attempts in last {window}s")
                return False

            # Add this attempt
            attempts.append(now)
            return True

    def _close_previous_connection(self, lfdi: str):
        """
        Close any existing connection from the same client (LFDI).

        When a client reconnects, this ensures only one connection per client
        is maintained by gracefully closing the old connection.

        Args:
            lfdi: Client identifier (LFDI or IP-based)
        """
        with self._connection_lock:
            if lfdi in self._connections_by_lfdi:
                old_info = self._connections_by_lfdi[lfdi]
                old_handler = old_info.get("handler")

                if old_handler and old_handler != self:
                    try:
                        _log.info(f"Client {lfdi[:16]}... reconnected, closing previous connection")
                        old_handler.close_connection = True
                        if hasattr(old_handler, 'connection'):
                            old_handler.connection.close()
                    except Exception as e:
                        _log.warning(f"Error closing previous connection for {lfdi[:16]}...: {e}")

                # Clean up backend connection for old connection
                if lfdi in self._backend_pool:
                    try:
                        old_backend = self._backend_pool[lfdi]
                        old_backend.close()
                        del self._backend_pool[lfdi]
                        _log.debug(f"Closed backend connection for replaced client {lfdi[:16]}...")
                    except Exception as e:
                        _log.warning(f"Error closing backend connection: {e}")

    def _register_connection(self, lfdi: str):
        """
        Register this connection in the global registry.

        Args:
            lfdi: Client identifier (LFDI or IP-based)
        """
        conn_id = id(self.connection)
        with self._connection_lock:
            self._connections_by_lfdi[lfdi] = {
                "conn_id": conn_id,
                "handler": self,
                "last_activity": time.time(),
                "client_address": self.client_address,
            }
        _log.info(f"Registered connection for client {lfdi[:16]}... from {self.client_address}")

        # Track for GridAPPS-D publishing
        _track_connection(lfdi, self.client_address, connected=True)

    def _update_activity(self, lfdi: str):
        """
        Update last activity timestamp for this client connection.

        Args:
            lfdi: Client identifier (LFDI or IP-based)
        """
        with self._connection_lock:
            if lfdi in self._connections_by_lfdi:
                self._connections_by_lfdi[lfdi]["last_activity"] = time.time()

    def _unregister_connection(self, lfdi: str):
        """
        Remove this connection from registries and clean up resources.

        Args:
            lfdi: Client identifier (LFDI or IP-based)
        """
        with self._connection_lock:
            # Remove from connection registry
            if lfdi in self._connections_by_lfdi:
                del self._connections_by_lfdi[lfdi]
                _log.info(f"Unregistered connection for client {lfdi[:16]}...")

            # Close and remove backend connection
            if lfdi in self._backend_pool:
                try:
                    backend = self._backend_pool[lfdi]
                    backend.close()
                    del self._backend_pool[lfdi]
                    _log.debug(f"Closed backend connection for {lfdi[:16]}...")
                except Exception as e:
                    _log.warning(f"Error closing backend connection: {e}")

        # Track disconnection for GridAPPS-D publishing
        _track_connection(lfdi, self.client_address, connected=False)

    def handle(self):
        """
        Handle multiple requests if keep-alive is enabled.

        Implements HTTP/1.1 persistent connection handling by processing multiple
        requests over a single client connection. This improves performance by
        reducing connection overhead for clients making multiple requests.

        Now includes:
        - Rate limiting check on connection establishment
        - Client identification via LFDI extraction
        - Single connection per client enforcement
        - Activity tracking for monitoring

        The method continues processing requests until:
        - Client requests connection close
        - Connection timeout occurs (timeout=0, so never based on time)
        - An unrecoverable error occurs
        """
        self.close_connection = False
        client_info = f"{self.client_address[0]}:{self.client_address[1]}"
        lfdi = None
        connection_start = time.time()

        try:
            # Check rate limit before accepting connection
            if not self._check_rate_limit():
                _log.warning(f"Rejecting connection from {client_info} due to rate limit")
                # Send 429 Too Many Requests
                self.send_error(429, "Too Many Requests - Rate limit exceeded")
                return

            # Extract client identifier (LFDI from certificate or IP-based)
            lfdi = self._extract_client_lfdi()
            if not lfdi:
                _log.error(f"Could not determine client identifier for {client_info}")
                return

            _log.info(f"Client {lfdi[:16]}... connected from {client_info}")

            # Close any previous connection from this client
            self._close_previous_connection(lfdi)

            # Register this connection
            self._register_connection(lfdi)

            # Process requests until the connection should be closed
            request_count = 0
            while not self.close_connection:
                request_count += 1
                _log.debug(f"Handling request #{request_count} for client {lfdi[:16]}... ({client_info})")

                # Update activity before processing request
                self._update_activity(lfdi)

                if not self.handle_one_request():
                    break

                # Update activity after processing request
                self._update_activity(lfdi)

                # Never limit number of requests per connection
                # Connections persist indefinitely regardless of request count

        except Exception as e:
            _log.error(f"Error in persistent connection handler for {client_info}: {e}", exc_info=True)
            self.close_connection = True
        finally:
            connection_duration = time.time() - connection_start
            if lfdi:
                _log.info(f"Closing connection for client {lfdi[:16]}... from {client_info} after {connection_duration:.1f}s and {request_count} requests")
                # Unregister and clean up
                self._unregister_connection(lfdi)
            else:
                _log.debug(f"Closing connection for {client_info} after {request_count} requests")

    def handle_one_request(self):
        """
        Handle a single HTTP request with proper keep-alive support.

        Processes one HTTP request from the client, determining whether to keep
        the connection open for additional requests based on HTTP version and
        Connection header values.

        Returns:
            bool: True if the request was handled successfully and connection
                 should remain open, False if connection should be closed

        The method handles various error conditions gracefully:
        - Socket timeouts from slow clients
        - Client disconnections
        - Invalid request encoding
        - Unsupported HTTP methods
        """
        try:
            # Read the request line with timeout
            self.raw_requestline = self.rfile.readline(65537)
            if not self.raw_requestline:
                self.close_connection = True
                return False

            # Parse the request
            if not self.parse_request():
                self.close_connection = True
                return False

            # Check if client wants to close connection
            connection_header = self.headers.get("Connection", "").lower()
            if "close" in connection_header:
                self.close_connection = True
                _log.debug(f"Client {self.client_address} requested connection close for {self.path}")

            # Handle the request
            mname = "do_" + self.command
            if not hasattr(self, mname):
                self.send_error(501, f"Unsupported method ({self.command})")
                return False

            method = getattr(self, mname)
            method()
            self.wfile.flush()

            return True

        except TimeoutError:
            _log.debug(f"Socket timeout on client connection from {self.client_address}")
            self.close_connection = True
            return False
        except (ConnectionResetError, BrokenPipeError) as e:
            _log.debug(f"Client {self.client_address} disconnected: {e}")
            self.close_connection = True
            return False
        except UnicodeDecodeError as e:
            _log.warning(f"Invalid request from {self.client_address}: {e}")
            try:
                self.send_error(400, "Bad Request: Invalid encoding")
            except Exception:
                pass  # If we can't send error, just close
            self.close_connection = True
            return False
        except Exception as e:
            # Only catch-all here because we MUST return a boolean to the caller
            # and we're at the HTTP protocol boundary
            _log.error(f"Unexpected error handling request from {self.client_address}: {e}", exc_info=True)
            try:
                self.send_error(500, "Internal Server Error")
            except Exception:
                pass  # If we can't send error, just close
            self.close_connection = True
            return False

    def _extract_client_certificate_cn(self) -> str | None:
        """
        Extract the Common Name from the client certificate, if available.

        Attempts to retrieve and parse the client's X.509 certificate from the
        TLS connection to extract the Common Name (CN) field from the certificate
        subject. This CN is typically used to identify the client device.

        Returns:
            str | None: The client certificate's Common Name if available and
                       parseable, None if no certificate was provided or if
                       parsing failed

        The method handles various error conditions gracefully:
        - No client certificate provided
        - Certificate parsing errors
        - SSL errors during certificate access
        """
        try:
            x509_binary = self.connection.getpeercert(True)
            if not x509_binary:
                _log.debug("Client did not provide a certificate")
                return None

            _log.debug("Client provided a certificate in binary format")

            try:
                x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_ASN1, x509_binary)
                client_cn = x509.get_subject().CN
                _log.debug(f"Extracted client certificate CN: {client_cn}")
                return client_cn

            except OpenSSL.crypto.Error as e:
                _log.warning(f"Failed to parse client certificate: {e}")
                return None

        except ssl.SSLError as e:
            _log.warning(f"SSL error accessing client certificate: {e}")
            return None
        except Exception as e:
            _log.warning(f"Error accessing client certificate: {e}")
            return None

    def _find_certificate_pair(self, client_cn: str) -> tuple[str | None, str | None]:
        """
        Find certificate pair for the given client CN.

        Searches the TLS repository for a certificate and private key pair
        matching the provided client Common Name. This allows the proxy to
        use client-specific certificates when connecting to the backend server.

        Args:
            client_cn (str): The Common Name from the client certificate

        Returns:
            tuple[str | None, str | None]: A tuple of (cert_file_path, key_file_path)
                                          Both will be None if the certificate pair
                                          is not found or an error occurs
        """
        try:
            cert_file, key_file = self.server.tls_repo.get_file_pair(client_cn)
            _log.debug(f"Found cert file for CN {client_cn}: {cert_file}, key file: {key_file}")
            return str(cert_file), str(key_file)

        except FileNotFoundError as e:
            _log.warning(f"Certificate pair not found for CN {client_cn}: {e}")
            return None, None
        except Exception as e:
            _log.warning(f"Failed to get certificate pair for CN {client_cn}: {e}")
            return None, None

    def _get_default_certificate_pair(self) -> tuple[str, str]:
        """
        Get the default server certificate pair.

        Retrieves the default server certificate and private key file paths
        from the TLS repository. This is used as a fallback when no client-specific
        certificate is available or when client certificate extraction fails.

        Returns:
            tuple[str, str]: A tuple of (cert_file_path, key_file_path) for the
                           default server certificate

        Raises:
            RuntimeError: If the TLS repository is not properly configured or
                         if the default certificate files cannot be accessed
        """
        try:
            cert_file = self.server.tls_repo.server_cert_file
            key_file = self.server.tls_repo.server_key_file
            _log.debug(f"Using default cert: {cert_file}, key: {key_file}")
            return str(cert_file), str(key_file)

        except AttributeError as e:
            _log.error(f"TLS repository not properly configured: {e}")
            raise RuntimeError("TLS repository not available") from e
        except Exception as e:
            _log.error(f"Failed to get default certificate: {e}")
            raise RuntimeError("No valid certificate found for server connection") from e

    def get_context_cert_pair(self) -> ContextWithPaths:
        """
        Dynamically establish SSL/TLS context based on the client's certificate.

        Creates an SSL context for connecting to the backend server, using either
        a client-specific certificate (if available) or falling back to the default
        server certificate. This enables certificate-based authentication where
        the proxy presents appropriate credentials to the backend server.

        The method follows this logic:
        1. Extract client certificate CN from the TLS connection
        2. Search for client-specific certificate pair in repository
        3. Fall back to default server certificate if needed
        4. Create and configure SSL context with chosen certificate

        Returns:
            ContextWithPaths: SSL context with associated certificate file paths

        Raises:
            RuntimeError: If SSL context creation fails or server is misconfigured
            FileNotFoundError: If required certificate files are missing

        The SSL context is configured for client mode (connecting to server)
        with verification disabled for test environments and permissive
        cipher suites for compatibility.
        """
        _log.debug("Getting SSL context and certificate pair for client connection")

        # Ensure we have access to the TLS repository
        if not hasattr(self.server, "tls_repo"):
            raise RuntimeError("Server does not have tls_repo attribute")

        # Initialize with default certificate paths
        cert_file = None
        key_file = None
        client_cn = None

        # Try to get client certificate
        client_cn = self._extract_client_certificate_cn()

        # Try to find certificate pair for the client
        if client_cn:
            cert_file, key_file = self._find_certificate_pair(client_cn)

        # Fall back to default certificate if needed
        if not cert_file or not key_file:
            _log.debug("Using default certificate")
            cert_file, key_file = self._get_default_certificate_pair()

        # Create the SSL context
        try:
            # Use TLS_CLIENT since we're acting as a client to the target server
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            _log.debug("Created SSL context with PROTOCOL_TLS_CLIENT")

            # Don't verify server certificate - typically needed for test environments
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            _log.debug("Set SSL verification: check_hostname=False, verify_mode=CERT_NONE")

            # Load CA file if available
            ca_file = str(Path(cert_file).parent.joinpath("ca.crt"))
            if Path(ca_file).exists():
                context.load_verify_locations(cafile=ca_file)
                _log.debug(f"Loaded CA file: {ca_file}")
            else:
                _log.debug(f"CA file not found at {ca_file}, skipping CA loading")

            # Load client certificate for outgoing connection
            if Path(cert_file).exists() and Path(key_file).exists():
                context.load_cert_chain(certfile=cert_file, keyfile=key_file)
                _log.debug(f"Loaded certificate chain: cert={cert_file}, key={key_file}")
            else:
                _log.error(f"Certificate or key file missing: cert={cert_file}, key={key_file}")
                raise FileNotFoundError(f"Certificate file {cert_file} or key file {key_file} not found")

            # Explicitly set cipher suites to be more permissive for compatibility
            context.set_ciphers("ALL:@SECLEVEL=1")
            _log.debug("Set cipher suite: ALL:@SECLEVEL=1")

            return ContextWithPaths(context=context, certpath=cert_file, keypath=key_file)

        except ssl.SSLError as e:
            _log.error(f"SSL configuration error: {e}")
            raise RuntimeError(f"Failed to configure SSL context: {e}") from e
        except FileNotFoundError:
            # Let this bubble up - caller should handle missing certificates
            raise
        except Exception as e:
            _log.error(f"Unexpected error creating SSL context: {e}")
            raise RuntimeError(f"Failed to create SSL context: {e}") from e

    def __create_server_connection__(self) -> HTTPSConnectionWithTimeout:
        """
        Gets or creates a backend connection to the server with connection pooling.

        NEW BEHAVIOR: Maintains one persistent backend connection per client (LFDI).
        This significantly reduces overhead by eliminating repeated TLS handshakes.

        Connection Pool Strategy:
        - First request from client: Create and cache backend connection
        - Subsequent requests: Reuse cached connection
        - Connection health check before reuse
        - Automatic reconnection if connection is broken
        - Cleanup when client disconnects

        Returns:
            HTTPSConnectionWithTimeout: An established connection to the backend server

        Raises:
            RuntimeError: If SSL context creation fails or all connection attempts fail
        """
        # DISABLED: Backend connection pooling causes lockups with Flask's dev server
        # Flask/Werkzeug doesn't properly handle HTTP keep-alive, and reusing connections
        # causes requests to hang when the server has closed its end of the connection.
        # Always create a fresh connection for each request.
        _log.debug("Creating new backend connection (pooling disabled)")
        return self.__create_new_backend_connection__()

    def __create_new_backend_connection__(self) -> HTTPSConnectionWithTimeout:
        """
        Creates a new backend connection (internal method for connection pooling).

        This method handles the actual connection creation with retry logic.
        Called by __create_server_connection__() when no cached connection exists.

        Returns:
            HTTPSConnectionWithTimeout: An established connection to the backend server

        Raises:
            RuntimeError: If SSL context creation fails or all connection attempts fail
        """
        max_retries = 2  # Reduced retries for faster response under load
        retry_delay = 0.5  # Shorter delay for better responsiveness
        host, port = self.server.proxy_target
        client_info = f"{self.client_address[0]}:{self.client_address[1]}"
        _log.debug(f"Creating new backend connection to {host}:{port} for client {client_info}")

        # Get SSL context once to avoid repeated expensive operations
        try:
            ccp = self.get_context_cert_pair()
            _log.debug(f"Got SSL context with cert: {os.path.basename(ccp.certpath)} for client {client_info}")
        except Exception as e:
            _log.error(f"Failed to get SSL context for client {client_info}: {e}")
            raise RuntimeError(f"Failed to get SSL context: {e}") from e

        for attempt in range(max_retries):
            try:
                _log.debug(f"Connection attempt {attempt + 1}/{max_retries} to {host}:{port} for client {client_info}")

                # Create connection with reasonable timeouts
                conn = HTTPSConnectionWithTimeout(
                    host=host,
                    port=port,
                    context=ccp.context,
                    timeout_connect=30,  # Keep reasonable connect timeout for initial connection
                    timeout_read=0,  # No read timeout - never disconnect active backend connections
                )

                _log.debug(f"Establishing connection for client {client_info}...")
                conn.connect()
                _log.debug(f"Created server connection on attempt {attempt + 1} for client {client_info}")
                return conn

            except (TimeoutError, ssl.SSLError) as e:
                _log.warning(f"Connection attempt {attempt + 1} failed for client {client_info}: {e}")
                if attempt < max_retries - 1:
                    _log.debug(f"Retrying in {retry_delay}s for client {client_info}...")
                    time.sleep(retry_delay)
                else:
                    _log.error(f"All {max_retries} connection attempts failed for client {client_info}")
                    raise RuntimeError(
                        f"Failed to establish server connection after {max_retries} attempts: {e}"
                    ) from e
            except Exception as e:
                _log.error(f"Unexpected error creating connection for client {client_info}: {e}")
                raise RuntimeError(f"Unexpected error creating server connection: {e}") from e

        # This should never be reached due to the loop structure
        raise RuntimeError("Failed to create server connection: unknown error")

    def __handle_response__(self, conn: HTTPSConnectionWithTimeout):
        """
        Handle the response with proper error handling.
        """
        client_info = f"{self.client_address[0]}:{self.client_address[1]}"
        _log.debug(f"Handling response from {self.command} {self.path}")
        try:
            _log.debug("Getting response from server")
            response = conn.getresponse()
            _log.debug(f"Got response: {response.status} {response.reason}")

            # Read response data with timeout handling
            try:
                _log.debug("Reading response data")
                data = response.read()
                _log.debug(f"Response size: {len(data)} bytes")
            except TimeoutError:
                _log.error("Timeout reading response data from server")
                try:
                    self.send_error(504, "Gateway Timeout")
                except Exception:
                    self.close_connection = True
                return None

            # COMPREHENSIVE RESPONSE LOGGING - Log all response data from backend
            _log.info(f"=== RESPONSE FROM BACKEND FOR CLIENT {client_info} ===")
            _log.info(f"Status: {response.status} {response.reason}")
            _log.info("Response Headers from backend:")
            for header_name, header_value in response.headers.items():
                _log.info(f"  {header_name}: {header_value}")

            if data:
                _log.info(f"Response Body from backend ({len(data)} bytes):")
                try:
                    # Try to decode as UTF-8 for text content
                    response_text = data.decode("utf-8")
                    _log.info(f"  {response_text}")
                except UnicodeDecodeError:
                    # Log as hex for binary content
                    _log.info(f"  [Binary content: {data.hex()}]")
            else:
                _log.info("Response Body: [None]")

            # Log successful response
            _log.info(f"{self.command} {self.path} {response.status} {response.reason}")

            # Send status line
            _log.debug(f"Sending status line: {response.status} {response.reason}")
            self.send_response(response.status, response.reason)

            # Send headers, filtering out problematic ones
            skip_headers = {"connection", "transfer-encoding", "content-length"}

            # Log what headers we're sending back to client
            _log.info(f"=== RESPONSE TO CLIENT {client_info} ===")
            _log.info(f"Status: {response.status} {response.reason}")
            _log.info("Headers being sent to client:")

            for k, v in response.headers.items():
                if k.lower() not in skip_headers:
                    _log.debug(f"Forwarding header: {k}: {v}")
                    _log.info(f"  {k}: {v}")
                    self.send_header(k, v)
                else:
                    _log.debug(f"Skipping header: {k}: {v}")

            # Set content length
            _log.debug(f"Setting Content-Length: {len(data)}")
            _log.info(f"  Content-Length: {len(data)}")
            self.send_header("Content-Length", str(len(data)))

            # Handle client connection based on request headers
            client_connection = self.headers.get("Connection", "").lower()
            if self.request_version >= "HTTP/1.1":
                # HTTP/1.1 defaults to keep-alive unless client requests close
                if "close" not in client_connection:
                    self.send_header("Connection", "keep-alive")
                    self.send_header("Keep-Alive", "timeout=86400, max=0")  # 24 hours, unlimited requests
                    _log.info("  Connection: keep-alive")
                    _log.info("  Keep-Alive: timeout=86400, max=0")
                    _log.debug("Maintaining keep-alive connection with client indefinitely")
                else:
                    self.send_header("Connection", "close")
                    _log.info("  Connection: close")
                    _log.debug("Client requested connection close")
            elif "keep-alive" in client_connection:
                # HTTP/1.0 with explicit keep-alive
                self.send_header("Connection", "keep-alive")
                self.send_header("Keep-Alive", "timeout=86400, max=0")  # 24 hours, unlimited requests
                _log.info("  Connection: keep-alive")
                _log.info("  Keep-Alive: timeout=86400, max=0")
                _log.debug("HTTP/1.0 client requested keep-alive - honoring indefinitely")
            else:
                # HTTP/1.0 default or explicit close
                self.send_header("Connection", "close")
                _log.info("  Connection: close")
                _log.debug("Using connection close for HTTP/1.0 client")

            self.end_headers()

            # Log response body being sent to client
            if data:
                _log.info(f"Response Body to client ({len(data)} bytes):")
                try:
                    response_text = data.decode("utf-8")
                    _log.info(f"  {response_text}")
                except UnicodeDecodeError:
                    _log.info(f"  [Binary content: {data.hex()}]")
            else:
                _log.info("Response Body to client: [None]")

            # Send response body
            if data:
                _log.debug(f"Writing {len(data)} bytes to client")
                try:
                    self.wfile.write(data)
                    _log.debug("Response data written successfully")
                    _log.info(f"=== TRANSACTION COMPLETED FOR CLIENT {client_info} ===")
                except (BrokenPipeError, ConnectionResetError) as e:
                    _log.error(f"Client disconnected while writing response: {e}")
                    # Client disconnected, close the connection
                    self.close_connection = True
                    return None

            return response

        except (TimeoutError, ssl.SSLError) as e:
            _log.error(f"Network error handling response from server: {e}")
            try:
                self.send_error(502, "Bad Gateway: Server Error")
            except Exception as ex:
                _log.error(f"Failed to send error response: {ex}")
                self.close_connection = True
            return None

        except (BrokenPipeError, ConnectionResetError) as e:
            _log.debug(f"Client disconnected during response handling: {e}")
            self.close_connection = True
            return None

        except Exception as e:
            # Only catch-all here because we're at the HTTP response boundary
            # and need to provide some response to the client
            _log.error(f"Unexpected error handling response: {e}", exc_info=True)
            try:
                self.send_error(502, "Bad Gateway: Response Error")
            except Exception as ex:
                _log.error(f"Failed to send error response: {ex}")
                self.close_connection = True
            return None

        finally:
            # Close backend connection after each request since connection pooling is disabled
            # This ensures clean state for each request and works around Flask/Werkzeug's
            # poor HTTP keep-alive support
            try:
                if conn and hasattr(conn, 'close'):
                    conn.close()
                    _log.debug("Backend connection closed after request")
            except Exception as e:
                _log.debug(f"Error closing backend connection: {e}")

    def _read_request_body(self) -> bytes:
        """
        Read request body based on Content-Length header.

        Reads the HTTP request body from the client connection, using the
        Content-Length header to determine how many bytes to read. This is
        essential for HTTP methods like POST and PUT that include request bodies.

        Returns:
            bytes: The request body data, or empty bytes if no body is present

        The method safely handles:
        - Missing Content-Length headers (treats as no body)
        - Zero-length bodies
        - Large request bodies (limited by available memory)
        """
        content_length = int(self.headers.get("Content-Length", 0))
        _log.debug(f"Reading request body, Content-Length: {content_length}")

        if content_length > 0:
            body = self.rfile.read(content_length)
            _log.debug(f"Read {len(body)} bytes from request body")
            return body
        return b""

    def _forward_request(self, method: str) -> None:
        """
        Common method to forward requests of any type.

        Handles the complete request forwarding process including:
        - Creating backend server connection
        - Reading request body for applicable methods
        - Processing and filtering headers
        - Adding client certificate information as headers
        - Forwarding request to backend server
        - Handling response and sending to client

        Args:
            method (str): HTTP method (GET, POST, PUT, DELETE, etc.)

        The method implements the core proxy functionality:
        1. Establishes connection to backend server
        2. Extracts client certificate and adds as HTTP headers
        3. Forwards the request with proper header filtering
        4. Handles the response and forwards back to client
        5. Ensures proper connection cleanup

        Client certificate information is added as HTTP headers in Nginx style:
        - SSL-Client-Cert: PEM-encoded certificate
        - SSL-Client-S-DN: Subject Distinguished Name
        - SSL-Client-I-DN: Issuer Distinguished Name
        - SSL-Client-Serial: Certificate serial number
        - SSL-Client-Fingerprint: SHA256 fingerprint
        """
        client_info = f"{self.client_address[0]}:{self.client_address[1]}"
        _log.info(f"Forwarding {method} {self.path} for client {client_info}")

        # COMPREHENSIVE REQUEST LOGGING - Log all incoming request data
        _log.info(f"=== INCOMING REQUEST FROM CLIENT {client_info} ===")
        _log.info(f"Method: {method}")
        _log.info(f"Path: {self.path}")
        _log.info(f"HTTP Version: {self.request_version}")
        _log.info("Request Headers:")
        for header_name, header_value in self.headers.items():
            _log.info(f"  {header_name}: {header_value}")

        conn = None

        try:
            # Create a new connection to the server for each request
            _log.debug(f"Creating server connection for {method} {self.path} from client {client_info}")
            conn = self.__create_server_connection__()

            # Read request body for methods that may have one
            body = None
            if method in ("POST", "PUT", "PATCH", "DELETE"):
                _log.debug(f"Reading body for {method} request from client {client_info}")
                body = self._read_request_body()
                _log.debug(f"Request body size: {len(body) if body else 0} bytes for client {client_info}")

                # Log request body content
                if body:
                    _log.info(f"Request Body ({len(body)} bytes):")
                    try:
                        # Try to decode as UTF-8 for text content
                        body_text = body.decode("utf-8")
                        _log.info(f"  {body_text}")
                    except UnicodeDecodeError:
                        # Log as hex for binary content
                        _log.info(f"  [Binary content: {body.hex()}]")
                else:
                    _log.info("Request Body: [None]")

            # Copy headers but skip hop-by-hop headers
            _log.debug(f"Processing request headers for client {client_info}")
            headers = {
                k: v
                for k, v in self.headers.items()
                if k.lower() not in ("connection", "keep-alive", "transfer-encoding")
            }

            # Set the host header to the target host
            host, port = self.server.proxy_target
            headers["Host"] = f"{host}:{port}"
            _log.debug(f"Set Host header to {host}:{port} for client {client_info}")

            # Add client certificate information as headers (similar to Nginx)
            try:
                x509_binary = self.connection.getpeercert(True)
                if x509_binary:
                    x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_ASN1, x509_binary)

                    # Convert to PEM format for header
                    cert_pem = OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, x509).decode("ascii")

                    # Get certificate fingerprint for LFDI calculation
                    fingerprint = x509.digest("sha256").decode("ascii")
                    cert_common_name = x509.get_subject().CN

                    # Calculate LFDI and SFDI from certificate fingerprint
                    try:
                        # Use configuration to determine LFDI calculation method
                        client_lfdi = None
                        client_sfdi = None
                        cert_common_name = x509.get_subject().CN

                        if self.server.config.lfdi_mode == "lfdi_mode_from_file":
                            # Use combined file method based on configuration
                            try:
                                # Use TLSRepository to calculate LFDI from file (like the server does)
                                client_lfdi = self.server.tls_repo.lfdi(cert_common_name)
                                client_sfdi = self.server.tls_repo.sfdi(cert_common_name)

                                # Get the file fingerprint for logging
                                file_fingerprint = self.server.tls_repo.fingerprint(
                                    cert_common_name, without_colan=False
                                )

                                _log.info("=== CLIENT CERTIFICATE IDENTIFIERS (FILE-BASED METHOD) ===")
                                _log.info(f"Client {client_info}:")
                                _log.info(f"  Certificate CN: {cert_common_name}")
                                _log.info(f"  LFDI mode: {self.server.config.lfdi_mode}")
                                _log.info(f"  File fingerprint: {file_fingerprint}")
                                _log.info(f"  Connection fingerprint: {fingerprint}")
                                _log.info(f"  LFDI (from file): {client_lfdi}")
                                _log.info(f"  SFDI (from file): {client_sfdi}")

                            except Exception as file_error:
                                _log.warning(f"Error calculating LFDI from file for {cert_common_name}: {file_error}")
                                _log.info("Falling back to connection certificate method")
                                # Fall back to connection method
                                client_lfdi = lfdi_from_fingerprint(fingerprint)
                                client_sfdi = sfdi_from_lfdi(client_lfdi)

                                _log.info("=== CLIENT CERTIFICATE IDENTIFIERS (FALLBACK CONNECTION METHOD) ===")
                                _log.info(f"Client {client_info}:")
                                _log.info(f"  Certificate CN: {cert_common_name}")
                                _log.info(f"  LFDI mode: {self.server.config.lfdi_mode} (failed, using fallback)")
                                _log.info(f"  LFDI (from connection): {client_lfdi}")
                                _log.info(f"  SFDI (from connection): {client_sfdi}")
                                _log.info(f"  Fingerprint: {fingerprint}")

                        else:  # lfdi_mode_from_cert_fingerprint
                            # Use connection certificate method
                            client_lfdi = lfdi_from_fingerprint(fingerprint)
                            client_sfdi = sfdi_from_lfdi(client_lfdi)

                            _log.info("=== CLIENT CERTIFICATE IDENTIFIERS (CERTIFICATE-BASED METHOD) ===")
                            _log.info(f"Client {client_info}:")
                            _log.info(f"  Certificate CN: {cert_common_name}")
                            _log.info(f"  LFDI mode: {self.server.config.lfdi_mode}")
                            _log.info(f"  LFDI (from connection): {client_lfdi}")
                            _log.info(f"  SFDI (from connection): {client_sfdi}")
                            _log.info(f"  Fingerprint: {fingerprint}")

                        # Add LFDI and SFDI as custom headers
                        headers["SSL-Client-LFDI"] = str(client_lfdi)
                        headers["SSL-Client-SFDI"] = str(client_sfdi)

                    except Exception as lfdi_error:
                        _log.warning(f"Could not calculate LFDI/SFDI for client {client_info}: {lfdi_error}")

                    # Add client certificate headers (Nginx-style)
                    headers["SSL-Client-Cert"] = cert_pem.replace("\n", " ")
                    headers["SSL-Client-S-DN"] = str(x509.get_subject())
                    headers["SSL-Client-I-DN"] = str(x509.get_issuer())
                    headers["SSL-Client-Serial"] = str(x509.get_serial_number())
                    headers["SSL-Client-Fingerprint"] = fingerprint

                    _log.debug(
                        f"Added client certificate headers for CN: {x509.get_subject().CN} from client {client_info}"
                    )
                else:
                    _log.debug(f"No client certificate provided by client {client_info}")
            except OpenSSL.crypto.Error as e:
                _log.warning(f"Could not parse client certificate for client {client_info}: {e}")
            except Exception as e:
                _log.warning(f"Could not extract client certificate info for client {client_info}: {e}")

            # Use Connection: keep-alive for backend to enable connection pooling and reuse
            # This allows us to maintain persistent backend connections per client
            headers["Connection"] = "keep-alive"

            _log.info(f"Forwarding {method} {self.path} to {host}:{port} for client {client_info}")
            if "SSL-Client-Cert" in headers:
                if "SSL-Client-LFDI" in headers:
                    _log.debug(
                        f"Forwarding client certificate for CN: {headers.get('SSL-Client-S-DN', 'unknown')} (LFDI: {headers['SSL-Client-LFDI']}, SFDI: {headers['SSL-Client-SFDI']}) from client {client_info}"
                    )
                else:
                    _log.debug(
                        f"Forwarding client certificate for CN: {headers.get('SSL-Client-S-DN', 'unknown')} from client {client_info}"
                    )

            # COMPREHENSIVE OUTGOING REQUEST LOGGING - Log all data being sent to backend
            _log.info(f"=== OUTGOING REQUEST TO BACKEND {host}:{port} ===")
            _log.info(f"Method: {method}")
            _log.info(f"Path: {self.path}")
            _log.info("Headers being sent to backend:")
            for header_name, header_value in headers.items():
                # Truncate SSL-Client-Cert for readability, highlight LFDI/SFDI
                if header_name == "SSL-Client-Cert":
                    _log.info(f"  {header_name}: [Client certificate - {len(header_value)} chars]")
                elif header_name in ("SSL-Client-LFDI", "SSL-Client-SFDI"):
                    _log.info(f"  {header_name}: {header_value} *** IEEE 2030.5 IDENTIFIER ***")
                else:
                    _log.info(f"  {header_name}: {header_value}")

            if body:
                _log.info(f"Body being sent to backend ({len(body)} bytes):")
                try:
                    body_text = body.decode("utf-8")
                    _log.info(f"  {body_text}")
                except UnicodeDecodeError:
                    _log.info(f"  [Binary content: {body.hex()}]")
            else:
                _log.info("Body: [None]")

            # Forward the request to the target server
            try:
                _log.debug(f"Sending {method} request to server: {self.path} for client {client_info}")
                conn.request(method=method, url=self.path, headers=headers, body=body)
                _log.debug(f"Request sent successfully for client {client_info}")
            except (TimeoutError, ssl.SSLError, BrokenPipeError, ConnectionResetError) as e:
                _log.error(f"Network error sending request to server for client {client_info}: {e}")
                try:
                    self.send_error(502, f"Bad Gateway: {str(e)}")
                except Exception:
                    # If we can't send error, close client connection
                    self.close_connection = True
                return

            # Handle the response - this will close the server connection
            _log.debug(f"Getting response from server for client {client_info}")
            response = self.__handle_response__(conn)
            conn = None  # Connection is now closed

            if not response:
                _log.error(f"{method} {self.path} -> Failed to get response for client {client_info}")

        except RuntimeError as e:
            # These are from our own methods (SSL context creation, connection creation)
            _log.error(f"Configuration error forwarding {method} request for client {client_info}: {e}")
            try:
                self.send_error(502, "Bad Gateway: Configuration Error")
            except Exception:
                self.close_connection = True

        except Exception as e:
            # Only catch-all here because we're at the HTTP request boundary
            # and must provide some response to the client
            _log.error(f"Unexpected error forwarding {method} request for client {client_info}: {e}", exc_info=True)
            try:
                self.send_error(502, "Bad Gateway: Internal Error")
            except Exception as ex:
                _log.error(f"Failed to send error response to client {client_info}: {ex}")
                # If we can't send error response, close the client connection
                self.close_connection = True

        finally:
            # Close backend connection after each request since connection pooling is disabled
            if conn:
                try:
                    conn.close()
                    _log.debug(f"Backend connection closed after request for client {client_info}")
                except Exception as e:
                    _log.debug(f"Error closing backend connection for client {client_info}: {e}")

    def do_GET(self):
        """Handle HTTP GET requests by forwarding to backend server."""
        import time

        start_time = time.time()
        client_info = f"{self.client_address[0]}:{self.client_address[1]}"
        _log.info(f"=== NEW GET REQUEST FROM CLIENT {client_info} ===")
        _log.debug(f"Received GET request for {self.path}")
        self._forward_request("GET")
        end_time = time.time()
        _log.info(f"GET request completed in {end_time - start_time:.3f} seconds")

    def do_HEAD(self):
        """Handle HTTP HEAD requests by forwarding to backend server."""
        import time

        start_time = time.time()
        client_info = f"{self.client_address[0]}:{self.client_address[1]}"
        _log.info(f"=== NEW HEAD REQUEST FROM CLIENT {client_info} ===")
        _log.debug(f"Received HEAD request for {self.path}")
        self._forward_request("HEAD")
        end_time = time.time()
        _log.info(f"HEAD request completed in {end_time - start_time:.3f} seconds")

    def do_POST(self):
        """Handle HTTP POST requests by forwarding to backend server."""
        import time

        start_time = time.time()
        client_info = f"{self.client_address[0]}:{self.client_address[1]}"
        _log.info(f"=== NEW POST REQUEST FROM CLIENT {client_info} ===")
        _log.debug(f"Received POST request for {self.path}")
        self._forward_request("POST")
        end_time = time.time()
        _log.info(f"POST request completed in {end_time - start_time:.3f} seconds")

    def do_PUT(self):
        """Handle HTTP PUT requests by forwarding to backend server."""
        import time

        start_time = time.time()
        client_info = f"{self.client_address[0]}:{self.client_address[1]}"
        _log.info(f"=== NEW PUT REQUEST FROM CLIENT {client_info} ===")
        _log.debug(f"Received PUT request for {self.path}")
        self._forward_request("PUT")
        end_time = time.time()
        _log.info(f"PUT request completed in {end_time - start_time:.3f} seconds")

    def do_DELETE(self):
        """Handle HTTP DELETE requests by forwarding to backend server."""
        import time

        start_time = time.time()
        client_info = f"{self.client_address[0]}:{self.client_address[1]}"
        _log.info(f"=== NEW DELETE REQUEST FROM CLIENT {client_info} ===")
        _log.debug(f"Received DELETE request for {self.path}")
        self._forward_request("DELETE")
        end_time = time.time()
        _log.info(f"DELETE request completed in {end_time - start_time:.3f} seconds")

    def do_OPTIONS(self):
        """Handle HTTP OPTIONS requests by forwarding to backend server."""
        import time

        start_time = time.time()
        client_info = f"{self.client_address[0]}:{self.client_address[1]}"
        _log.info(f"=== NEW OPTIONS REQUEST FROM CLIENT {client_info} ===")
        _log.debug(f"Received OPTIONS request for {self.path}")
        self._forward_request("OPTIONS")
        end_time = time.time()
        _log.info(f"OPTIONS request completed in {end_time - start_time:.3f} seconds")

    def do_PATCH(self):
        """Handle HTTP PATCH requests by forwarding to backend server."""
        import time

        start_time = time.time()
        client_info = f"{self.client_address[0]}:{self.client_address[1]}"
        _log.info(f"=== NEW PATCH REQUEST FROM CLIENT {client_info} ===")
        _log.debug(f"Received PATCH request for {self.path}")
        self._forward_request("PATCH")
        end_time = time.time()
        _log.info(f"PATCH request completed in {end_time - start_time:.3f} seconds")

    def log_request(self, code="-", size="-"):
        """
        Custom request logging with appropriate log levels.

        Args:
            code: HTTP response code (string or integer)
            size: Response size (string or integer)
        """
        if isinstance(code, str) or code < 400:
            _log.info(f"{self.command} {self.path} {code} {size}")
        else:
            _log.warning(f"{self.command} {self.path} {code} {size}")

    def log_error(self, format, *args):
        """Override to use our logger instead of stderr."""
        _log.error(format % args)

    def log_message(self, format, *args):
        """Override to use our logger instead of stderr."""
        _log.info(format % args)


class ProxyServer(ThreadingHTTPServer):
    """
    Multi-threaded proxy server that can handle multiple clients simultaneously.

    Extends ThreadingHTTPServer to provide concurrent client support for IEEE 2030.5
    proxy operations. Each client connection is handled in a separate thread, enabling
    multiple devices to communicate through the proxy simultaneously without blocking.

    Key Features:
    - Thread-per-client architecture for true concurrency
    - TCP keep-alive for improved connection performance
    - Configurable request queue for handling connection bursts
    - Proper resource cleanup with daemon threads
    - Socket reuse for quick restart capability

    Attributes:
        allow_reuse_address (bool): Enable SO_REUSEADDR for quick restart
        daemon_threads (bool): Don't wait for threads on shutdown
        request_queue_size (int): Maximum pending connections (50)

    The server maintains references to:
    - tls_repo: TLS repository for certificate management
    - proxy_target: Backend server address tuple (host, port)
    """

    # Allow connection reuse and set reasonable limits
    allow_reuse_address = True
    daemon_threads = True  # Don't wait for threads to finish on shutdown

    def __init__(self, tls_repo: TLSRepository, proxy_target: tuple[str, int], config: ServerConfiguration, **kwargs):
        """
        Initialize the proxy server with TLS repository and target configuration.

        Args:
            tls_repo (TLSRepository): Certificate repository for SSL operations
            proxy_target (Tuple[str, int]): Backend server (host, port) tuple
            config (ServerConfiguration): Server configuration including lfdi_mode
            **kwargs: Additional arguments passed to ThreadingHTTPServer
        """
        _log.debug(f"Initializing ProxyServer with target {proxy_target}")
        # Store our custom attributes before calling super().__init__
        self._tls_repo = tls_repo
        self._proxy_target = proxy_target
        self._config = config

        # Call parent constructor
        super().__init__(**kwargs)

        # Set socket options for better concurrent performance
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Enable TCP keep-alive for client connections
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

        # Set a reasonable backlog for incoming connections
        self.request_queue_size = 50

        _log.debug("ProxyServer initialized with concurrent client support")

    @property
    def proxy_target(self) -> tuple[str, int]:
        """Get the backend server target address."""
        return self._proxy_target

    @property
    def tls_repo(self) -> TLSRepository:
        """Get the TLS repository for certificate operations."""
        return self._tls_repo

    @property
    def config(self) -> ServerConfiguration:
        """Get the server configuration."""
        return self._config

    def server_bind(self):
        """
        Override to set additional socket options for optimal performance.

        Configures TCP keep-alive parameters (Linux-specific) to maintain
        long-lived connections and detect dead connections efficiently.
        """
        super().server_bind()

        # Set TCP keep-alive parameters if available (Linux-specific)
        try:
            if hasattr(socket, "TCP_KEEPIDLE"):
                self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60)
            if hasattr(socket, "TCP_KEEPINTVL"):
                self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10)
            if hasattr(socket, "TCP_KEEPCNT"):
                self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 6)
            _log.debug("Set TCP keep-alive parameters for client connections")
        except (AttributeError, OSError) as e:
            _log.debug(f"Could not set TCP keep-alive parameters: {e}")

    def process_request(self, request, client_address):
        """
        Override to add better logging and error handling for concurrent requests.

        Args:
            request: The client socket connection
            client_address: Tuple of (host, port) for the client

        Provides enhanced error handling and logging for debugging issues
        with concurrent client connections in production environments.
        """
        try:
            _log.debug(f"Processing new request from {client_address}")
            super().process_request(request, client_address)
        except Exception as e:
            _log.error(f"Error processing request from {client_address}: {e}")
            try:
                self.handle_error(request, client_address)
            except Exception:
                pass
            try:
                self.shutdown_request(request)
            except Exception:
                pass


def start_proxy(
    server_address: tuple[str, int], tls_repo: TLSRepository, proxy_target: tuple[str, int], config: ServerConfiguration,
    gridappsd_address: str | None = None, gridappsd_port: int = 61613,
    gridappsd_username: str = "system", gridappsd_password: str = "manager"
):
    """
    Start the proxy server with SSL/TLS configuration.

    Creates and starts a multi-threaded proxy server that accepts client connections
    with TLS client certificates and forwards requests to a backend IEEE 2030.5 server.
    The server requires client certificates for authentication and calculates LFDI/SFDI
    based on the configuration's lfdi_mode setting.

    Args:
        server_address (Tuple[str, int]): Address to bind the proxy server (host, port)
        tls_repo (TLSRepository): Certificate repository containing CA, server certs
        proxy_target (Tuple[str, int]): Backend server address (host, port)
        config (ServerConfiguration): Configuration including lfdi_mode setting
        gridappsd_address (str | None): GridAPPS-D STOMP broker address for publishing connection status
        gridappsd_port (int): GridAPPS-D STOMP broker port (default: 61613)
        gridappsd_username (str): GridAPPS-D STOMP username (default: "system")
        gridappsd_password (str): GridAPPS-D STOMP password (default: "manager")

    The function configures:
    - TLS server context requiring client certificates
    - Certificate chain loading for server identity
    - Permissive cipher suites for compatibility
    - LFDI calculation method based on config.lfdi_mode
    - Graceful shutdown handling
    - GridAPPS-D connection status publisher (if gridappsd_address is provided)

    LFDI Calculation Modes:
    - lfdi_mode_from_file: Uses SHA256 of combined certificate file content
    - lfdi_mode_from_cert_fingerprint: Uses certificate's built-in fingerprint

    Server Operation:
    - Binds to the specified address and port
    - Loads server certificates from TLS repository
    - Requires client certificates (CERT_REQUIRED)
    - Runs until KeyboardInterrupt or fatal error
    """
    global _stomp_publisher

    _log.info(f"Serving proxy at {server_address} -> {proxy_target}")
    try:
        _log.debug(f"Creating ProxyServer instance at {server_address}")
        httpd = ProxyServer(
            tls_repo=tls_repo,
            proxy_target=proxy_target,
            server_address=server_address,
            RequestHandlerClass=RequestForwarder,
            config=config,
        )
        _log.debug("ProxyServer instance created successfully")

        # Verify the server has the required attributes
        if hasattr(httpd, "tls_repo"):
            _log.debug(f"Server tls_repo verified: {type(httpd.tls_repo)}")
        else:
            _log.error("Server missing tls_repo attribute after creation")

        if hasattr(httpd, "proxy_target"):
            _log.debug(f"Server proxy_target verified: {httpd.proxy_target}")
        else:
            _log.error("Server missing proxy_target attribute after creation")

    except Exception as e:
        _log.error(f"Error initializing ProxyServer: {e}", exc_info=True)
        raise

    try:
        _log.debug("Creating SSL context for proxy server")
        # Use PROTOCOL_TLS_SERVER instead of deprecated PROTOCOL_TLS
        sslctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

        # Configure SSL to require client certificates
        sslctx.verify_mode = ssl.CERT_REQUIRED  # Require client certificates
        sslctx.check_hostname = False
        _log.debug("SSL context configured with verify_mode=CERT_REQUIRED, check_hostname=False")

        # Load CA and server certificates
        if Path(tls_repo.ca_cert_file).exists():
            _log.debug(f"Loading CA certificate from {tls_repo.ca_cert_file}")
            sslctx.load_verify_locations(cafile=tls_repo.ca_cert_file)
        else:
            _log.warning(f"CA certificate file not found: {tls_repo.ca_cert_file}")

        if Path(tls_repo.server_cert_file).exists() and Path(tls_repo.server_key_file).exists():
            _log.debug(f"Loading server certificate: {tls_repo.server_cert_file}, {tls_repo.server_key_file}")
            sslctx.load_cert_chain(certfile=tls_repo.server_cert_file, keyfile=tls_repo.server_key_file)
        else:
            _log.error(f"Server certificate files not found: {tls_repo.server_cert_file}, {tls_repo.server_key_file}")
            return

        # Set cipher suites to be more permissive
        sslctx.set_ciphers("ALL:@SECLEVEL=1")
        _log.debug("Set cipher suite: ALL:@SECLEVEL=1")

        _log.debug("Wrapping server socket with SSL")
        httpd.socket = sslctx.wrap_socket(httpd.socket, server_side=True)

        # Start GridAPPS-D connection status publisher if configured
        if gridappsd_address:
            _stomp_publisher = GridAPPSDConnectionPublisher(
                gridappsd_address=gridappsd_address,
                gridappsd_port=gridappsd_port,
                username=gridappsd_username,
                password=gridappsd_password
            )
            _stomp_publisher.start()
            _log.info(f"GridAPPS-D connection publisher configured for {gridappsd_address}:{gridappsd_port}")
        else:
            _log.debug("GridAPPS-D connection publishing not configured")

        _log.info("Proxy server started successfully")
        _log.debug("Entering serve_forever() loop")
        httpd.serve_forever()

    except KeyboardInterrupt:
        _log.warning("Proxy server shutting down due to keyboard interrupt...")
    except Exception as e:
        _log.error(f"Proxy server error: {e}", exc_info=True)
    finally:
        # Stop GridAPPS-D publisher
        if _stomp_publisher:
            _stomp_publisher.stop()

        _log.debug("Closing server")
        httpd.server_close()
        _log.info("Proxy server shut down")


def build_address_tuple(hostname: str) -> tuple[str, int]:
    """
    Create a Tuple[str, int] from the passed hostname.

    Parses various hostname formats to extract host and port information,
    providing sensible defaults for IEEE 2030.5 applications.

    Args:
        hostname (str): Hostname in various formats:
                       - "https://server:port" (URL format)
                       - "http://server:port" (URL format)
                       - "server:port" (host:port format)
                       - "server" (host only, defaults to port 443)

    Returns:
        Tuple[str, int]: A tuple of (hostname, port) with guaranteed integer port

    Default Ports:
        - HTTPS URLs without port: 443
        - HTTP URLs without port: 80
        - Plain hostnames without port: 443 (secure default for IEEE 2030.5)

    Examples:
        >>> build_address_tuple("https://example.com:8443")
        ('example.com', 8443)
        >>> build_address_tuple("example.com")
        ('example.com', 443)
        >>> build_address_tuple("http://example.com")
        ('example.com', 80)
    """
    _log.debug(f"Parsing hostname: {hostname}")
    parsed = urlparse(hostname)
    if parsed.hostname:
        port = parsed.port
        if port is None:
            # Default port based on scheme
            port = 443 if parsed.scheme == "https" else 80
        hostname_tuple = (parsed.hostname, port)
        _log.debug(f"Parsed URL format: {hostname_tuple}")
    else:
        parts = hostname.split(":")
        if len(parts) > 1:
            hostname_tuple = (parts[0], int(parts[1]))
        else:
            # Default to port 443 if no port specified
            hostname_tuple = (parts[0], 443)
        _log.debug(f"Parsed host:port format: {hostname_tuple}")
    return hostname_tuple


def _main():
    """
    Main entry point for the IEEE 2030.5 proxy server application.

    Parses command line arguments, loads configuration, initializes the TLS
    repository, and starts the proxy server. This function handles the complete
    application lifecycle including error handling and graceful shutdown.

    Command Line Arguments:
        config: Path to YAML configuration file (required)
        --debug: Enable debug logging (optional)
        --syslog: Enable syslog logging in addition to console (optional)
        --syslog-facility: Syslog facility to use (default: local0)

    Configuration File Format:
        The YAML config file must contain:
        - proxy_hostname: Address for proxy to bind to
        - server_hostname: Backend server address
        - tls_repository: Path to certificate directory
        - openssl_cnf: Path to OpenSSL configuration template

    Returns:
        int: Exit code (0 for success, 1 for error)

    The function performs these steps:
    1. Parse command line arguments
    2. Configure logging based on debug and syslog flags
    3. Load and validate configuration file
    4. Initialize TLS repository with certificates
    5. Parse server and proxy addresses
    6. Start the proxy server
    7. Handle shutdown and cleanup
    """
    import argparse

    parser = argparse.ArgumentParser(description="IEEE 2030.5 proxy server with client certificate forwarding")
    parser.add_argument(dest="config", help="Configuration file for the server.")
    parser.add_argument(
        "--debug", action="store_true", default=False, help="Turns debugging on for logging of the proxy."
    )
    parser.add_argument(
        "--syslog", action="store_true", default=False, help="Enable syslog logging in addition to console logging."
    )
    parser.add_argument(
        "--log-file", type=str, default=None, help="Path to log file. Logs will be written to this file in addition to console."
    )
    parser.add_argument(
        "--syslog-facility",
        default="local0",
        choices=[
            "kern",
            "user",
            "mail",
            "daemon",
            "auth",
            "syslog",
            "lpr",
            "news",
            "uucp",
            "cron",
            "authpriv",
            "ftp",
            "local0",
            "local1",
            "local2",
            "local3",
            "local4",
            "local5",
            "local6",
            "local7",
        ],
        help="Syslog facility to use (default: local0)",
    )
    opts = parser.parse_args()

    # If syslog facility is specified (and it's not the default), enable syslog automatically
    use_syslog = opts.syslog or opts.syslog_facility != "local0"

    # Setup enhanced logging with optional syslog and file logging
    logger = setup_logging(
        debug=opts.debug,
        use_syslog=use_syslog,
        syslog_facility=opts.syslog_facility,
        log_file=opts.log_file
    )
    _log.debug(f"Starting 2030.5 proxy server with config: {opts.config}")

    if use_syslog:
        _log.info(f"Syslog enabled with facility: {opts.syslog_facility}")

    try:
        _log.debug(f"Loading configuration from {opts.config}")
        cfg_path = Path(opts.config).expanduser().resolve(strict=True)
        cfg_dict = yaml.safe_load(cfg_path.read_text())
        _log.debug(f"Loaded configuration: {cfg_dict}")

        config = ServerConfiguration(**cfg_dict)

        # Set environment variable for LFDI calculation mode
        if config.lfdi_mode == "lfdi_mode_from_file":
            os.environ["IEEE_2030_5_CERT_FROM_COMBINED_FILE"] = "1"
            _log.info("Using LFDI calculation from combined certificate file")

        if config.proxy_hostname is None:
            _log.error("Invalid proxy_hostname in config file.")
            return

        _log.debug(f"Initializing TLS repository: {config.tls_repository}")
        tls_repo = TLSRepository(
            repo_dir=config.tls_repository,
            openssl_cnffile_template=config.openssl_cnf,
            serverhost=config.server_hostname,
            proxyhost=config.proxy_hostname,
            clear=False,
        )
        _log.debug("TLS repository initialized successfully")

        proxy_host = build_address_tuple(config.proxy_hostname)
        server_host = build_address_tuple(config.server_hostname)

        _log.debug(f"Proxy host tuple: {proxy_host}")
        _log.debug(f"Server host tuple: {server_host}")

        # Get GridAPPS-D config from the gridappsd section if present
        gridappsd_address = None
        gridappsd_port = 61613
        gridappsd_username = "system"
        gridappsd_password = "manager"

        if hasattr(config, 'gridappsd') and config.gridappsd:
            gridappsd_cfg = config.gridappsd
            # Handle both dict and GridappsdConfiguration object
            if hasattr(gridappsd_cfg, 'address'):
                gridappsd_address = gridappsd_cfg.address
                gridappsd_port = gridappsd_cfg.port
                gridappsd_username = gridappsd_cfg.username
                gridappsd_password = gridappsd_cfg.password
            else:
                gridappsd_address = gridappsd_cfg.get('address', 'localhost')
                gridappsd_port = gridappsd_cfg.get('port', 61613)
                gridappsd_username = gridappsd_cfg.get('username', 'system')
                gridappsd_password = gridappsd_cfg.get('password', 'manager')
            _log.info(f"GridAPPS-D publishing enabled: {gridappsd_address}:{gridappsd_port}")

        start_proxy(
            server_address=(proxy_host[0], int(proxy_host[1])),
            tls_repo=tls_repo,
            proxy_target=(server_host[0], int(server_host[1])),
            config=config,
            gridappsd_address=gridappsd_address,
            gridappsd_port=gridappsd_port,
            gridappsd_username=gridappsd_username,
            gridappsd_password=gridappsd_password,
        )

    except Exception as e:
        _log.critical(f"Fatal error in proxy server: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    _main()
