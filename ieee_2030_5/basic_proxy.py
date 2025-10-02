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
def setup_logging(debug=False, use_syslog=False, syslog_facility="local0"):
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

    Returns:
        logging.Logger: The configured root logger instance

    Syslog Integration:
        When syslog is enabled, log messages are sent to the system log daemon
        with the specified facility. This allows integration with system monitoring
        tools and centralized log management.

    Example:
        >>> logger = setup_logging(debug=True, use_syslog=True)
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
                timeout_read (int): Read timeout in seconds (default: 30)
                context (ssl.SSLContext): SSL context for the connection
        """
        # Set reasonable timeouts
        self.timeout_connect = kwargs.pop("timeout_connect", 30)
        self.timeout_read = kwargs.pop("timeout_read", 30)

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

            # Set socket read timeout
            self.sock.settimeout(self.timeout_read)
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

    # Set reasonable timeouts for client connections
    timeout = 300  # 5 minutes for client socket timeout

    # Type annotation for the server to ensure it has our required attributes
    server: ProxyServer

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
        if hasattr(self.connection, "settimeout"):
            self.connection.settimeout(self.timeout)
            _log.debug(f"Set client connection timeout to {self.timeout}s for {self.client_address}")

        # Verify server has required attributes
        if not hasattr(self.server, "tls_repo"):
            _log.error(f"Server {type(self.server)} does not have tls_repo attribute")
            raise RuntimeError("Server missing tls_repo attribute")
        if not hasattr(self.server, "proxy_target"):
            _log.error(f"Server {type(self.server)} does not have proxy_target attribute")
            raise RuntimeError("Server missing proxy_target attribute")

        _log.debug(f"RequestForwarder setup complete for {self.client_address}")

    def handle(self):
        """
        Handle multiple requests if keep-alive is enabled.

        Implements HTTP/1.1 persistent connection handling by processing multiple
        requests over a single client connection. This improves performance by
        reducing connection overhead for clients making multiple requests.

        The method continues processing requests until:
        - Client requests connection close
        - Connection timeout occurs
        - Maximum requests per connection reached (1000)
        - An unrecoverable error occurs
        """
        self.close_connection = False
        client_info = f"{self.client_address[0]}:{self.client_address[1]}"
        _log.debug(f"Starting connection handler for client {client_info}")

        try:
            # Process requests until the connection should be closed
            request_count = 0
            while not self.close_connection:
                request_count += 1
                _log.debug(f"Handling request #{request_count} for client {client_info}")

                if not self.handle_one_request():
                    break

                # Limit number of requests per connection to prevent resource exhaustion
                if request_count >= 1000:  # Same as Keep-Alive max
                    _log.debug(f"Reached max requests ({request_count}) for client {client_info}")
                    self.close_connection = True
                    break

        except Exception as e:
            _log.error(f"Error in persistent connection handler for {client_info}: {e}")
            self.close_connection = True
        finally:
            _log.debug(f"Closing connection handler for client {client_info} after {request_count} requests")

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
        Creates a new connection to the server with proper error handling.

        Establishes a fresh HTTPS connection to the backend server for each client
        request, using the appropriate SSL context based on the client's certificate.
        This approach ensures isolation between client requests and enables proper
        certificate-based authentication.

        The method is optimized for concurrent client requests with:
        - Reduced retry attempts for faster response under load
        - Shorter timeouts for better responsiveness
        - Comprehensive error handling and logging

        Returns:
            HTTPSConnectionWithTimeout: An established connection to the backend server

        Raises:
            RuntimeError: If SSL context creation fails or all connection attempts fail

        Connection Strategy:
        - Creates SSL context once per request (cached for retries)
        - Uses shorter timeouts for better concurrency
        - Implements retry logic with exponential backoff
        - Provides detailed logging for debugging connection issues
        """
        max_retries = 2  # Reduced retries for faster response under load
        retry_delay = 0.5  # Shorter delay for better responsiveness
        host, port = self.server.proxy_target
        client_info = f"{self.client_address[0]}:{self.client_address[1]}"
        _log.debug(f"Creating server connection to {host}:{port} for client {client_info}")

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
                    timeout_connect=30,  # Reasonable connect timeout
                    timeout_read=60,  # Reasonable read timeout
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
                    self.send_header("Keep-Alive", "timeout=300, max=1000")
                    _log.info("  Connection: keep-alive")
                    _log.info("  Keep-Alive: timeout=300, max=1000")
                    _log.debug("Maintaining keep-alive connection with client")
                else:
                    self.send_header("Connection", "close")
                    _log.info("  Connection: close")
                    _log.debug("Client requested connection close")
            elif "keep-alive" in client_connection:
                # HTTP/1.0 with explicit keep-alive
                self.send_header("Connection", "keep-alive")
                self.send_header("Keep-Alive", "timeout=300, max=1000")
                _log.info("  Connection: keep-alive")
                _log.info("  Keep-Alive: timeout=300, max=1000")
                _log.debug("HTTP/1.0 client requested keep-alive")
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
            # Always close the server connection
            _log.debug("Closing server connection")
            try:
                conn.close()
            except Exception as e:
                _log.warning(f"Error closing server connection: {e}")

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

            # Add Connection: close to server request to ensure proper cleanup
            headers["Connection"] = "close"

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
            # Ensure server connection is closed if still open
            if conn:
                _log.debug(f"Closing connection in finally block for client {client_info}")
                try:
                    conn.close()
                except Exception as e:
                    _log.warning(f"Error closing connection for client {client_info}: {e}")

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
    server_address: tuple[str, int], tls_repo: TLSRepository, proxy_target: tuple[str, int], config: ServerConfiguration
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

    The function configures:
    - TLS server context requiring client certificates
    - Certificate chain loading for server identity
    - Permissive cipher suites for compatibility
    - LFDI calculation method based on config.lfdi_mode
    - Graceful shutdown handling

    LFDI Calculation Modes:
    - lfdi_mode_from_file: Uses SHA256 of combined certificate file content
    - lfdi_mode_from_cert_fingerprint: Uses certificate's built-in fingerprint

    Server Operation:
    - Binds to the specified address and port
    - Loads server certificates from TLS repository
    - Requires client certificates (CERT_REQUIRED)
    - Runs until KeyboardInterrupt or fatal error
    """
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

        _log.info("Proxy server started successfully")
        _log.debug("Entering serve_forever() loop")
        httpd.serve_forever()

    except KeyboardInterrupt:
        _log.warning("Proxy server shutting down due to keyboard interrupt...")
    except Exception as e:
        _log.error(f"Proxy server error: {e}", exc_info=True)
    finally:
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

    # Setup enhanced logging with optional syslog
    logger = setup_logging(debug=opts.debug, use_syslog=use_syslog, syslog_facility=opts.syslog_facility)
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

        start_proxy(
            server_address=(proxy_host[0], int(proxy_host[1])),
            tls_repo=tls_repo,
            proxy_target=(server_host[0], int(server_host[1])),
            config=config,
        )

    except Exception as e:
        _log.critical(f"Fatal error in proxy server: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    _main()
