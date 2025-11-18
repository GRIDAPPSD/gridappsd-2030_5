import hashlib
import json
import logging
import queue
import random
import re
import socket
import ssl
import threading
import time
import uuid
import xml.dom.minidom
from dataclasses import fields
from datetime import datetime
from functools import lru_cache
from pathlib import Path

import OpenSSL
import werkzeug.exceptions
from flask import Flask, Response, g, redirect, render_template, request, url_for

# from flask_socketio import SocketIO, send
from werkzeug.serving import BaseWSGIServer, run_simple

from ieee_2030_5.utils import dataclass_to_xml

__all__ = ["build_server"]

import ieee_2030_5.adapters as adpt
import ieee_2030_5.hrefs as hrefs
import ieee_2030_5.models as m
from ieee_2030_5.certs import TLSRepository, lfdi_from_fingerprint, sfdi_from_lfdi

# templates = Jinja2Templates(directory="templates")
from ieee_2030_5.config import ServerConfiguration
from ieee_2030_5.data.indexer import get_href, get_href_all_names
from ieee_2030_5.models import DeviceCategoryType
from ieee_2030_5.server.admin_endpoints import AdminEndpoints

# from ieee_2030_5.server.server_constructs import EndDevices, get_groups
from ieee_2030_5.server.server_endpoints import ServerEndpoints

_log = logging.getLogger(__file__)
# Create a specific logger for HTTP communication
_log_http = logging.getLogger("ieee_2030_5.http")

server_config: ServerConfiguration | None = None
tls_repository: TLSRepository | None = None

# Maximum header value + 1
# 64KB + 1
MAX_REQUEST_LINE_SIZE = 65537


def setup_request_logging():
    """Configure loggers for HTTP debugging"""
    # Create file handler for HTTP logs
    http_handler = logging.FileHandler("logs/http_debug.log")
    http_handler.setLevel(logging.DEBUG)

    # Create formatter with detailed information
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] [%(thread)d] %(message)s")
    http_handler.setFormatter(formatter)

    # Add handler to the logger
    _log_http.setLevel(logging.DEBUG)
    _log_http.addHandler(http_handler)


def log_socket_info(server):
    """Log socket options for debugging"""
    try:
        socket_opts = {}
        for opt_name in ["SO_KEEPALIVE", "SO_REUSEADDR", "SO_RCVBUF", "SO_SNDBUF"]:
            if hasattr(socket, opt_name):
                opt_val = getattr(socket, opt_name)
                try:
                    socket_opts[opt_name] = server.socket.getsockopt(socket.SOL_SOCKET, opt_val)
                except:
                    socket_opts[opt_name] = "Error getting option"

        # Try to get TCP keep-alive parameters if available
        if hasattr(socket, "TCP_KEEPIDLE"):
            try:
                socket_opts["TCP_KEEPIDLE"] = server.socket.getsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE)
            except:
                socket_opts["TCP_KEEPIDLE"] = "Not supported"

        _log_http.info(f"Server socket options: {socket_opts}")
    except Exception as e:
        _log_http.error(f"Error logging socket info: {e}")


def log_ssl_info(ssl_context):
    """Log SSL context information"""
    try:
        ssl_info = {
            "verify_mode": ssl_context.verify_mode,
            "check_hostname": getattr(ssl_context, "check_hostname", "N/A"),
            "options": ssl_context.options,
            "protocol": getattr(ssl_context, "protocol", "N/A"),
        }
        _log_http.info(f"SSL context configuration: {ssl_info}")
    except Exception as e:
        _log_http.error(f"Error logging SSL info: {e}")


class ConnectionManager(threading.Thread):
    def __init__(self, idle_timeout=300):  # 5 minutes default timeout
        super().__init__(daemon=True)
        self.idle_timeout = idle_timeout
        self.running = True
        self.name = "2030.5-Connection-Manager"

    def run(self):
        while self.running:
            try:
                self._clean_idle_connections()
            except Exception as e:
                _log.error(f"Error in connection manager: {e}")
            time.sleep(60)  # Check every minute

    def _clean_idle_connections(self):
        now = time.time()
        to_close = []

        with IEEE2030_5_RequestHandler.connection_lock:
            for conn_id, info in list(IEEE2030_5_RequestHandler.active_connections.items()):
                idle_time = now - info["last_activity"]
                if idle_time > self.idle_timeout:
                    to_close.append((conn_id, info))

        # Close connections outside the lock to avoid deadlocks
        for conn_id, info in to_close:
            try:
                _log.info(
                    f"Closing idle connection from {info['client_address']} after {self.idle_timeout}s of inactivity"
                )
                info["connection"].close()

                with IEEE2030_5_RequestHandler.connection_lock:
                    if conn_id in IEEE2030_5_RequestHandler.active_connections:
                        del IEEE2030_5_RequestHandler.active_connections[conn_id]

            except Exception as e:
                _log.warning(f"Error closing idle connection: {e}")

    def stop(self):
        self.running = False


class IEEE2030_5_RequestHandler(werkzeug.serving.WSGIRequestHandler):
    """Request handler that properly manages HTTP/1.1 persistent connections."""

    protocol_version = "HTTP/1.1"  # Force HTTP/1.1
    connection_lock = threading.Lock()
    active_connections = {}

    @staticmethod
    @lru_cache
    def is_admin(path_info) -> bool:
        """Check if the request path is for an admin endpoint."""
        admin_prefixes = ["/admin", "/socket-io", "/api"]
        return any(path_info.startswith(prefix) for prefix in admin_prefixes)

    def make_environ(self):
        """
        The superclass method develops the environ hash that eventually
        forms part of the Flask request object.

        We allow the superclass method to run first, then we insert the
        peer certificate into the hash. That exposes it to us later in
        the request variable that Flask provides
        """
        _log.debug("Making environment")
        environ = super(IEEE2030_5_RequestHandler, self).make_environ()

        # Check admin access early - admin endpoints are now unprotected
        if IEEE2030_5_RequestHandler.is_admin(environ["PATH_INFO"]):
            return self._setup_admin_environ_unprotected(environ)

        # Handle LFDI client mode (HTTP without certificates)
        if self.config.lfdi_client:
            return self._setup_lfdi_client_environ(environ)

        try:
            # Load certificate from various sources
            x509 = self._load_client_certificate(environ)

            # Set up certificate environment variables
            environ["ieee_2030_5_peercert"] = x509
            environ["ieee_2030_5_serial_number"] = x509.get_serial_number()

            # Calculate LFDI and SFDI
            self._calculate_device_identifiers(environ, x509)

            # Verify device is known (for non-admin requests)
            self._verify_device_authorization(environ)

        except OpenSSL.crypto.Error as e:
            _log.warning(f"Certificate error: {e}")
            environ["peercert"] = None
        except Exception as e:
            _log.error(f"Unexpected error in make_environ: {e}")
            raise

        return environ

    def _setup_admin_environ(self, environ):
        """Setup environment for admin requests (protected with certificates)"""
        try:
            cert, key = self.tlsrepo.get_file_pair("admin")
            x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert)
            environ["ieee_2030_5_peercert"] = x509
            environ["ieee_2030_5_serial_number"] = x509.get_serial_number()
            self._calculate_device_identifiers(environ, x509)
            return environ
        except Exception as e:
            _log.error(f"Failed to setup admin environment: {e}")
            raise werkzeug.exceptions.InternalServerError("Admin certificate setup failed")

    def _setup_admin_environ_unprotected(self, environ):
        """Setup environment for unprotected admin requests (no certificate required)"""
        # Set up minimal environment for admin access without requiring certificates
        # Use a valid 40-character hex LFDI for admin access
        admin_lfdi = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"  # 40 character hex string
        environ["ieee_2030_5_lfdi"] = admin_lfdi
        environ["ieee_2030_5_sfdi"] = sfdi_from_lfdi(admin_lfdi)
        environ["ieee_2030_5_admin_access"] = True  # Flag to indicate admin access
        _log.debug("Admin access granted without certificate verification")
        return environ

    def _setup_lfdi_client_environ(self, environ):
        """Setup environment for LFDI client mode (HTTP without certificates)"""
        environ["ieee_2030_5_lfdi"] = self.config.lfdi_client
        environ["ieee_2030_5_sfdi"] = sfdi_from_lfdi(self.config.lfdi_client)
        return environ

    def _load_client_certificate(self, environ):
        """Load client certificate from proxy headers or direct TLS connection"""
        # Try proxy headers first (with validation)
        if "HTTP_SSL_CLIENT_CERT" in environ or "SSL_CLIENT_CERT" in environ:
            return self._load_certificate_from_proxy_headers(environ)

        # Fall back to direct TLS connection
        return self._load_certificate_from_connection()

    def _load_certificate_from_proxy_headers(self, environ):
        """Load and validate certificate from proxy headers"""
        cert_header = "HTTP_SSL_CLIENT_CERT" if "HTTP_SSL_CLIENT_CERT" in environ else "SSL_CLIENT_CERT"
        _log.debug(f"Using {cert_header} from proxy header")

        cert_pem = environ[cert_header]
        _log.debug(f"Raw certificate from proxy: {cert_pem[:50]}...")

        # Handle certificate format - proxy may send it as a single line with spaces
        if cert_pem.startswith("-----BEGIN CERTIFICATE-----") and "-----END CERTIFICATE-----" in cert_pem:
            # Certificate is in single-line format, need to properly format it
            if "\n" not in cert_pem:
                _log.debug("Converting single-line certificate to proper PEM format")
                # Split on the certificate boundaries and base64 content
                parts = cert_pem.split("-----BEGIN CERTIFICATE-----")
                if len(parts) == 2:
                    remaining = parts[1].split("-----END CERTIFICATE-----")
                    if len(remaining) == 2:
                        base64_content = remaining[0].strip()
                        # Remove any spaces from the base64 content and reformat
                        base64_content = base64_content.replace(" ", "")
                        # Add newlines every 64 characters for proper PEM format
                        formatted_lines = []
                        for i in range(0, len(base64_content), 64):
                            formatted_lines.append(base64_content[i : i + 64])

                        cert_pem = (
                            "-----BEGIN CERTIFICATE-----\n" + "\n".join(formatted_lines) + "\n-----END CERTIFICATE-----"
                        )
                        _log.debug("Reformatted certificate to proper PEM format")

        try:
            x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert_pem)
            _log.debug(f"Successfully loaded client certificate from proxy header for CN: {x509.get_subject().CN}")

            # Additional validation using other proxy headers if available
            self._validate_proxy_certificate_headers(environ, x509)

            return x509
        except Exception as e:
            _log.error(f"Failed to load certificate from proxy header: {e}")
            _log.error(f"Certificate content: {cert_pem}")
            raise

    def _load_certificate_from_connection(self):
        """Load certificate directly from TLS connection"""
        try:
            x509_binary = self.connection.getpeercert(True)
            if not x509_binary:
                raise ValueError("No client certificate provided in TLS connection")

            x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_ASN1, x509_binary)
            _log.debug(f"Successfully loaded client certificate from TLS connection for CN: {x509.get_subject().CN}")
            return x509
        except Exception as e:
            _log.error(f"Failed to load certificate from TLS connection: {e}")
            raise

    def _validate_proxy_certificate_headers(self, environ, x509):
        """Validate certificate using additional proxy headers if available"""
        # Check if proxy provided additional validation headers
        if "HTTP_SSL_CLIENT_S_DN" in environ:
            expected_subject = str(x509.get_subject())
            provided_subject = environ["HTTP_SSL_CLIENT_S_DN"]
            if expected_subject != provided_subject:
                _log.warning(f"Subject DN mismatch: expected {expected_subject}, got {provided_subject}")

        if "HTTP_SSL_CLIENT_SERIAL" in environ:
            expected_serial = str(x509.get_serial_number())
            provided_serial = environ["HTTP_SSL_CLIENT_SERIAL"]
            if expected_serial != provided_serial:
                _log.warning(f"Serial number mismatch: expected {expected_serial}, got {provided_serial}")

        if "HTTP_SSL_CLIENT_FINGERPRINT" in environ:
            expected_fingerprint = x509.digest("sha256").decode("ascii")
            provided_fingerprint = environ["HTTP_SSL_CLIENT_FINGERPRINT"]
            if expected_fingerprint != provided_fingerprint:
                _log.warning(f"Fingerprint mismatch: expected {expected_fingerprint}, got {provided_fingerprint}")

    def _normalize_lfdi(self, lfdi_value):
        """Normalize LFDI to consistent lowercase hex string format"""
        if isinstance(lfdi_value, bytes):
            return lfdi_value.hex().lower()
        else:
            # Remove any non-hex characters and convert to lowercase
            return str(lfdi_value).lower().replace("\\x", "").replace(" ", "").replace("-", "")

    def _calculate_device_identifiers(self, environ, x509):
        """Calculate LFDI and SFDI from certificate"""
        if IEEE2030_5_RequestHandler.config.lfdi_mode == "lfdi_mode_from_file":
            _log.debug("Using hash from combined file")
            try:
                pth = IEEE2030_5_RequestHandler.tlsrepo.__get_combined_file__(x509.get_subject().CN)
                sha256hash = hashlib.sha256(pth.read_text().encode("utf-8")).hexdigest()
                raw_lfdi = lfdi_from_fingerprint(sha256hash)
            except Exception as e:
                _log.error(f"Failed to read combined file for {x509.get_subject().CN}: {e}")
                raise
        else:
            raw_lfdi = lfdi_from_fingerprint(x509.digest("sha256").decode("ascii"))

        # Normalize LFDI to consistent format immediately when calculated
        environ["ieee_2030_5_lfdi"] = self._normalize_lfdi(raw_lfdi)
        environ["ieee_2030_5_sfdi"] = sfdi_from_lfdi(environ["ieee_2030_5_lfdi"])

        # Log LFDI/SFDI only when debugging specific auth issues
        # _log.debug(f"Environment lfdi: {environ['ieee_2030_5_lfdi']} sfdi: {environ['ieee_2030_5_sfdi']}")

    def _verify_device_authorization(self, environ):
        """Verify that the device is authorized to access the server"""
        # Skip verification for admin requests
        if IEEE2030_5_RequestHandler.is_admin(environ["PATH_INFO"]):
            return

        # Only verify in certificate fingerprint mode
        if IEEE2030_5_RequestHandler.config.lfdi_mode != "lfdi_mode_from_cert_fingerprint":
            _log.debug("Skipping device verification - not in cert fingerprint mode")
            return

        # Look up device in TLS repository
        found_device_id = self.tlsrepo.find_device_id_from_sfdi(environ["ieee_2030_5_sfdi"])
        if not found_device_id:
            _log.warning(f"Unknown device with SFDI: {environ['ieee_2030_5_sfdi']} from {self.client_address}")
            raise werkzeug.exceptions.Forbidden("Unknown device certificate")

        _log.debug(f"Verified device id: {found_device_id}")
        environ["ieee_2030_5_device_id"] = found_device_id

    def setup(self):
        """Set up the connection"""
        super().setup()
        # Set a long read timeout
        self.connection.settimeout(300)  # 5 minutes timeout

    def finish(self):
        """Finish handling the request"""
        super().finish()

    def handle(self):
        """Handle multiple requests if keep-alive is enabled"""
        # Register this as an active connection
        conn_id = id(self.connection)

        # Track this connection
        with self.connection_lock:
            self.active_connections[conn_id] = {
                "connection": self.connection,
                "last_activity": time.time(),
                "client_address": self.client_address,
            }

        try:
            # Process requests
            self.raw_requestline = None
            self.close_connection = True

            # Handle first request
            self.handle_one_request()

            # Continue handling requests until the connection is closed
            while not self.close_connection:
                self.raw_requestline = None
                self.handle_one_request()

        finally:
            # Clean up the connection tracking
            with self.connection_lock:
                if conn_id in self.active_connections:
                    del self.active_connections[conn_id]

    def handle_one_request(self):
        """Handle a single HTTP request with proper keep-alive support"""
        try:
            # Read the request line with a timeout
            self.raw_requestline = self.rfile.readline(MAX_REQUEST_LINE_SIZE)

            _log.debug(f"{'*' * 20}Raw Request Line {self.raw_requestline}")

            # If no data, close the connection
            if not self.raw_requestline:
                self.close_connection = True
                return

            # Process the request normally
            if not self.parse_request():
                self.close_connection = True
                return

            # Parse connection header
            connection_header = self.headers.get("Connection", "").lower()

            # Log only important requests at info level
            if any(p in self.path for p in ["/edev", "/der", "/dcap", "/fsa", "/msg"]):
                _log.info(f"Request: {self.command} {self.path}")
            # Connection header logging not needed for every request

            # Process the request
            handler = getattr(self, f"do_{self.command}", self.do_GET)
            handler()
            self.wfile.flush()

            # For HTTP/1.1, persistent is default unless 'Connection: close'
            if (
                self.request_version >= "HTTP/1.1"
                and "close" not in connection_header
                or "keep-alive" in connection_header
            ):
                self.close_connection = False
                # Keep-alive is normal, no need to log
                pass
            # Otherwise close
            else:
                self.close_connection = True
                # Connection close is normal, no need to log
                pass

        except TimeoutError:
            # Timeout reading from socket - close connection
            # Socket timeouts can be logged at warning level if needed
            _log.warning(f"Socket timeout from {self.client_address}")
            self.close_connection = True
        except Exception as e:
            # Handle any other errors
            _log.error(f"Error handling request: {e}")
            self.close_connection = True

    def send_response(self, code, message=None):
        """Send response with appropriate headers for persistent connections"""
        # Create the HTTP response line
        self.log_request(code)
        self.send_response_only(code, message)

        # Add server and date headers
        self.send_header("Server", "IEEE2030_5/1.0")
        self.send_header("Date", self.date_time_string())

        # Add keep-alive headers unless we're closing the connection
        if not self.close_connection:
            self.send_header("Connection", "keep-alive")
            self.send_header("Keep-Alive", "timeout=300, max=1000")


class IEEE2030_5_Server(BaseWSGIServer):
    """Custom WSGI server with optimizations for IEEE 2030.5"""

    def __init__(self, host, port, app, **kwargs):
        super().__init__(host, port, app, **kwargs)
        self.protocol_version = "HTTP/1.1"

    def server_bind(self):
        """Set socket options when binding the server socket"""
        # Set socket options for performance
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

        # Set TCP keep-alive options if available
        # These are platform-specific, so use try/except
        try:
            # Linux-specific options
            if hasattr(socket, "TCP_KEEPIDLE"):
                self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60)
            if hasattr(socket, "TCP_KEEPINTVL"):
                self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10)
            if hasattr(socket, "TCP_KEEPCNT"):
                self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 5)
        except (AttributeError, OSError):
            pass

        # Complete the binding process
        super().server_bind()


def set_socket_options(socket):
    """Configure socket options for optimized keep-alive support"""
    # Enable TCP keep-alive
    socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

    # Set keep-alive parameters if platform supports them
    # Linux specific, may need to adjust for other platforms
    if hasattr(socket, "TCP_KEEPIDLE") and hasattr(socket, "TCP_KEEPINTVL") and hasattr(socket, "TCP_KEEPCNT"):
        socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60)  # Start sending after 60 seconds of idle
        socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10)  # Send every 10 seconds
        socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 6)  # Consider dead after 6 failures


# based on
# https://stackoverflow.com/questions/19459236/how-to-handle-413-request-entity-too-large-in-python-flask-server#:~:text=server%20MAY%20close%20the%20connection,client%20from%20continuing%20the%20request.&text=time%20the%20client%20MAY%20try,you%20the%20Broken%20pipe%20error.&text=Great%20than%20the%20application%20is%20acting%20correct.
def log_client_request(lfdi: str, request_id: str, cn: str = None):
    """Log incoming request details to client-specific file"""
    debug_dir = Path("debug_client_traffic")

    # Ensure the debug directory exists
    debug_dir.mkdir(exist_ok=True)

    # Use CN for filename if available, otherwise fall back to LFDI
    # Sanitize the filename to remove any invalid characters
    safe_name = cn if cn else lfdi
    safe_name = safe_name.replace("/", "_").replace("\\", "_").replace(":", "_")
    filename = f"client_{safe_name}.txt"  # Changed to .txt
    client_file = debug_dir / filename

    timestamp = datetime.now().isoformat()

    # Try to get request body if present
    body_data = None
    if request.content_length and request.content_length > 0:
        try:
            # Get the raw data and restore it for the actual request handler
            body_data = request.get_data(as_text=True)
        except Exception as e:
            body_data = f"[Error reading body: {e}]"

    # Format XML body if present
    formatted_body = ""
    if body_data:
        try:
            dom = xml.dom.minidom.parseString(body_data)
            formatted_body = dom.toprettyxml(indent="  ")
            # Remove the XML declaration line if present and empty lines
            lines = formatted_body.split("\n")
            if lines[0].startswith("<?xml"):
                lines = lines[1:]
            # Remove excessive empty lines
            formatted_body = "\n".join(line for line in lines if line.strip() or not line)
        except Exception:
            # If XML parsing fails, use the raw body
            formatted_body = body_data

    # Write to file with error handling in human-readable format
    try:
        with open(client_file, "a") as f:
            f.write("=" * 80 + "\n")
            f.write(f"REQUEST [{timestamp}]\n")
            f.write(f"Request ID: {request_id}\n")
            f.write(f"Method: {request.method}\n")
            f.write(f"Path: {request.path}\n")
            if request.query_string:
                f.write(f"Query: {request.query_string.decode('utf-8')}\n")
            f.write(f"From: {request.remote_addr}\n")
            if formatted_body:
                f.write(f"\nBody:\n{formatted_body}\n")
            else:
                f.write("\nBody: (empty)\n")
            f.write("\n")
    except Exception as e:
        _log.error(f"Failed to write request log for {safe_name}: {e}")


def log_client_response(lfdi: str, request_id: str, response: Response, duration: float, cn: str = None):
    """Log outgoing response details to client-specific file"""
    debug_dir = Path("debug_client_traffic")

    # Ensure the debug directory exists
    debug_dir.mkdir(exist_ok=True)

    # Use CN for filename if available, otherwise fall back to LFDI
    # Sanitize the filename to remove any invalid characters
    safe_name = cn if cn else lfdi
    safe_name = safe_name.replace("/", "_").replace("\\", "_").replace(":", "_")
    filename = f"client_{safe_name}.txt"  # Changed to .txt
    client_file = debug_dir / filename

    timestamp = datetime.now().isoformat()

    # Try to get response body
    response_body = None
    try:
        response_body = response.get_data(as_text=True)
    except Exception as e:
        response_body = f"[Error reading body: {e}]"

    # Format XML body if present
    formatted_body = ""
    if response_body:
        try:
            dom = xml.dom.minidom.parseString(response_body)
            formatted_body = dom.toprettyxml(indent="  ")
            # Remove the XML declaration line if present and empty lines
            lines = formatted_body.split("\n")
            if lines[0].startswith("<?xml"):
                lines = lines[1:]
            # Remove excessive empty lines
            formatted_body = "\n".join(line for line in lines if line.strip() or not line)
        except Exception:
            # If XML parsing fails, use the raw body
            formatted_body = response_body

    # Write to file with error handling in human-readable format
    try:
        with open(client_file, "a") as f:
            f.write(f"RESPONSE [{timestamp}]\n")
            f.write(f"Request ID: {request_id}\n")
            f.write(f"Status: {response.status_code}\n")
            f.write(f"Duration: {duration:.3f}s\n")
            if formatted_body:
                f.write(f"\nBody:\n{formatted_body}\n")
            else:
                f.write("\nBody: (empty)\n")
            f.write("=" * 80 + "\n\n")
    except Exception as e:
        _log.error(f"Failed to write response log for {safe_name}: {e}")


def handle_chunking():
    """
    Sets the "wsgi.input_terminated" environment flag, thus enabling
    Werkzeug to pass chunked requests as streams.  The gunicorn server
    should set this, but it's not yet been implemented.
    """

    transfer_encoding = request.headers.get("Transfer-Encoding", None)
    if transfer_encoding == "chunked":
        request.environ["wsgi.input_terminated"] = True


def before_request():
    g.SERVER_CONFIG = server_config
    g.TLS_REPOSITORY = tls_repository
    # Add request tracking
    g.start_time = time.time()
    g.request_id = str(uuid.uuid4())[:8]  # Generate short request ID for tracking

    # Get request details early for burst detection
    method = request.method
    path = request.path

    # Simultaneous request detection and mitigation
    # Track recent requests to detect bursts and add delays for database-intensive operations
    current_time = g.start_time
    request_signature = f"{method}:{path}"

    # Initialize global request tracking if not exists
    if not hasattr(before_request, "_recent_requests"):
        before_request._recent_requests = []
        before_request._request_lock = threading.RLock()

    with before_request._request_lock:
        # Clean old requests (older than 100ms)
        before_request._recent_requests = [
            (ts, sig) for ts, sig in before_request._recent_requests if current_time - ts < 0.1
        ]

        # Check for simultaneous requests that could cause database contention
        simultaneous_count = len(before_request._recent_requests)
        recent_mup_posts = sum(1 for ts, sig in before_request._recent_requests if "POST:" in sig and "/mup" in sig)
        recent_db_ops = sum(
            1 for ts, sig in before_request._recent_requests if any(op in sig for op in ["POST:", "PUT:"])
        )

        # Add this request to tracking
        before_request._recent_requests.append((current_time, request_signature))

        # Apply burst mitigation for database-intensive operations
        should_delay = False
        delay_reason = ""

        if method in ["POST", "PUT"] and simultaneous_count > 0:
            if "/mup" in path and recent_mup_posts > 0:
                # Multiple MUP operations - high contention risk
                should_delay = True
                delay_reason = f"MUP burst (sim:{simultaneous_count}, mup:{recent_mup_posts})"
            elif recent_db_ops >= 2:
                # High database operation density
                should_delay = True
                delay_reason = f"DB op burst (sim:{simultaneous_count}, db_ops:{recent_db_ops})"

        if should_delay:
            # Add larger randomized delay to handle severe contention (100-500ms for high-risk operations)
            if "/mup" in path and recent_mup_posts > 0:
                # MUP operations get longer delays due to high contention
                delay = random.uniform(0.1, 0.5)  # 100-500ms
            else:
                # Other DB operations get moderate delays
                delay = random.uniform(0.05, 0.2)  # 50-200ms
            time.sleep(delay)
            _log_http.debug(f"[{g.request_id}] Added {delay * 1000:.1f}ms delay for {delay_reason}")

            # Update start time after delay
            g.start_time = time.time()

    # Log the incoming request details
    client_address = request.remote_addr
    protocol = request.environ.get("SERVER_PROTOCOL", "")

    # Log basic request info
    _log_http.info(f"[{g.request_id}] {client_address} - {method} {path} {protocol}")

    # Log detailed headers
    _log_http.debug(f"[{g.request_id}] Request Headers:")
    for name, value in request.headers.items():
        _log_http.debug(f"[{g.request_id}]   {name}: {value}")

    # Log Connection header specifically since it's important for keep-alive
    connection_header = request.headers.get("Connection", "none")
    _log_http.info(f"[{g.request_id}] Connection header: {connection_header}")

    # Log client certificate info if available
    if "ieee_2030_5_lfdi" in request.environ:
        _log_http.debug(f"[{g.request_id}] Client LFDI: {request.environ.get('ieee_2030_5_lfdi')}")

        # Client-specific debug logging to file
        lfdi = request.environ.get("ieee_2030_5_lfdi")
        if lfdi and getattr(server_config, "debug_client_traffic", False):
            try:
                # Try to get CN from the certificate
                cn = None
                if "ieee_2030_5_peercert" in request.environ:
                    try:
                        x509 = request.environ.get("ieee_2030_5_peercert")
                        cn = x509.get_subject().CN if x509 else None
                    except Exception as e:
                        _log.debug(f"Could not extract CN from certificate: {e}")
                log_client_request(lfdi, g.request_id, cn)
            except Exception as e:
                _log.error(f"Failed to log client request: {e}")


def after_request(response: Response) -> Response:
    # Calculate request processing time
    duration = time.time() - g.start_time

    # Log response details
    status_code = response.status_code
    content_length = response.headers.get("Content-Length", 0)
    content_type = response.headers.get("Content-Type", "unknown")

    # Log basic response info
    _log_http.info(
        f"[{g.request_id}] Response: {status_code} - {content_length} bytes - {content_type} ({duration:.3f}s)"
    )

    # Add necessary headers for XML responses
    if "Content-Type" not in response.headers:
        response.headers["Content-Type"] = "application/sep+xml"

    # Force persistent connections for HTTP/1.1
    if request.environ.get("SERVER_PROTOCOL") == "HTTP/1.1":
        response.headers["Connection"] = "keep-alive"
        response.headers["Keep-Alive"] = "timeout=300, max=1000"

    _log.debug(f"\nREQ: {request.path}")
    _log.debug(f"\nRESP HEADER: {str(response.headers).strip()}")
    resp = response.get_data().decode("utf-8")
    _log.debug(f"\nRESP: {resp}")

    # Client-specific debug logging to file
    lfdi = request.environ.get("ieee_2030_5_lfdi")
    if lfdi and getattr(server_config, "debug_client_traffic", False):
        try:
            # Try to get CN from the certificate
            cn = None
            if "ieee_2030_5_peercert" in request.environ:
                try:
                    x509 = request.environ.get("ieee_2030_5_peercert")
                    cn = x509.get_subject().CN if x509 else None
                except Exception as e:
                    _log.debug(f"Could not extract CN from certificate: {e}")
            log_client_response(lfdi, g.request_id, response, duration, cn)
        except Exception as e:
            _log.error(f"Failed to log client response: {e}")

    return response

    # Log response details
    status_code = response.status_code
    content_length = response.headers.get("Content-Length", 0)
    content_type = response.headers.get("Content-Type", "unknown")

    # Log basic response info
    _log_http.info(
        f"[{g.request_id}] Response: {status_code} - {content_length} bytes - {content_type} ({duration:.3f}s)"
    )

    # Log detailed response headers
    _log_http.debug(f"[{g.request_id}] Response Headers:")
    for name, value in response.headers.items():
        _log_http.debug(f"[{g.request_id}]   {name}: {value}")

    connection_header = request.headers.get("Connection", "").lower()
    if "keep-alive" in connection_header:
        response.headers["Connection"] = "keep-alive"
        response.headers["Keep-Alive"] = "timeout=60, max=1000"

    _log.debug(f"\nREQ: {request.path}")
    _log.debug(f"\nRESP HEADER: {str(response.headers).strip()}")
    resp = response.get_data().decode("utf-8")
    _log.debug(f"\nRESP: {resp}")

    if (
        request.environ.get("SERVER_PROTOCOL") == "HTTP/1.1"
        and "close" not in request.headers.get("Connection", "").lower()
    ):
        response.headers["Connection"] = "keep-alive"
        response.headers["Keep-Alive"] = "timeout=60, max=1000"
        _log_http.info(f"[{g.request_id}] Forced keep-alive for HTTP/1.1 request")

    return response


def __build_ssl_context__(tlsrepo: TLSRepository) -> ssl.SSLContext:
    server_key_file = str(tlsrepo.server_key_file)
    server_cert_file = str(tlsrepo.server_cert_file)
    ca_cert = str(tlsrepo.ca_cert_file)

    # Create SSL context
    ssl_context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH, cafile=str(ca_cert))
    ssl_context.load_cert_chain(certfile=server_cert_file, keyfile=server_key_file)
    ssl_context.verify_mode = ssl.CERT_OPTIONAL

    # Performance optimizations
    ssl_context.options |= ssl.OP_NO_TICKET

    # Enable session caching if supported
    if hasattr(ssl_context, "session_cache_mode"):
        ssl_context.session_cache_mode = ssl.SESS_CACHE_SERVER

    return ssl_context


def __build_ssl_context__old(tlsrepo: TLSRepository) -> ssl.SSLContext:
    # to establish an SSL socket we need the private key and certificate that
    # we want to serve to users.
    server_key_file = str(tlsrepo.server_key_file)
    server_cert_file = str(tlsrepo.server_cert_file)

    # in order to verify client certificates we need the certificate of the
    # CA that issued the client's certificate. In this example I have a
    # single certificate, but this could also be a bundle file.
    ca_cert = str(tlsrepo.ca_cert_file)

    # create_default_context establishes a new SSLContext object that
    # aligns with the purpose we provide as an argument. Here we provide
    # Purpose.CLIENT_AUTH, so the SSLContext is set up to handle validation
    # of client certificates.
    ssl_context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH, cafile=str(ca_cert))

    # load in the certificate and private key for our server to provide to clients.
    # force the client to provide a certificate.
    ssl_context.load_cert_chain(
        certfile=server_cert_file,
        keyfile=server_key_file,
        # password=app_key_password
    )
    # change this to ssl.CERT_REQUIRED during deployment.
    # TODO if required we have to have one all the time on the server.
    ssl_context.verify_mode = ssl.CERT_OPTIONAL  # ssl.CERT_REQUIRED
    # Enable session caching for TLS performance
    ssl_context.options |= ssl.OP_NO_TICKET
    # ssl_context.set_session_cache_mode(ssl.SESS_CACHE_SERVER)

    return ssl_context


def __build_http_app__(config: ServerConfiguration) -> Flask:
    app = Flask(__name__,
                template_folder=str(Path(".").resolve().joinpath("templates")),
                static_folder=str(Path(".").resolve().joinpath("static")),
                static_url_path="/static")
    # Debug headers path and request arguments
    app.before_request(before_request)
    # Allows for larger data to be sent through because of chunking types.
    app.before_request(handle_chunking)
    app.after_request(after_request)

    @app.route("/dcap", methods=["GET"])
    def http_root() -> Response:
        return dataclass_to_xml(m.DeviceCapability(href="https://localhost:7443/dcap"))
        # return adpt.DeviceCapabilityAdapter()


def __build_app__(config: ServerConfiguration, tlsrepo: TLSRepository) -> Flask:
    app = Flask(__name__,
                template_folder=str(Path(".").resolve().joinpath("templates")),
                static_folder=str(Path(".").resolve().joinpath("static")),
                static_url_path="/static")

    app.config["PRESERVE_CONTEXT_ON_EXCEPTION"] = False

    # Force HTTP/1.1 responses
    app.config["SERVER_PROTOCOL"] = "HTTP/1.1"

    # Debug headers path and request arguments
    app.before_request(before_request)
    # Allows for larger data to be sent through because of chunking types.
    app.before_request(handle_chunking)
    app.after_request(after_request)

    # Adapters already initialized in __main__.py

    ServerEndpoints(app, tls_repo=tlsrepo, config=config)
    AdminEndpoints(app, tls_repo=tlsrepo, config=config)

    # TODO investigate socket-io connection here.
    # app.config['SECRET_KEY'] = 'secret!'
    # socketio = SocketIO(app)

    # @socketio.on('my event')
    # def handle_my_custom_event(json):
    #     print('received json: ' + str(json))
    #     send(f"I received: {json}")

    # now we get into the regular Flask details, except we're passing in the peer certificate
    # as a variable to the template.
    @app.route("/")
    def root():
        return redirect("/admin/index.html")
        # cert = request.environ['peercert']
        # cert_data = f"{cert.get_subject()}"
        # return render_template("admin/index.html")
        # return render_template('helloworld.html', client_cert=request.environ['peercert'])

    @app.route("/admin/")
    @app.route("/admin/index.html")
    def admin_home():
        return render_template("admin/index.html")

    @app.route("/admin/execute", methods=["get", "post"])
    def execute_method():
        if request.method == "POST":
            _log.debug("Posting stuff to server.")

        return render_template("admin/execute.html")

    @app.route("/admin/add-fsa", methods=["get", "post"])
    def admin_fsa():
        if request.method == "POST":
            # Get form data
            description = request.form.get("description", "").strip()
            primacy = request.form.get("primacy", "0").strip()
            end_device_id = request.form.get("end_device_id", "").strip()
            selected_programs = request.form.getlist("programs")

            # Validation
            if not description:
                end_devices = adpt.EndDeviceAdapter.get_all()
                programs = adpt.ListAdapter.get_list(hrefs.DEFAULT_DERP_ROOT, m.DERProgram)
                return render_template(
                    "admin/add-fsa.html",
                    end_devices=end_devices,
                    programs=programs.DERProgram if programs and hasattr(programs, 'DERProgram') else [],
                    error="Description is required"
                )

            if not end_device_id:
                end_devices = adpt.EndDeviceAdapter.get_all()
                programs = adpt.ListAdapter.get_list(hrefs.DEFAULT_DERP_ROOT, m.DERProgram)
                return render_template(
                    "admin/add-fsa.html",
                    end_devices=end_devices,
                    programs=programs.DERProgram if programs and hasattr(programs, 'DERProgram') else [],
                    error="End device is required"
                )

            try:
                device_index = int(end_device_id)
                end_device = adpt.EndDeviceAdapter.get(device_index)
                if not end_device:
                    raise ValueError("Device not found")
            except (ValueError, TypeError) as e:
                end_devices = adpt.EndDeviceAdapter.get_all()
                programs = adpt.ListAdapter.get_list(hrefs.DEFAULT_DERP_ROOT, m.DERProgram)
                return render_template(
                    "admin/add-fsa.html",
                    end_devices=end_devices,
                    programs=programs.DERProgram if programs and hasattr(programs, 'DERProgram') else [],
                    error=f"Invalid end device: {e}"
                )

            # Get the device's FSA list href
            ed_href = hrefs.EndDeviceHref(device_index)
            fsa_list_href = ed_href.function_set_assignments

            # Initialize FSA list if needed
            adpt.ListAdapter.initialize_uri(fsa_list_href, m.FunctionSetAssignments)

            # Get next FSA index
            fsa_index = adpt.ListAdapter.get_list_size(fsa_list_href)

            # Create FSA
            fsa_href = hrefs.SEP.join((fsa_list_href, str(fsa_index)))
            fsa = m.FunctionSetAssignments(
                href=fsa_href,
                mRID=adpt.get_global_mrids().new_mrid(),
                description=description,
                subscribable=1,
            )

            # Set primacy if provided
            try:
                primacy_value = int(primacy)
                # Note: FunctionSetAssignments has a primacy field in IEEE 2030.5
                # but it may not be directly settable here - it's typically in DERProgram
            except (ValueError, TypeError):
                pass

            # Create DER program list for this FSA if programs selected
            if selected_programs:
                derp_list_href = hrefs.SEP.join((fsa_href, "derp"))
                adpt.ListAdapter.initialize_uri(derp_list_href, m.DERProgram)

                fsa.DERProgramListLink = m.DERProgramListLink(
                    href=derp_list_href,
                    all=len(selected_programs),
                )

                # Note: In a full implementation, we'd copy selected programs
                # For now, just set up the link

            # Add FSA to the device's FSA list
            from ieee_2030_5.data.indexer import add_href
            result = adpt.ListAdapter.append(fsa_list_href, fsa)
            if result.success:
                add_href(fsa.href, fsa)
                adpt.get_global_mrids().add_item_with_mrid(fsa.href, fsa)
                _log.info("Created FSA '%s' at %s for device %d", description, fsa_href, device_index)
            else:
                end_devices = adpt.EndDeviceAdapter.get_all()
                programs = adpt.ListAdapter.get_list(hrefs.DEFAULT_DERP_ROOT, m.DERProgram)
                return render_template(
                    "admin/add-fsa.html",
                    end_devices=end_devices,
                    programs=programs.DERProgram if programs and hasattr(programs, 'DERProgram') else [],
                    error=f"Failed to create FSA: {result.error}"
                )

            return redirect(url_for("admin_home"))

        # GET request - show form
        end_devices = adpt.EndDeviceAdapter.get_all()
        programs = adpt.ListAdapter.get_list(hrefs.DEFAULT_DERP_ROOT, m.DERProgram)

        return render_template(
            "admin/add-fsa.html",
            end_devices=end_devices,
            programs=programs.DERProgram if programs and hasattr(programs, 'DERProgram') else []
        )

    @app.route("/admin/add-end-device", methods=["get", "post"])
    def admin_end_device():
        if request.method == "POST":
            # Get form data
            cert_name = request.form.get("cert_name", "").strip()
            pin = request.form.get("pin", "").strip()

            # Validation
            if not cert_name:
                return render_template(
                    "admin/add-end-device.html",
                    device_categories=DeviceCategoryType,
                    error="Certificate name is required"
                )

            # Validate certificate name format (alphanumeric, underscores, hyphens)
            if not re.match(r'^[a-zA-Z0-9_-]+$', cert_name):
                return render_template(
                    "admin/add-end-device.html",
                    device_categories=DeviceCategoryType,
                    error="Certificate name can only contain letters, numbers, underscores, and hyphens"
                )

            # Validate PIN if provided (numeric only)
            if pin and not pin.isdigit():
                return render_template(
                    "admin/add-end-device.html",
                    device_categories=DeviceCategoryType,
                    error="PIN must contain only numbers"
                )

            # Build device category from checkboxes
            device_category = 0
            for category in DeviceCategoryType:
                if request.form.get(category.name):
                    device_category |= category.value

            try:
                # Create EndDevice
                end_device = m.EndDevice()
                end_device.deviceCategory = device_category if device_category else None

                # Set PIN for registration
                if pin:
                    end_device.Registration = m.Registration(pIN=int(pin))

                # Add the device to get href
                end_device = adpt.EndDeviceAdapter.add(end_device)

                # Normalize certificate name
                if cert_name.startswith("/"):
                    cert_name = cert_name[1:]
                cert_name = cert_name.replace("/", "-")

                # Create certificate
                cert_file, key_file = tlsrepo.get_file_pair(cert_name)
                Path(cert_file).unlink(missing_ok=True)
                Path(key_file).unlink(missing_ok=True)
                tlsrepo.create_cert(cert_name)

                # Set LFDI and SFDI from certificate
                end_device.lFDI = get_lfdi_from_cert(cert_file)
                end_device.sFDI = get_sfdi_from_lfdi(end_device.lFDI)

                # Update the device with LFDI/SFDI
                index = int(end_device.href.rsplit(hrefs.SEP)[-1])
                adpt.EndDeviceAdapter.put(index, end_device)

                # Create device capability
                create_device_capability(index, None, config)

                _log.info(f"Created end device: {end_device.href} with cert: {cert_name}")

                return redirect(url_for("admin_home"))

            except Exception as e:
                _log.error(f"Failed to create end device: {e}")
                return render_template(
                    "admin/add-end-device.html",
                    device_categories=DeviceCategoryType,
                    error=f"Failed to create end device: {str(e)}"
                )

        return render_template("admin/add-end-device.html", device_categories=DeviceCategoryType)

    @app.route("/admin/add-der-program", methods=["get", "post"])
    def admin_der_program():
        controls, default_control = adpt.DERControlAdapter.get_all()

        if request.method == "POST":
            args = request.form.to_dict()
            print(f"Args before: {args}")
            adpt.DERProgramAdapter.build(**args)
            print(f"Args after: {args}")

            return redirect(url_for("admin_home"))

        return render_template("admin/add-der-program.html", der_controls=controls, default_der_control=default_control)

    @app.route("/admin/default-der-control", methods=["get", "post"])
    def admin_default_der_control():
        dderc = adpt.DERControlAdapter.fetch_default()

        if request.method == "POST":
            kwargs = request.form.to_dict()
            # TODO: Build a helper that will allow us to populate by known form elements.
            # Helper for connect and energize mode, which are ready for usage.
            if "enable_opModConnect" not in kwargs:
                kwargs["enable_opModConnect"] = "off"

            if "enable_opModEnergize" not in kwargs:
                kwargs["enable_opModEnergize"] = "off"

            field_list = fields(dderc)
            base_control = dderc.DERControlBase
            for k, v in kwargs.items():
                if k.startswith("enable_"):
                    k = k.split("_")[1]
                    v = True if v == "on" else False

                for f in field_list:
                    if k == f.name:
                        setattr(dderc, k, v)
                for f in fields(base_control):
                    if k == f.name:
                        setattr(base_control, k, v)

            adpt.DERControlAdapter.store_default(dderc=dderc)

            return redirect(url_for("admin_home"))

        return render_template("admin/update-default-der-control.html", dderc=dderc)

    # DER Management Routes
    @app.route("/admin/der/list")
    def admin_der_list():
        """List all DERs."""
        start = int(request.args.get("s", 0))
        limit = int(request.args.get("l", 100))
        ders = adpt.DERAdapter.fetch_all(m.DERList(), start=start, limit=limit)
        return render_template("admin/der-list.html", ders=ders)

    @app.route("/admin/der/add", methods=["GET", "POST"])
    def admin_der_add():
        """Add a new DER."""
        if request.method == "POST":
            # Create DER from form data
            der = m.DER()

            # Set current program if provided
            current_program = request.form.get("current_program")
            if current_program:
                der.CurrentDERProgramLink = m.CurrentDERProgramLink(href=current_program)

            # Add the DER
            der = adpt.DERAdapter.add(der)

            return redirect(url_for("admin_der_list"))

        # GET: Show form
        end_devices = adpt.EndDeviceAdapter.fetch_all(m.EndDeviceList())
        programs = adpt.DERProgramAdapter.fetch_all(m.DERProgramList())
        return render_template(
            "admin/der-form.html",
            der=None,
            end_devices=end_devices.EndDevice if end_devices.EndDevice else [],
            programs=programs.DERProgram if programs.DERProgram else [],
            capability=None,
            settings=None
        )

    @app.route("/admin/der/<int:der_id>")
    def admin_der_detail(der_id: int):
        """View DER details."""
        der = adpt.DERAdapter.fetch(der_id)
        return render_template("admin/der-detail.html", der=der, der_id=der_id)

    @app.route("/admin/der/<int:der_id>/edit", methods=["GET", "POST"])
    def admin_der_edit(der_id: int):
        """Edit an existing DER."""
        if request.method == "POST":
            # Get existing DER
            der = adpt.DERAdapter.fetch(der_id)

            # Update current program if provided
            current_program = request.form.get("current_program")
            if current_program:
                der.CurrentDERProgramLink = m.CurrentDERProgramLink(href=current_program)
            else:
                der.CurrentDERProgramLink = None

            # Save the DER
            adpt.DERAdapter.put(der_id, der)

            return redirect(url_for("admin_der_list"))

        # GET: Show form with existing data
        der = adpt.DERAdapter.fetch(der_id)
        end_devices = adpt.EndDeviceAdapter.fetch_all(m.EndDeviceList())
        programs = adpt.DERProgramAdapter.fetch_all(m.DERProgramList())
        return render_template(
            "admin/der-form.html",
            der=der,
            end_devices=end_devices.EndDevice if end_devices.EndDevice else [],
            programs=programs.DERProgram if programs.DERProgram else [],
            capability=None,
            settings=None
        )

    @app.route("/admin/der/save", methods=["POST"])
    def admin_der_save():
        """Save DER (redirect target for form)."""
        href = request.form.get("href")

        if href:
            # Update existing
            der_id = int(href.rsplit("/", 1)[-1])
            return redirect(url_for("admin_der_edit", der_id=der_id), code=307)
        else:
            # Create new
            return redirect(url_for("admin_der_add"), code=307)

    # DER Control Management Routes
    @app.route("/admin/controls/list")
    def admin_control_list():
        """List all DER Controls."""
        start = int(request.args.get("s", 0))
        limit = int(request.args.get("l", 100))
        controls = adpt.DERControlAdapter.fetch_all(m.DERControlList(), start=start, limit=limit)
        return render_template("admin/controls-list.html", controls=controls)

    @app.route("/admin/controls/add", methods=["GET", "POST"])
    def admin_control_add():
        """Add a new DER Control."""
        if request.method == "POST":
            # Build DERControl from form data
            control = m.DERControl()
            control.description = request.form.get("description", "")

            mrid = request.form.get("mRID")
            if mrid:
                control.mRID = mrid

            # Set interval
            start_time = request.form.get("startTime")
            duration = request.form.get("duration")
            if start_time or duration:
                control.interval = m.DateTimeInterval()
                if start_time:
                    dt = datetime.fromisoformat(start_time)
                    control.interval.start = int(dt.timestamp())
                if duration:
                    control.interval.duration = int(duration)

            # Set randomization
            randomize_start = request.form.get("randomizeStart")
            if randomize_start:
                control.randomizeStart = int(randomize_start)

            randomize_duration = request.form.get("randomizeDuration")
            if randomize_duration:
                control.randomizeDuration = int(randomize_duration)

            # Set DERControlBase
            control.DERControlBase = m.DERControlBase()

            set_max_w = request.form.get("setMaxW")
            if set_max_w:
                control.DERControlBase.setMaxW = m.ActivePower(multiplier=0, value=int(set_max_w))

            set_max_var = request.form.get("setMaxVar")
            if set_max_var:
                control.DERControlBase.setMaxVar = m.ReactivePower(multiplier=0, value=int(set_max_var))

            set_grad_w = request.form.get("setGradW")
            if set_grad_w:
                control.DERControlBase.setGradW = int(float(set_grad_w))

            op_mod_connect = request.form.get("opModConnect")
            if op_mod_connect:
                control.DERControlBase.opModConnect = op_mod_connect == "true"

            op_mod_energize = request.form.get("opModEnergize")
            if op_mod_energize:
                control.DERControlBase.opModEnergize = op_mod_energize == "true"

            # Add the control
            control = adpt.DERControlAdapter.add(control)

            return redirect(url_for("admin_control_list"))

        # GET: Show form
        return render_template("admin/control-form.html", control=None, start_time=None)

    @app.route("/admin/controls/<int:control_id>/edit", methods=["GET", "POST"])
    def admin_control_edit(control_id: int):
        """Edit an existing DER Control."""
        if request.method == "POST":
            # Get existing control
            control = adpt.DERControlAdapter.fetch(control_id)

            # Update fields
            control.description = request.form.get("description", control.description)

            # Update interval
            start_time = request.form.get("startTime")
            duration = request.form.get("duration")
            if start_time or duration:
                if not control.interval:
                    control.interval = m.DateTimeInterval()
                if start_time:
                    dt = datetime.fromisoformat(start_time)
                    control.interval.start = int(dt.timestamp())
                if duration:
                    control.interval.duration = int(duration)

            # Update DERControlBase
            if not control.DERControlBase:
                control.DERControlBase = m.DERControlBase()

            set_max_w = request.form.get("setMaxW")
            if set_max_w:
                control.DERControlBase.setMaxW = m.ActivePower(multiplier=0, value=int(set_max_w))

            set_max_var = request.form.get("setMaxVar")
            if set_max_var:
                control.DERControlBase.setMaxVar = m.ReactivePower(multiplier=0, value=int(set_max_var))

            # Save
            adpt.DERControlAdapter.put(control_id, control)

            return redirect(url_for("admin_control_list"))

        # GET: Show form with existing data
        control = adpt.DERControlAdapter.fetch(control_id)

        # Convert timestamp to datetime string for form
        start_time = None
        if control and control.interval and control.interval.start:
            start_time = datetime.fromtimestamp(control.interval.start).strftime("%Y-%m-%dT%H:%M")

        return render_template("admin/control-form.html", control=control, start_time=start_time)

    @app.route("/admin/controls/save", methods=["POST"])
    def admin_control_save():
        """Save DER Control (redirect target for form)."""
        href = request.form.get("href")

        if href:
            control_id = int(href.rsplit("/", 1)[-1])
            return redirect(url_for("admin_control_edit", control_id=control_id), code=307)
        else:
            return redirect(url_for("admin_control_add"), code=307)

    # DER Curve Management Routes
    @app.route("/admin/curves/list")
    def admin_curve_list():
        """List all DER Curves."""
        start = int(request.args.get("s", 0))
        limit = int(request.args.get("l", 100))
        curves = adpt.DERCurveAdapter.fetch_all(m.DERCurveList(), start=start, limit=limit)
        return render_template("admin/curves-list.html", curves=curves)

    @app.route("/admin/curves/add", methods=["GET", "POST"])
    def admin_curve_add():
        """Add a new DER Curve."""
        if request.method == "POST":
            # Build DERCurve from form data
            curve = m.DERCurve()
            curve.description = request.form.get("description", "")

            curve_type = request.form.get("curveType")
            if curve_type:
                curve.curveType = int(curve_type)

            # Collect curve data points
            curve.CurveData = []
            i = 0
            while True:
                x_val = request.form.get(f"x_{i}")
                y_val = request.form.get(f"y_{i}")
                if x_val is None and y_val is None:
                    break
                if x_val or y_val:
                    curve_data = m.CurveData()
                    curve_data.xvalue = int(float(x_val)) if x_val else 0
                    curve_data.yvalue = int(float(y_val)) if y_val else 0
                    curve.CurveData.append(curve_data)
                i += 1

            # Timing parameters
            open_loop = request.form.get("openLoopTms")
            if open_loop:
                curve.openLoopTms = int(open_loop)

            ramp_dec = request.form.get("rampDecTms")
            if ramp_dec:
                curve.rampDecTms = int(ramp_dec)

            ramp_inc = request.form.get("rampIncTms")
            if ramp_inc:
                curve.rampIncTms = int(ramp_inc)

            ramp_pt1 = request.form.get("rampPT1Tms")
            if ramp_pt1:
                curve.rampPT1Tms = int(ramp_pt1)

            # Multipliers
            x_mult = request.form.get("xMultiplier")
            if x_mult:
                curve.xMultiplier = int(x_mult)

            y_mult = request.form.get("yMultiplier")
            if y_mult:
                curve.yMultiplier = int(y_mult)

            # Add the curve
            curve = adpt.DERCurveAdapter.add(curve)

            return redirect(url_for("admin_curve_list"))

        # GET: Show form
        return render_template("admin/curve-form.html", curve=None)

    @app.route("/admin/curves/<int:curve_id>/edit", methods=["GET", "POST"])
    def admin_curve_edit(curve_id: int):
        """Edit an existing DER Curve."""
        if request.method == "POST":
            # Get existing curve
            curve = adpt.DERCurveAdapter.fetch(curve_id)

            # Update fields
            curve.description = request.form.get("description", curve.description)

            curve_type = request.form.get("curveType")
            if curve_type:
                curve.curveType = int(curve_type)

            # Update curve data points
            curve.CurveData = []
            i = 0
            while True:
                x_val = request.form.get(f"x_{i}")
                y_val = request.form.get(f"y_{i}")
                if x_val is None and y_val is None:
                    break
                if x_val or y_val:
                    curve_data = m.CurveData()
                    curve_data.xvalue = int(float(x_val)) if x_val else 0
                    curve_data.yvalue = int(float(y_val)) if y_val else 0
                    curve.CurveData.append(curve_data)
                i += 1

            # Update timing parameters
            open_loop = request.form.get("openLoopTms")
            if open_loop:
                curve.openLoopTms = int(open_loop)

            ramp_dec = request.form.get("rampDecTms")
            if ramp_dec:
                curve.rampDecTms = int(ramp_dec)

            # Save
            adpt.DERCurveAdapter.put(curve_id, curve)

            return redirect(url_for("admin_curve_list"))

        # GET: Show form with existing data
        curve = adpt.DERCurveAdapter.fetch(curve_id)
        return render_template("admin/curve-form.html", curve=curve)

    @app.route("/admin/curves/save", methods=["POST"])
    def admin_curve_save():
        """Save DER Curve (redirect target for form)."""
        href = request.form.get("href")

        if href:
            curve_id = int(href.rsplit("/", 1)[-1])
            return redirect(url_for("admin_curve_edit", curve_id=curve_id), code=307)
        else:
            return redirect(url_for("admin_curve_add"), code=307)

    @app.route("/admin/resources")
    def admin_resource_list():
        resource = request.args.get("rurl")
        obj = get_href(resource)
        all_resources = sorted(get_href_all_names())
        if obj:
            return render_template(
                "admin/resource_list.html",
                resource_urls=all_resources,
                href_shown=resource,
                object=dataclass_to_xml(obj),
            )
        else:
            return render_template("admin/resource_list.html", resource_urls=all_resources)

    @app.route("/admin/clients")
    def admin_clients():
        clients = tlsrepo.client_list
        return render_template("admin/clients.html", registered=clients, connected=[])

    @app.route("/admin/clients/dcap/<int:index>")
    def admin_clients_dcap(index: int = hrefs.NO_INDEX):
        clients = tlsrepo.client_list
        return render_template("admin/clients.html", registered=clients, connected=[])

    @app.route("/admin/routes")
    def admin_routes():
        routes = "<ul>"
        for p in app.url_map.iter_rules():
            routes += f"<li>{p.rule}</li>"
        routes += "</ul>"
        return Response(f"{routes}")

    @app.route("/admin/performance")
    def admin_performance():
        """Performance monitoring dashboard endpoint."""
        try:
            # Get monitoring data from the point store
            from ieee_2030_5.persistance.points import get_db

            monitoring_data = None
            db = get_db()
            if hasattr(db, "get_monitoring_data"):
                monitoring_data = db.get_monitoring_data()

            return render_template(
                "admin/performance.html", monitoring_data=monitoring_data, current_time=datetime.now().isoformat()
            )
        except Exception as e:
            _log.error(f"Error in performance endpoint: {e}")
            return Response(f"Error: {e}", status=500)

    @app.route("/api/monitoring")
    def api_monitoring():
        """JSON API endpoint for monitoring data (for graphs/dashboards)."""
        try:
            # Get monitoring data from the point store
            from ieee_2030_5.persistance.points import get_db

            db = get_db()
            if hasattr(db, "get_monitoring_data"):
                data = db.get_monitoring_data()
                return Response(json.dumps(data, indent=2, default=str), mimetype="application/json")
            else:
                return Response(
                    json.dumps(
                        {"error": "Point store monitoring not available", "timestamp": datetime.now().isoformat()}
                    ),
                    mimetype="application/json",
                    status=503,
                )
        except Exception as e:
            _log.error(f"Error in monitoring API: {e}")
            return Response(
                json.dumps({"error": str(e), "timestamp": datetime.now().isoformat()}),
                mimetype="application/json",
                status=500,
            )

    @app.route("/api/monitoring/reset", methods=["POST"])
    def api_monitoring_reset():
        """Reset performance statistics."""
        try:
            from ieee_2030_5.persistance.points import get_db

            db = get_db()
            if hasattr(db, "reset_stats"):
                db.reset_stats()
                return Response(
                    json.dumps(
                        {
                            "success": True,
                            "message": "Statistics reset successfully",
                            "timestamp": datetime.now().isoformat(),
                        }
                    ),
                    mimetype="application/json",
                )
            else:
                return Response(
                    json.dumps(
                        {"error": "Point store monitoring not available", "timestamp": datetime.now().isoformat()}
                    ),
                    mimetype="application/json",
                    status=503,
                )
        except Exception as e:
            _log.error(f"Error resetting monitoring stats: {e}")
            return Response(
                json.dumps({"error": str(e), "timestamp": datetime.now().isoformat()}),
                mimetype="application/json",
                status=500,
            )

    @app.route("/admin/message-bus")
    def admin_message_bus():
        """GridAPPS-D message bus traffic monitoring dashboard."""
        return render_template("admin/message_bus.html", current_time=datetime.now().isoformat())

    @app.route("/api/message-bus/events")
    def api_message_bus_events():
        """Server-Sent Events stream for real-time message bus traffic."""

        def generate_events():
            from ieee_2030_5.monitoring import get_message_monitor

            monitor = get_message_monitor()

            # Send initial messages
            recent_messages = monitor.get_recent_messages(50)  # Last 50 messages
            for msg in recent_messages:
                yield f"data: {json.dumps(msg.to_dict())}\n\n"

            # Set up real-time subscription
            message_queue = queue.Queue(maxsize=100)

            def message_callback(event):
                try:
                    message_queue.put(event, block=False)
                except queue.Full:
                    pass  # Drop messages if queue is full

            monitor.subscribe(message_callback)

            try:
                while True:
                    try:
                        # Wait for new messages with timeout
                        event = message_queue.get(timeout=30)  # 30 second keepalive
                        yield f"data: {json.dumps(event.to_dict())}\n\n"
                    except queue.Empty:
                        # Send keepalive
                        yield f'data: {{"type":"keepalive","timestamp":"{datetime.now().isoformat()}"}}\n\n'
            finally:
                monitor.unsubscribe(message_callback)

        return Response(generate_events(), mimetype="text/event-stream", headers={"Cache-Control": "no-cache"})

    @app.route("/api/message-bus/stats")
    def api_message_bus_stats():
        """Get message bus monitoring statistics."""
        try:
            from ieee_2030_5.monitoring import get_message_monitor

            monitor = get_message_monitor()
            stats = monitor.get_stats()
            return Response(json.dumps(stats, indent=2, default=str), mimetype="application/json")
        except Exception as e:
            _log.error(f"Error getting message bus stats: {e}")
            return Response(
                json.dumps({"error": str(e), "timestamp": datetime.now().isoformat()}),
                mimetype="application/json",
                status=500,
            )

    @app.route("/api/message-bus/search")
    def api_message_bus_search():
        """Search message bus traffic."""
        try:
            query = request.args.get("q", "")
            topic_filter = request.args.get("topic", None)

            from ieee_2030_5.monitoring import get_message_monitor

            monitor = get_message_monitor()
            results = monitor.search_messages(query, topic_filter)

            return Response(
                json.dumps([msg.to_dict() for msg in results], indent=2, default=str), mimetype="application/json"
            )
        except Exception as e:
            _log.error(f"Error searching messages: {e}")
            return Response(
                json.dumps({"error": str(e), "timestamp": datetime.now().isoformat()}),
                mimetype="application/json",
                status=500,
            )

    @app.route("/api/message-bus/clear", methods=["POST"])
    def api_message_bus_clear():
        """Clear message bus traffic history."""
        try:
            from ieee_2030_5.monitoring import get_message_monitor

            monitor = get_message_monitor()
            monitor.clear_messages()
            return Response(
                json.dumps(
                    {"success": True, "message": "Message history cleared", "timestamp": datetime.now().isoformat()}
                ),
                mimetype="application/json",
            )
        except Exception as e:
            _log.error(f"Error clearing messages: {e}")
            return Response(
                json.dumps({"error": str(e), "timestamp": datetime.now().isoformat()}),
                mimetype="application/json",
                status=500,
            )

    @app.route("/api/message-bus/toggle", methods=["POST"])
    def api_message_bus_toggle():
        """Toggle message bus monitoring on/off."""
        try:
            from ieee_2030_5.monitoring import get_message_monitor

            monitor = get_message_monitor()

            if monitor.is_enabled():
                monitor.disable()
                status = "disabled"
            else:
                monitor.enable()
                status = "enabled"

            return Response(
                json.dumps({"success": True, "status": status, "timestamp": datetime.now().isoformat()}),
                mimetype="application/json",
            )
        except Exception as e:
            _log.error(f"Error toggling message monitoring: {e}")
            return Response(
                json.dumps({"error": str(e), "timestamp": datetime.now().isoformat()}),
                mimetype="application/json",
                status=500,
            )

    return app


class HTTP11WSGIServer(BaseWSGIServer):
    """WSGI server that forces HTTP/1.1 protocol."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure the handler class knows to use HTTP/1.1
        self.protocol_version = "HTTP/1.1"

    def server_bind(self):
        # Set TCP socket options before binding
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Enable TCP keep-alive
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        # Bind the socket
        super().server_bind()


def run_app(app: Flask, host, ssl_context, request_handler, port, **kwargs):
    exclude_patterns = ["data_store/**", "docs/**", "examples/**", "logs/**"]
    app.run(
        host=host,
        ssl_context=ssl_context,
        request_handler=request_handler,
        port=port,
        exclude_patterns=exclude_patterns,
        **kwargs,
    )


def run_dual_server(config: ServerConfiguration, tlsrepo: TLSRepository, admin_http_port: int = 5001, **kwargs):
    """Run both HTTPS server (for IEEE 2030.5 API) and HTTP server (for admin only)"""
    global server_config, tls_repository
    server_config = config
    tls_repository = tlsrepo

    # Build the main app
    app = __build_app__(config, tlsrepo)

    # Parse main server configuration
    try:
        host, port = config.server_hostname.split(":")
        port = int(port)
    except ValueError:
        host = config.server_hostname
        port = 8443

    # Set up request handler
    IEEE2030_5_RequestHandler.config = config
    IEEE2030_5_RequestHandler.tlsrepo = tlsrepo

    # Create SSL context for HTTPS server
    ssl_context = __build_ssl_context__(tlsrepo) if not config.lfdi_client else None

    def start_https_server():
        """Start the main HTTPS server for IEEE 2030.5 API"""
        _log.info(f"Starting HTTPS server on {host}:{port}")
        run_app(
            app=app, host=host, ssl_context=ssl_context, port=port, request_handler=IEEE2030_5_RequestHandler, **kwargs
        )

    def start_http_admin_server():
        """Start HTTP server for admin access only"""
        # Use the same Flask app but different server (simpler approach)
        # Bind HTTP admin server to all interfaces for convenience
        # This will allow the same routes to be accessible via both HTTPS and HTTP

        admin_host = "0.0.0.0"  # Allow access from any interface for HTTP admin
        _log.info(f"Starting HTTP admin server on {admin_host}:{admin_http_port}")
        run_simple(
            admin_host, admin_http_port, app, threaded=True, use_reloader=False, use_debugger=kwargs.get("debug", False)
        )

    # Start both servers in separate threads
    https_thread = threading.Thread(target=start_https_server, daemon=True)
    http_thread = threading.Thread(target=start_http_admin_server, daemon=True)

    https_thread.start()
    http_thread.start()

    # Wait for both threads
    try:
        https_thread.join()
    except KeyboardInterrupt:
        _log.info("Shutting down dual servers")
        raise


def run_server(config: ServerConfiguration, tlsrepo: TLSRepository, **kwargs):
    global server_config, tls_repository
    server_config = config
    tls_repository = tlsrepo

    app = __build_app__(config, tlsrepo)

    ssl_context = None
    # If lfd_client is specified then we are running in http mode so we don'
    # establish an sslcontext.
    if not config.lfdi_client:
        ssl_context = __build_ssl_context__(tlsrepo)

    try:
        host, port = config.server_hostname.split(":")
    except ValueError:
        # host and port not available
        host = config.server_hostname
        port = 8443

    IEEE2030_5_RequestHandler.config = config
    IEEE2030_5_RequestHandler.tlsrepo = tlsrepo

    # PeerCertWSGIRequestHandler.config = config
    # PeerCertWSGIRequestHandler.tlsrepo = tlsrepo

    run_app(app=app, host=host, ssl_context=ssl_context, port=port, request_handler=IEEE2030_5_RequestHandler, **kwargs)


def build_server(config: ServerConfiguration, tlsrepo: TLSRepository, **kwargs) -> BaseWSGIServer:
    """Build and configure the IEEE 2030.5 server"""
    global server_config, tls_repository
    server_config = config
    tls_repository = tlsrepo

    # Create debug directory for client traffic logs if debug is enabled
    if getattr(config, "debug_client_traffic", False):
        debug_dir = Path("debug_client_traffic")
        debug_dir.mkdir(exist_ok=True)
        _log.info(f"Client traffic debugging enabled. Logs will be written to {debug_dir}")

    # Build the Flask application
    app = __build_app__(config, tlsrepo)

    # Set HTTP/1.1 as the protocol version
    app.config["PROTOCOL_VERSION"] = "HTTP/1.1"

    # Configure SSL context
    ssl_context = __build_ssl_context__(tlsrepo)

    # Parse host and port
    try:
        host, port = config.server_hostname.split(":")
    except ValueError:
        host = config.server_hostname
        port = 8443

    # Configure the request handler
    IEEE2030_5_RequestHandler.config = config
    IEEE2030_5_RequestHandler.tlsrepo = tlsrepo

    # Build custom server options
    server_kwargs = {
        "app": app,
        "host": host,
        "port": int(port),
        "request_handler": IEEE2030_5_RequestHandler,
        "ssl_context": ssl_context,
        "threaded": True,
        "passthrough_errors": False,
    }

    # Add any additional kwargs
    server_kwargs.update(kwargs)

    # Create our custom server
    server = IEEE2030_5_Server(**server_kwargs)

    # Initialize the connection manager
    if not hasattr(app, "connection_manager"):
        connection_manager = ConnectionManager(idle_timeout=getattr(config, "connection_idle_timeout", 300))
        connection_manager.start()
        app.connection_manager = connection_manager

        # Register shutdown handler
        def shutdown_server():
            if hasattr(app, "connection_manager"):
                app.connection_manager.stop()
                app.connection_manager.join(timeout=5)

            with IEEE2030_5_RequestHandler.connection_lock:
                for info in IEEE2030_5_RequestHandler.active_connections.values():
                    try:
                        info["connection"].close()
                    except:
                        pass
                IEEE2030_5_RequestHandler.active_connections.clear()

        atexit.register(shutdown_server)

    return server


def make_app(config_file: Path, reset_certs: bool) -> Flask:
    config = ServerConfiguration.load(config_file)
    tlsrepo = TLSRepository(
        config.tls_repository,
        clear=reset_certs,
        openssl_cnffile_template=config.openssl_cnf,
        serverhost=config.server_hostname,
    )
    app = __build_app__(config, tlsrepo)
    return app
