import hashlib
import itertools
import json
import logging
import os
import socket
import ssl
import threading
import time
from datetime import datetime
from dataclasses import fields
from functools import lru_cache
from pathlib import Path
from queue import Queue
import uuid

import OpenSSL
import werkzeug.exceptions
from flask import (Flask, Response, g, redirect, render_template, request, url_for)
from flask_session import Session
# from flask_socketio import SocketIO, send
from werkzeug.serving import BaseWSGIServer, make_server

from ieee_2030_5.utils import dataclass_to_xml

__all__ = ["build_server"]

import ieee_2030_5.adapters as adpt
import ieee_2030_5.hrefs as hrefs
import ieee_2030_5.models as m
from ieee_2030_5.certs import (TLSRepository, lfdi_from_fingerprint, sfdi_from_lfdi)
# templates = Jinja2Templates(directory="templates")
from ieee_2030_5.config import ServerConfiguration
from ieee_2030_5.data.indexer import get_href, get_href_all_names
from ieee_2030_5.models import DeviceCategoryType
from ieee_2030_5.server.admin_endpoints import AdminEndpoints
#from ieee_2030_5.server.server_constructs import EndDevices, get_groups
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
    http_handler = logging.FileHandler('logs/http_debug.log')
    http_handler.setLevel(logging.DEBUG)

    # Create formatter with detailed information
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] [%(thread)d] %(message)s')
    http_handler.setFormatter(formatter)

    # Add handler to the logger
    _log_http.setLevel(logging.DEBUG)
    _log_http.addHandler(http_handler)

def log_socket_info(server):
    """Log socket options for debugging"""
    try:
        socket_opts = {}
        for opt_name in ['SO_KEEPALIVE', 'SO_REUSEADDR', 'SO_RCVBUF', 'SO_SNDBUF']:
            if hasattr(socket, opt_name):
                opt_val = getattr(socket, opt_name)
                try:
                    socket_opts[opt_name] = server.socket.getsockopt(socket.SOL_SOCKET, opt_val)
                except:
                    socket_opts[opt_name] = "Error getting option"

        # Try to get TCP keep-alive parameters if available
        if hasattr(socket, "TCP_KEEPIDLE"):
            try:
                socket_opts["TCP_KEEPIDLE"] = server.socket.getsockopt(
                    socket.IPPROTO_TCP, socket.TCP_KEEPIDLE)
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
                idle_time = now - info['last_activity']
                if idle_time > self.idle_timeout:
                    to_close.append((conn_id, info))

        # Close connections outside the lock to avoid deadlocks
        for conn_id, info in to_close:
            try:
                _log.info(f"Closing idle connection from {info['client_address']} "
                          f"after {self.idle_timeout}s of inactivity")
                info['connection'].close()

                with IEEE2030_5_RequestHandler.connection_lock:
                    if conn_id in IEEE2030_5_RequestHandler.active_connections:
                        del IEEE2030_5_RequestHandler.active_connections[conn_id]

            except Exception as e:
                _log.warning(f"Error closing idle connection: {e}")

    def stop(self):
        self.running = False


class IEEE2030_5_RequestHandler(werkzeug.serving.WSGIRequestHandler):
    """Request handler that properly manages HTTP/1.1 persistent connections."""

    protocol_version = 'HTTP/1.1'  # Force HTTP/1.1
    connection_lock = threading.Lock()
    active_connections = {}

    @staticmethod
    @lru_cache
    def is_admin(path_info) -> bool:
        start_paths = ['/admin', '/socket-io']
        a_filter = itertools.accumulate(start_paths,
                                        lambda x: 1 if path_info.startswith(x) else 0,
                                        initial=0)
        return next(a_filter) > 0

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

        # Check admin access early
        if IEEE2030_5_RequestHandler.is_admin(environ['PATH_INFO']):
            if not self.config.generate_admin_cert:
                raise werkzeug.exceptions.Forbidden()
            return self._setup_admin_environ(environ)

        # Handle LFDI client mode (HTTP without certificates)
        if self.config.lfdi_client:
            return self._setup_lfdi_client_environ(environ)

        try:
            # Load certificate from various sources
            x509 = self._load_client_certificate(environ)

            # Set up certificate environment variables
            environ['ieee_2030_5_peercert'] = x509
            environ['ieee_2030_5_serial_number'] = x509.get_serial_number()

            # Calculate LFDI and SFDI
            self._calculate_device_identifiers(environ, x509)

            # Verify device is known (for non-admin requests)
            self._verify_device_authorization(environ)

        except OpenSSL.crypto.Error as e:
            _log.warning(f"Certificate error: {e}")
            environ['peercert'] = None
        except Exception as e:
            _log.error(f"Unexpected error in make_environ: {e}")
            raise

        return environ

    def _setup_admin_environ(self, environ):
        """Setup environment for admin requests"""
        try:
            cert, key = self.tlsrepo.get_file_pair("admin")
            x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert)
            environ['ieee_2030_5_peercert'] = x509
            environ['ieee_2030_5_serial_number'] = x509.get_serial_number()
            self._calculate_device_identifiers(environ, x509)
            return environ
        except Exception as e:
            _log.error(f"Failed to setup admin environment: {e}")
            raise werkzeug.exceptions.InternalServerError("Admin certificate setup failed")

    def _setup_lfdi_client_environ(self, environ):
        """Setup environment for LFDI client mode (HTTP without certificates)"""
        environ['ieee_2030_5_lfdi'] = self.config.lfdi_client
        environ['ieee_2030_5_sfdi'] = sfdi_from_lfdi(self.config.lfdi_client)
        return environ

    def _load_client_certificate(self, environ):
        """Load client certificate from proxy headers or direct TLS connection"""
        # Try proxy headers first (with validation)
        if 'HTTP_SSL_CLIENT_CERT' in environ or 'SSL_CLIENT_CERT' in environ:
            return self._load_certificate_from_proxy_headers(environ)

        # Fall back to direct TLS connection
        return self._load_certificate_from_connection()

    def _load_certificate_from_proxy_headers(self, environ):
        """Load and validate certificate from proxy headers"""
        cert_header = 'HTTP_SSL_CLIENT_CERT' if 'HTTP_SSL_CLIENT_CERT' in environ else 'SSL_CLIENT_CERT'
        _log.debug(f"Using {cert_header} from proxy header")

        cert_pem = environ[cert_header]
        _log.debug(f"Raw certificate from proxy: {cert_pem[:50]}...")

        # Handle certificate format - proxy may send it as a single line with spaces
        if cert_pem.startswith('-----BEGIN CERTIFICATE-----') and '-----END CERTIFICATE-----' in cert_pem:
            # Certificate is in single-line format, need to properly format it
            if '\n' not in cert_pem:
                _log.debug("Converting single-line certificate to proper PEM format")
                # Split on the certificate boundaries and base64 content
                parts = cert_pem.split('-----BEGIN CERTIFICATE-----')
                if len(parts) == 2:
                    remaining = parts[1].split('-----END CERTIFICATE-----')
                    if len(remaining) == 2:
                        base64_content = remaining[0].strip()
                        # Remove any spaces from the base64 content and reformat
                        base64_content = base64_content.replace(' ', '')
                        # Add newlines every 64 characters for proper PEM format
                        formatted_lines = []
                        for i in range(0, len(base64_content), 64):
                            formatted_lines.append(base64_content[i:i+64])

                        cert_pem = '-----BEGIN CERTIFICATE-----\n' + '\n'.join(formatted_lines) + '\n-----END CERTIFICATE-----'
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
        if 'HTTP_SSL_CLIENT_S_DN' in environ:
            expected_subject = str(x509.get_subject())
            provided_subject = environ['HTTP_SSL_CLIENT_S_DN']
            if expected_subject != provided_subject:
                _log.warning(f"Subject DN mismatch: expected {expected_subject}, got {provided_subject}")

        if 'HTTP_SSL_CLIENT_SERIAL' in environ:
            expected_serial = str(x509.get_serial_number())
            provided_serial = environ['HTTP_SSL_CLIENT_SERIAL']
            if expected_serial != provided_serial:
                _log.warning(f"Serial number mismatch: expected {expected_serial}, got {provided_serial}")

        if 'HTTP_SSL_CLIENT_FINGERPRINT' in environ:
            expected_fingerprint = x509.digest("sha256").decode('ascii')
            provided_fingerprint = environ['HTTP_SSL_CLIENT_FINGERPRINT']
            if expected_fingerprint != provided_fingerprint:
                _log.warning(f"Fingerprint mismatch: expected {expected_fingerprint}, got {provided_fingerprint}")

    def _calculate_device_identifiers(self, environ, x509):
        """Calculate LFDI and SFDI from certificate"""
        if IEEE2030_5_RequestHandler.config.lfdi_mode == "lfdi_mode_from_file":
            _log.debug("Using hash from combined file")
            try:
                pth = IEEE2030_5_RequestHandler.tlsrepo.__get_combined_file__(x509.get_subject().CN)
                sha256hash = hashlib.sha256(pth.read_text().encode('utf-8')).hexdigest()
                environ['ieee_2030_5_lfdi'] = lfdi_from_fingerprint(sha256hash)
            except Exception as e:
                _log.error(f"Failed to read combined file for {x509.get_subject().CN}: {e}")
                raise
        else:
            environ['ieee_2030_5_lfdi'] = lfdi_from_fingerprint(x509.digest("sha256").decode('ascii'))

        environ['ieee_2030_5_sfdi'] = sfdi_from_lfdi(environ['ieee_2030_5_lfdi'])

        _log.debug(f"Environment lfdi: {environ['ieee_2030_5_lfdi']} sfdi: {environ['ieee_2030_5_sfdi']}")

    def _verify_device_authorization(self, environ):
        """Verify that the device is authorized to access the server"""
        # Skip verification for admin requests
        if IEEE2030_5_RequestHandler.is_admin(environ['PATH_INFO']):
            return

        # Only verify in certificate fingerprint mode
        if IEEE2030_5_RequestHandler.config.lfdi_mode != "lfdi_mode_from_cert_fingerprint":
            _log.debug("Skipping device verification - not in cert fingerprint mode")
            return

        # Look up device in TLS repository
        found_device_id = self.tlsrepo.find_device_id_from_sfdi(environ['ieee_2030_5_sfdi'])
        if not found_device_id:
            _log.warning(
                f"Unknown device with SFDI: {environ['ieee_2030_5_sfdi']} "
                f"from {self.client_address}"
            )
            raise werkzeug.exceptions.Forbidden("Unknown device certificate")

        _log.debug(f"Verified device id: {found_device_id}")
        environ['ieee_2030_5_device_id'] = found_device_id


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
                'connection': self.connection,
                'last_activity': time.time(),
                'client_address': self.client_address
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
            connection_header = self.headers.get('Connection', '').lower()

            # Log request
            _log.debug(f"Request: {self.command} {self.path} {self.request_version}")
            _log.debug(f"Connection header: {connection_header}")

            # Process the request
            handler = getattr(self, f'do_{self.command}', self.do_GET)
            handler()
            self.wfile.flush()

            # For HTTP/1.1, persistent is default unless 'Connection: close'
            if self.request_version >= 'HTTP/1.1' and 'close' not in connection_header:
                self.close_connection = False
                _log.debug(f"HTTP/1.1 default keep-alive for {self.client_address}")
            # For HTTP/1.0 with keep-alive header
            elif 'keep-alive' in connection_header:
                self.close_connection = False
                _log.debug(f"Explicit keep-alive for {self.client_address}")
            # Otherwise close
            else:
                self.close_connection = True
                _log.debug(f"Connection will close for {self.client_address}")

        except socket.timeout:
            # Timeout reading from socket - close connection
            _log.debug(f"Socket timeout from {self.client_address}")
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
        self.send_header('Server', 'IEEE2030_5/1.0')
        self.send_header('Date', self.date_time_string())

        # Add keep-alive headers unless we're closing the connection
        if not self.close_connection:
            self.send_header('Connection', 'keep-alive')
            self.send_header('Keep-Alive', 'timeout=300, max=1000')


class IEEE2030_5_Server(BaseWSGIServer):
    """Custom WSGI server with optimizations for IEEE 2030.5"""

    def __init__(self, host, port, app, **kwargs):
        super().__init__(host, port, app, **kwargs)
        self.protocol_version = 'HTTP/1.1'

    def server_bind(self):
        """Set socket options when binding the server socket"""
        # Set socket options for performance
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

        # Set TCP keep-alive options if available
        # These are platform-specific, so use try/except
        try:
            # Linux-specific options
            if hasattr(socket, 'TCP_KEEPIDLE'):
                self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60)
            if hasattr(socket, 'TCP_KEEPINTVL'):
                self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10)
            if hasattr(socket, 'TCP_KEEPCNT'):
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
        socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 6)     # Consider dead after 6 failures
# based on
# https://stackoverflow.com/questions/19459236/how-to-handle-413-request-entity-too-large-in-python-flask-server#:~:text=server%20MAY%20close%20the%20connection,client%20from%20continuing%20the%20request.&text=time%20the%20client%20MAY%20try,you%20the%20Broken%20pipe%20error.&text=Great%20than%20the%20application%20is%20acting%20correct.
def log_client_request(lfdi: str, request_id: str, cn: str = None):
    """Log incoming request details to client-specific file"""
    debug_dir = Path('debug_client_traffic')
    
    # Ensure the debug directory exists
    debug_dir.mkdir(exist_ok=True)
    
    # Use CN for filename if available, otherwise fall back to LFDI
    # Sanitize the filename to remove any invalid characters
    safe_name = cn if cn else lfdi
    safe_name = safe_name.replace('/', '_').replace('\\', '_').replace(':', '_')
    filename = f"client_{safe_name}.log"
    client_file = debug_dir / filename
    
    timestamp = datetime.now().isoformat()
    
    request_data = {
        'timestamp': timestamp,
        'request_id': request_id,
        'type': 'REQUEST',
        'lfdi': lfdi,
        'cn': cn,
        'method': request.method,
        'path': request.path,
        'query_string': request.query_string.decode('utf-8') if request.query_string else '',
        'headers': dict(request.headers),
        'remote_addr': request.remote_addr,
        'content_length': request.content_length,
        'content_type': request.content_type,
        'body': None
    }
    
    # Try to get request body if present
    if request.content_length and request.content_length > 0:
        try:
            # Get the raw data and restore it for the actual request handler
            body_data = request.get_data(as_text=True)
            request_data['body'] = body_data
        except Exception as e:
            request_data['body_error'] = str(e)
    
    # Write to file with error handling
    try:
        with open(client_file, 'a') as f:
            f.write(json.dumps(request_data, indent=2) + '\n\n')
    except Exception as e:
        _log.error(f"Failed to write request log for {safe_name}: {e}")

def log_client_response(lfdi: str, request_id: str, response: Response, duration: float, cn: str = None):
    """Log outgoing response details to client-specific file"""
    debug_dir = Path('debug_client_traffic')
    
    # Ensure the debug directory exists
    debug_dir.mkdir(exist_ok=True)
    
    # Use CN for filename if available, otherwise fall back to LFDI
    # Sanitize the filename to remove any invalid characters
    safe_name = cn if cn else lfdi
    safe_name = safe_name.replace('/', '_').replace('\\', '_').replace(':', '_')
    filename = f"client_{safe_name}.log"
    client_file = debug_dir / filename
    
    timestamp = datetime.now().isoformat()
    
    response_data = {
        'timestamp': timestamp,
        'request_id': request_id,
        'type': 'RESPONSE',
        'lfdi': lfdi,
        'cn': cn,
        'status_code': response.status_code,
        'headers': dict(response.headers),
        'content_length': response.headers.get('Content-Length', 0),
        'content_type': response.headers.get('Content-Type', 'unknown'),
        'duration_seconds': duration,
        'body': None
    }
    
    # Try to get response body
    try:
        response_body = response.get_data(as_text=True)
        response_data['body'] = response_body
    except Exception as e:
        response_data['body_error'] = str(e)
    
    # Write to file with error handling
    try:
        with open(client_file, 'a') as f:
            f.write(json.dumps(response_data, indent=2) + '\n\n')
    except Exception as e:
        _log.error(f"Failed to write response log for {safe_name}: {e}")

def handle_chunking():
    """
    Sets the "wsgi.input_terminated" environment flag, thus enabling
    Werkzeug to pass chunked requests as streams.  The gunicorn server
    should set this, but it's not yet been implemented.
    """

    transfer_encoding = request.headers.get("Transfer-Encoding", None)
    if transfer_encoding == u"chunked":
        request.environ["wsgi.input_terminated"] = True


def before_request():

    g.SERVER_CONFIG = server_config
    g.TLS_REPOSITORY = tls_repository
    # Add request tracking
    g.start_time = time.time()
    g.request_id = str(uuid.uuid4())[:8]  # Generate short request ID for tracking

    # Log the incoming request details
    client_address = request.remote_addr
    method = request.method
    path = request.path
    protocol = request.environ.get('SERVER_PROTOCOL', '')

    # Log basic request info
    _log_http.info(f"[{g.request_id}] {client_address} - {method} {path} {protocol}")

    # Log detailed headers
    _log_http.debug(f"[{g.request_id}] Request Headers:")
    for name, value in request.headers.items():
        _log_http.debug(f"[{g.request_id}]   {name}: {value}")

    # Log Connection header specifically since it's important for keep-alive
    connection_header = request.headers.get('Connection', 'none')
    _log_http.info(f"[{g.request_id}] Connection header: {connection_header}")

    # Log client certificate info if available
    if 'ieee_2030_5_lfdi' in request.environ:
        _log_http.debug(f"[{g.request_id}] Client LFDI: {request.environ.get('ieee_2030_5_lfdi')}")
        
        # Client-specific debug logging to file
        lfdi = request.environ.get('ieee_2030_5_lfdi')
        if lfdi and getattr(server_config, 'debug_client_traffic', False):
            try:
                # Try to get CN from the certificate
                cn = None
                if 'ieee_2030_5_peercert' in request.environ:
                    try:
                        x509 = request.environ.get('ieee_2030_5_peercert')
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
    content_length = response.headers.get('Content-Length', 0)
    content_type = response.headers.get('Content-Type', 'unknown')

    # Log basic response info
    _log_http.info(f"[{g.request_id}] Response: {status_code} - {content_length} bytes - {content_type} ({duration:.3f}s)")

    # Add necessary headers for XML responses
    if 'Content-Type' not in response.headers:
        response.headers['Content-Type'] = 'application/sep+xml'

    # Force persistent connections for HTTP/1.1
    if request.environ.get('SERVER_PROTOCOL') == 'HTTP/1.1':
        response.headers['Connection'] = 'keep-alive'
        response.headers['Keep-Alive'] = 'timeout=300, max=1000'

    _log.debug(f"\nREQ: {request.path}")
    _log.debug(f"\nRESP HEADER: {str(response.headers).strip()}")
    resp = response.get_data().decode('utf-8')
    _log.debug(f"\nRESP: {resp}")
    
    # Client-specific debug logging to file
    lfdi = request.environ.get('ieee_2030_5_lfdi')
    if lfdi and getattr(server_config, 'debug_client_traffic', False):
        try:
            # Try to get CN from the certificate
            cn = None
            if 'ieee_2030_5_peercert' in request.environ:
                try:
                    x509 = request.environ.get('ieee_2030_5_peercert')
                    cn = x509.get_subject().CN if x509 else None
                except Exception as e:
                    _log.debug(f"Could not extract CN from certificate: {e}")
            log_client_response(lfdi, g.request_id, response, duration, cn)
        except Exception as e:
            _log.error(f"Failed to log client response: {e}")

    return response

    # Log response details
    status_code = response.status_code
    content_length = response.headers.get('Content-Length', 0)
    content_type = response.headers.get('Content-Type', 'unknown')

    # Log basic response info
    _log_http.info(f"[{g.request_id}] Response: {status_code} - {content_length} bytes - {content_type} ({duration:.3f}s)")

    # Log detailed response headers
    _log_http.debug(f"[{g.request_id}] Response Headers:")
    for name, value in response.headers.items():
        _log_http.debug(f"[{g.request_id}]   {name}: {value}")

    connection_header = request.headers.get('Connection', '').lower()
    if 'keep-alive' in connection_header:
        response.headers['Connection'] = 'keep-alive'
        response.headers['Keep-Alive'] = 'timeout=60, max=1000'

    _log.debug(f"\nREQ: {request.path}")
    _log.debug(f"\nRESP HEADER: {str(response.headers).strip()}")
    resp = response.get_data().decode('utf-8')
    _log.debug(f"\nRESP: {resp}")

    if request.environ.get('SERVER_PROTOCOL') == 'HTTP/1.1' and 'close' not in request.headers.get('Connection', '').lower():
        response.headers['Connection'] = 'keep-alive'
        response.headers['Keep-Alive'] = 'timeout=60, max=1000'
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
    if hasattr(ssl_context, 'session_cache_mode'):
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
    ssl_context.verify_mode = ssl.CERT_OPTIONAL    # ssl.CERT_REQUIRED
    # Enable session caching for TLS performance
    ssl_context.options |= ssl.OP_NO_TICKET
    # ssl_context.set_session_cache_mode(ssl.SESS_CACHE_SERVER)

    return ssl_context


def __build_http_app__(config: ServerConfiguration) -> Flask:
    app = Flask(__name__, template_folder=str(Path(".").resolve().joinpath('templates')))
    # Debug headers path and request arguments
    app.before_request(before_request)
    # Allows for larger data to be sent through because of chunking types.
    app.before_request(handle_chunking)
    app.after_request(after_request)

    @app.route("/dcap", methods=['GET'])
    def http_root() -> Response:
        return dataclass_to_xml(m.DeviceCapability(href=f"https://localhost:7443/dcap"))
        #return adpt.DeviceCapabilityAdapter()


def __build_app__(config: ServerConfiguration, tlsrepo: TLSRepository) -> Flask:
    app = Flask(__name__, template_folder=str(Path(".").resolve().joinpath('templates')))

    app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False

    # Force HTTP/1.1 responses
    app.config['SERVER_PROTOCOL'] = 'HTTP/1.1'

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
    @app.route('/')
    def root():
        return redirect("/admin/index.html")
        # cert = request.environ['peercert']
        # cert_data = f"{cert.get_subject()}"
        # return render_template("admin/index.html")
        # return render_template('helloworld.html', client_cert=request.environ['peercert'])

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
            return redirect("admin/index.html")

        controls, default_control = adpt.DERControlAdapter.get_all()
        return render_template("admin/add-fsa.html")

    @app.route("/admin/add-end-device", methods=["get", "post"])
    def admin_end_device():
        if request.method == "POST":
            return redirect(url_for("admin_home"))

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

        return render_template("admin/add-der-program.html",
                               der_controls=controls,
                               default_der_control=default_control)

    @app.route("/admin/default-der-control", methods=['get', 'post'])
    def admin_default_der_control():
        dderc = adpt.DERControlAdapter.fetch_default()

        if request.method == 'POST':
            kwargs = request.form.to_dict()
            # TODO: Build a helper that will allow us to populate by known form elements.
            # Helper for connect and energize mode, which are ready for usage.
            if 'enable_opModConnect' not in kwargs:
                kwargs['enable_opModConnect'] = 'off'

            if 'enable_opModEnergize' not in kwargs:
                kwargs['enable_opModEnergize'] = 'off'

            field_list = fields(dderc)
            base_control = dderc.DERControlBase
            for k, v in kwargs.items():
                if k.startswith('enable_'):
                    k = k.split('_')[1]
                    v = True if v == 'on' else False

                for f in field_list:
                    if k == f.name:
                        setattr(dderc, k, v)
                for f in fields(base_control):
                    if k == f.name:
                        setattr(base_control, k, v)

            adpt.DERControlAdapter.store_default(dderc=dderc)

            return redirect(url_for("admin_home"))

        return render_template("admin/update-default-der-control.html", dderc=dderc)

    @app.route("/admin/resources")
    def admin_resource_list():
        resource = request.args.get("rurl")
        obj = get_href(resource)
        all_resources = sorted(get_href_all_names())
        if obj:
            return render_template("admin/resource_list.html",
                                   resource_urls=all_resources,
                                   href_shown=resource,
                                   object=dataclass_to_xml(obj))
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
        routes = '<ul>'
        for p in app.url_map.iter_rules():
            routes += f"<li>{p.rule}</li>"
        routes += "</ul>"
        return Response(f"{routes}")

    return app

class HTTP11WSGIServer(BaseWSGIServer):
    """WSGI server that forces HTTP/1.1 protocol."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure the handler class knows to use HTTP/1.1
        self.protocol_version = 'HTTP/1.1'

    def server_bind(self):
        # Set TCP socket options before binding
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Enable TCP keep-alive
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        # Bind the socket
        super().server_bind()


def run_app(app: Flask, host, ssl_context, request_handler, port, **kwargs):
    exclude_patterns = ["data_store/**", "docs/**", "examples/**", "ieee_2030_5_gui/**", "logs/**"]
    app.run(host=host,
            ssl_context=ssl_context,
            request_handler=request_handler,
            port=port,
            exclude_patterns=exclude_patterns,
            **kwargs)


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

    #PeerCertWSGIRequestHandler.config = config
    #PeerCertWSGIRequestHandler.tlsrepo = tlsrepo

    run_app(app=app,
            host=host,
            ssl_context=ssl_context,
            port=port,
            request_handler=IEEE2030_5_RequestHandler,
            **kwargs)

def build_server(config: ServerConfiguration, tlsrepo: TLSRepository, **kwargs) -> BaseWSGIServer:
    """Build and configure the IEEE 2030.5 server"""
    global server_config, tls_repository
    server_config = config
    tls_repository = tlsrepo
    
    # Create debug directory for client traffic logs if debug is enabled
    if getattr(config, 'debug_client_traffic', False):
        debug_dir = Path('debug_client_traffic')
        debug_dir.mkdir(exist_ok=True)
        _log.info(f"Client traffic debugging enabled. Logs will be written to {debug_dir}")

    # Build the Flask application
    app = __build_app__(config, tlsrepo)

    # Set HTTP/1.1 as the protocol version
    app.config['PROTOCOL_VERSION'] = 'HTTP/1.1'

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
        'app': app,
        'host': host,
        'port': int(port),
        'request_handler': IEEE2030_5_RequestHandler,
        'ssl_context': ssl_context,
        'threaded': True,
        'passthrough_errors': False,
    }

    # Add any additional kwargs
    server_kwargs.update(kwargs)

    # Create our custom server
    server = IEEE2030_5_Server(**server_kwargs)

    # Initialize the connection manager
    if not hasattr(app, 'connection_manager'):
        connection_manager = ConnectionManager(
            idle_timeout=getattr(config, 'connection_idle_timeout', 300)
        )
        connection_manager.start()
        app.connection_manager = connection_manager

        # Register shutdown handler
        def shutdown_server():
            if hasattr(app, 'connection_manager'):
                app.connection_manager.stop()
                app.connection_manager.join(timeout=5)

            with IEEE2030_5_RequestHandler.connection_lock:
                for info in IEEE2030_5_RequestHandler.active_connections.values():
                    try:
                        info['connection'].close()
                    except:
                        pass
                IEEE2030_5_RequestHandler.active_connections.clear()

        atexit.register(shutdown_server)

    return server


def make_app(config_file: Path, reset_certs: bool) -> Flask:
    config = ServerConfiguration.load(config_file)
    tlsrepo = TLSRepository(config.tls_repository, clear=reset_certs, openssl_cnffile_template=config.openssl_cnf, serverhost=config.server_hostname)
    app = __build_app__(config, tlsrepo)
    return app
