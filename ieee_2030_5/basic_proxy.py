from __future__ import annotations
import logging
import os
import socket
import ssl
import threading
import traceback
from dataclasses import dataclass
from http.client import HTTPSConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Tuple
from urllib.parse import urlparse
import time
import OpenSSL
import yaml
from ieee_2030_5.certs import (TLSRepository, lfdi_from_fingerprint, sfdi_from_lfdi)
from ieee_2030_5.config import ServerConfiguration

# Create a custom formatter that includes file name and line number
class DetailedFormatter(logging.Formatter):
    def format(self, record):
        # Add file name and line number to the log message
        if hasattr(record, 'pathname'):
            record.file_info = f"{os.path.basename(record.pathname)}:{record.lineno}"
        else:
            record.file_info = "unknown:0"
        return super().format(record)

# Setup root logger with the detailed formatter
def setup_logging(debug=False):
    level = logging.DEBUG if debug else logging.INFO
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    console = logging.StreamHandler()
    console.setLevel(level)
    formatter = DetailedFormatter(
        '%(asctime)s - %(file_info)s - %(name)s - %(levelname)s - %(message)s'
    )
    console.setFormatter(formatter)
    root_logger.addHandler(console)

    return root_logger

_log = logging.getLogger(__name__)

@dataclass
class ContextWithPaths:
    context: ssl.SSLContext
    certpath: str
    keypath: str

class HTTPSConnectionWithTimeout(HTTPSConnection):
    """Extended HTTPSConnection with better error handling."""

    def __init__(self, *args, **kwargs):
        # Set reasonable timeouts
        self.timeout_connect = kwargs.pop('timeout_connect', 30)
        self.timeout_read = kwargs.pop('timeout_read', 30)

        # Save context explicitly as an instance attribute
        self.context = kwargs.get('context')

        _log.debug(
            f"Creating HTTPSConnection with timeouts: connect={self.timeout_connect}s, read={self.timeout_read}s"
        )
        super().__init__(*args, **kwargs)

    def connect(self):
        """Connect to the host and port specified in __init__."""
        _log.debug(f"Attempting to connect to {self.host}:{self.port}")
        try:
            # Use connect timeout
            self.sock = socket.create_connection((self.host, self.port), self.timeout_connect)
            _log.debug(f"Socket connected to {self.host}:{self.port}")

            if self._tunnel_host:
                _log.debug(f"Setting up tunnel to {self._tunnel_host}")
                self._tunnel()

            # Apply SSL context
            if hasattr(self, 'context') and self.context:
                _log.debug(f"Wrapping socket with provided SSL context")
                self.sock = self.context.wrap_socket(self.sock, server_hostname=self.host)
                _log.debug(
                    f"SSL handshake complete, cipher: {self.sock.cipher() if hasattr(self.sock, 'cipher') else 'unknown'}"
                )
            else:
                # Fallback to default SSL
                _log.debug(
                    f"Wrapping socket with default SSL (cert={self.cert_file}, key={self.key_file})"
                )
                self.sock = ssl.wrap_socket(self.sock,
                                            keyfile=self.key_file,
                                            certfile=self.cert_file)

            # Set socket read timeout
            self.sock.settimeout(self.timeout_read)
            _log.debug(f"Connection to {self.host}:{self.port} established successfully")

        except ssl.SSLError as e:
            _log.error(f"SSL Error connecting to {self.host}:{self.port}: {e}", exc_info=True)
            # Log SSL specific details if available
            if hasattr(e, 'verify_message'):
                _log.error(f"SSL verification error: {e.verify_message}")
            raise
        except socket.timeout:
            _log.error(
                f"Connection timeout to {self.host}:{self.port} after {self.timeout_connect}s")
            raise
        except Exception as e:
            _log.error(f"Error connecting to {self.host}:{self.port}: {e}", exc_info=True)
            raise

class RequestForwarder(BaseHTTPRequestHandler):
    """HTTP request handler that forwards requests to a target server while maintaining client connections."""

    # Use HTTP/1.1 to support persistent connections with clients
    protocol_version = 'HTTP/1.1'

    # Set reasonable timeouts for client connections
    timeout = 300  # 5 minutes for client socket timeout

    def setup(self):
        """Set up the request handler with proper timeouts for concurrent clients"""
        super().setup()
        # Set client socket timeout to prevent hanging connections
        if hasattr(self.connection, 'settimeout'):
            self.connection.settimeout(self.timeout)
            _log.debug(f"Set client connection timeout to {self.timeout}s for {self.client_address}")

    def handle(self):
        """Handle multiple requests if keep-alive is enabled"""
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
        """Handle a single HTTP request with proper keep-alive support"""
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
            connection_header = self.headers.get('Connection', '').lower()
            if 'close' in connection_header:
                self.close_connection = True
                _log.debug(f"Client {self.client_address} requested connection close for {self.path}")

            # Handle the request
            mname = 'do_' + self.command
            if not hasattr(self, mname):
                self.send_error(501, f"Unsupported method ({self.command})")
                return False

            method = getattr(self, mname)
            method()
            self.wfile.flush()

            return True

        except socket.timeout:
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

    def get_context_cert_pair(self) -> ContextWithPaths:
        """
        Dynamically establish SSL/TLS context based on the client's certificate.
        Falls back to a default certificate if client certificate is not available.
        """
        _log.debug("Getting SSL context and certificate pair for client connection")

        # Initialize with default certificate paths
        cert_file = None
        key_file = None
        client_cn = None

        # Try to get client certificate
        try:
            x509_binary = self.connection.getpeercert(True)
            if x509_binary:
                _log.debug("Client provided a certificate in binary format")
                try:
                    x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_ASN1, x509_binary)
                    client_cn = x509.get_subject().CN
                    _log.debug(f"Extracted client certificate CN: {client_cn}")

                    if client_cn:
                        try:
                            cert_file, key_file = self.server.tls_repo.get_file_pair(client_cn)
                            _log.debug(f"Found cert file for CN {client_cn}: {cert_file}, key file: {key_file}")
                        except FileNotFoundError as e:
                            _log.warning(f"Certificate pair not found for CN {client_cn}: {e}")
                        except Exception as e:
                            _log.warning(f"Failed to get certificate pair for CN {client_cn}: {e}")
                except OpenSSL.crypto.Error as e:
                    _log.warning(f"Failed to parse client certificate: {e}")
                except Exception as e:
                    _log.warning(f"Failed to extract CN from client certificate: {e}")
            else:
                _log.debug("Client did not provide a certificate in binary format")
        except ssl.SSLError as e:
            _log.warning(f"SSL error accessing client certificate: {e}")
        except Exception as e:
            _log.warning(f"Error accessing client certificate: {e}")

        # Fall back to default certificate if needed
        if not cert_file or not key_file:
            _log.debug("Using default certificate")
            try:
                # Use the server certificate as a fallback
                cert_file = self.server.tls_repo.server_cert_file
                key_file = self.server.tls_repo.server_key_file
                _log.debug(f"Using default cert: {cert_file}, key: {key_file}")
            except AttributeError as e:
                _log.error(f"TLS repository not properly configured: {e}")
                raise RuntimeError("TLS repository not available") from e
            except Exception as e:
                _log.error(f"Failed to get default certificate: {e}")
                raise RuntimeError("No valid certificate found for server connection") from e

        # Create the SSL context
        try:
            # Use TLS_CLIENT since we're acting as a client to the target server
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            _log.debug(f"Created SSL context with PROTOCOL_TLS_CLIENT")

            # Don't verify server certificate - typically needed for test environments
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            _log.debug(f"Set SSL verification: check_hostname=False, verify_mode=CERT_NONE")

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
            context.set_ciphers('ALL:@SECLEVEL=1')
            _log.debug("Set cipher suite: ALL:@SECLEVEL=1")

            return ContextWithPaths(context=context, certpath=cert_file, keypath=key_file)

        except ssl.SSLError as e:
            _log.error(f"SSL configuration error: {e}")
            raise RuntimeError(f"Failed to configure SSL context: {e}") from e
        except FileNotFoundError as e:
            # Let this bubble up - caller should handle missing certificates
            raise
        except Exception as e:
            _log.error(f"Unexpected error creating SSL context: {e}")
            raise RuntimeError(f"Failed to create SSL context: {e}") from e

    def __create_server_connection__(self) -> HTTPSConnectionWithTimeout:
        """
        Creates a new connection to the server with proper error handling.
        Optimized for concurrent client requests.
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
                _log.debug(f"Connection attempt {attempt+1}/{max_retries} to {host}:{port} for client {client_info}")

                # Create connection with shorter timeouts for better concurrency
                conn = HTTPSConnectionWithTimeout(
                    host=host,
                    port=port,
                    context=ccp.context,
                    timeout_connect=5,   # Shorter connect timeout
                    timeout_read=15      # Shorter read timeout
                )

                _log.debug(f"Establishing connection for client {client_info}...")
                conn.connect()
                _log.debug(f"Created server connection on attempt {attempt+1} for client {client_info}")
                return conn

            except (ssl.SSLError, socket.timeout) as e:
                _log.warning(f"Connection attempt {attempt+1} failed for client {client_info}: {e}")
                if attempt < max_retries - 1:
                    _log.debug(f"Retrying in {retry_delay}s for client {client_info}...")
                    time.sleep(retry_delay)
                else:
                    _log.error(f"All {max_retries} connection attempts failed for client {client_info}")
                    raise RuntimeError(f"Failed to establish server connection after {max_retries} attempts: {e}") from e
            except Exception as e:
                _log.error(f"Unexpected error creating connection for client {client_info}: {e}")
                raise RuntimeError(f"Unexpected error creating server connection: {e}") from e

        # This should never be reached due to the loop structure
        raise RuntimeError("Failed to create server connection: unknown error")

    def __handle_response__(self, conn: HTTPSConnectionWithTimeout):
        """
        Handle the response with proper error handling.
        """
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
            except socket.timeout:
                _log.error("Timeout reading response data from server")
                try:
                    self.send_error(504, "Gateway Timeout")
                except Exception:
                    self.close_connection = True
                return None

            # Log successful response
            _log.info(f"{self.command} {self.path} {response.status} {response.reason}")

            # Send status line
            _log.debug(f"Sending status line: {response.status} {response.reason}")
            self.send_response(response.status, response.reason)

            # Send headers, filtering out problematic ones
            skip_headers = {'connection', 'transfer-encoding', 'content-length'}
            for k, v in response.headers.items():
                if k.lower() not in skip_headers:
                    _log.debug(f"Forwarding header: {k}: {v}")
                    self.send_header(k, v)
                else:
                    _log.debug(f"Skipping header: {k}: {v}")

            # Set content length
            _log.debug(f"Setting Content-Length: {len(data)}")
            self.send_header('Content-Length', str(len(data)))

            # Handle client connection based on request headers
            client_connection = self.headers.get('Connection', '').lower()
            if self.request_version >= 'HTTP/1.1':
                # HTTP/1.1 defaults to keep-alive unless client requests close
                if 'close' not in client_connection:
                    self.send_header('Connection', 'keep-alive')
                    self.send_header('Keep-Alive', 'timeout=300, max=1000')
                    _log.debug("Maintaining keep-alive connection with client")
                else:
                    self.send_header('Connection', 'close')
                    _log.debug("Client requested connection close")
            elif 'keep-alive' in client_connection:
                # HTTP/1.0 with explicit keep-alive
                self.send_header('Connection', 'keep-alive')
                self.send_header('Keep-Alive', 'timeout=300, max=1000')
                _log.debug("HTTP/1.0 client requested keep-alive")
            else:
                # HTTP/1.0 default or explicit close
                self.send_header('Connection', 'close')
                _log.debug("Using connection close for HTTP/1.0 client")

            self.end_headers()

            # Send response body
            if data:
                _log.debug(f"Writing {len(data)} bytes to client")
                try:
                    self.wfile.write(data)
                    _log.debug("Response data written successfully")
                except (BrokenPipeError, ConnectionResetError) as e:
                    _log.error(f"Client disconnected while writing response: {e}")
                    # Client disconnected, close the connection
                    self.close_connection = True
                    return None

            return response

        except (ssl.SSLError, socket.timeout) as e:
            _log.error(f"Network error handling response from server: {e}")
            try:
                self.send_error(502, f"Bad Gateway: Server Error")
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
                self.send_error(502, f"Bad Gateway: Response Error")
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
        """Read request body based on Content-Length header"""
        content_length = int(self.headers.get('Content-Length', 0))
        _log.debug(f"Reading request body, Content-Length: {content_length}")

        if content_length > 0:
            body = self.rfile.read(content_length)
            _log.debug(f"Read {len(body)} bytes from request body")
            return body
        return b''

    def _forward_request(self, method: str) -> None:
        """Common method to forward requests of any type"""
        client_info = f"{self.client_address[0]}:{self.client_address[1]}"
        _log.info(f"Forwarding {method} {self.path} for client {client_info}")
        conn = None

        try:
            # Create a new connection to the server for each request
            _log.debug(f"Creating server connection for {method} {self.path} from client {client_info}")
            conn = self.__create_server_connection__()

            # Read request body for methods that may have one
            body = None
            if method in ('POST', 'PUT', 'PATCH', 'DELETE'):
                _log.debug(f"Reading body for {method} request from client {client_info}")
                body = self._read_request_body()
                _log.debug(f"Request body size: {len(body) if body else 0} bytes for client {client_info}")

            # Copy headers but skip hop-by-hop headers
            _log.debug(f"Processing request headers for client {client_info}")
            headers = {
                k: v
                for k, v in self.headers.items()
                if k.lower() not in ('connection', 'keep-alive', 'transfer-encoding')
            }

            # Set the host header to the target host
            host, port = self.server.proxy_target
            headers['Host'] = f"{host}:{port}"
            _log.debug(f"Set Host header to {host}:{port} for client {client_info}")

            # Add client certificate information as headers (similar to Nginx)
            try:
                x509_binary = self.connection.getpeercert(True)
                if x509_binary:
                    x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_ASN1, x509_binary)

                    # Convert to PEM format for header
                    cert_pem = OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, x509).decode('ascii')

                    # Add client certificate headers (Nginx-style)
                    headers['SSL-Client-Cert'] = cert_pem.replace('\n', ' ')
                    headers['SSL-Client-S-DN'] = str(x509.get_subject())
                    headers['SSL-Client-I-DN'] = str(x509.get_issuer())
                    headers['SSL-Client-Serial'] = str(x509.get_serial_number())
                    headers['SSL-Client-Fingerprint'] = x509.digest("sha256").decode('ascii')

                    _log.debug(f"Added client certificate headers for CN: {x509.get_subject().CN} from client {client_info}")
                else:
                    _log.debug(f"No client certificate provided by client {client_info}")
            except OpenSSL.crypto.Error as e:
                _log.warning(f"Could not parse client certificate for client {client_info}: {e}")
            except Exception as e:
                _log.warning(f"Could not extract client certificate info for client {client_info}: {e}")

            # Add Connection: close to server request to ensure proper cleanup
            headers['Connection'] = 'close'

            _log.info(f"Forwarding {method} {self.path} to {host}:{port} for client {client_info}")
            if 'SSL-Client-Cert' in headers:
                _log.debug(f"Forwarding client certificate for CN: {headers.get('SSL-Client-S-DN', 'unknown')} from client {client_info}")

            # Forward the request to the target server
            try:
                _log.debug(f"Sending {method} request to server: {self.path} for client {client_info}")
                conn.request(method=method, url=self.path, headers=headers, body=body)
                _log.debug(f"Request sent successfully for client {client_info}")
            except (ssl.SSLError, socket.timeout, BrokenPipeError, ConnectionResetError) as e:
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
            conn = None    # Connection is now closed

            if not response:
                _log.error(f"{method} {self.path} -> Failed to get response for client {client_info}")

        except RuntimeError as e:
            # These are from our own methods (SSL context creation, connection creation)
            _log.error(f"Configuration error forwarding {method} request for client {client_info}: {e}")
            try:
                self.send_error(502, f"Bad Gateway: Configuration Error")
            except Exception:
                self.close_connection = True

        except Exception as e:
            # Only catch-all here because we're at the HTTP request boundary
            # and must provide some response to the client
            _log.error(f"Unexpected error forwarding {method} request for client {client_info}: {e}", exc_info=True)
            try:
                self.send_error(502, f"Bad Gateway: Internal Error")
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
        _log.debug(f"Received GET request for {self.path}")
        self._forward_request('GET')

    def do_HEAD(self):
        _log.debug(f"Received HEAD request for {self.path}")
        self._forward_request('HEAD')

    def do_POST(self):
        _log.debug(f"Received POST request for {self.path}")
        self._forward_request('POST')

    def do_PUT(self):
        _log.debug(f"Received PUT request for {self.path}")
        self._forward_request('PUT')

    def do_DELETE(self):
        _log.debug(f"Received DELETE request for {self.path}")
        self._forward_request('DELETE')

    def do_OPTIONS(self):
        _log.debug(f"Received OPTIONS request for {self.path}")
        self._forward_request('OPTIONS')

    def do_PATCH(self):
        _log.debug(f"Received PATCH request for {self.path}")
        self._forward_request('PATCH')

    def log_request(self, code='-', size='-'):
        """Custom request logging"""
        if isinstance(code, str):
            _log.info(f"{self.command} {self.path} {code} {size}")
        elif code < 400:
            _log.info(f"{self.command} {self.path} {code} {size}")
        else:
            _log.warning(f"{self.command} {self.path} {code} {size}")

    def log_error(self, format, *args):
        """Override to use our logger instead"""
        _log.error(format % args)

    def log_message(self, format, *args):
        """Override to use our logger instead"""
        _log.info(format % args)

class ProxyServer(ThreadingHTTPServer):
    """Multi-threaded proxy server that can handle multiple clients simultaneously."""

    # Allow connection reuse and set reasonable limits
    allow_reuse_address = True
    daemon_threads = True  # Don't wait for threads to finish on shutdown

    def __init__(self, tls_repo: TLSRepository, proxy_target: Tuple[str, int], **kwargs):
        _log.debug(f"Initializing ProxyServer with target {proxy_target}")
        super().__init__(**kwargs)
        self._tls_repo = tls_repo
        self._proxy_target = proxy_target

        # Set socket options for better concurrent performance
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Enable TCP keep-alive for client connections
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

        # Set a reasonable backlog for incoming connections
        self.request_queue_size = 50

        _log.debug("ProxyServer initialized with concurrent client support")

    @property
    def proxy_target(self) -> Tuple[str, int]:
        return self._proxy_target

    @property
    def tls_repo(self) -> TLSRepository:
        return self._tls_repo

    def server_bind(self):
        """Override to set additional socket options"""
        super().server_bind()

        # Set TCP keep-alive parameters if available (Linux-specific)
        try:
            if hasattr(socket, 'TCP_KEEPIDLE'):
                self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60)
            if hasattr(socket, 'TCP_KEEPINTVL'):
                self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10)
            if hasattr(socket, 'TCP_KEEPCNT'):
                self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 6)
            _log.debug("Set TCP keep-alive parameters for client connections")
        except (AttributeError, OSError) as e:
            _log.debug(f"Could not set TCP keep-alive parameters: {e}")

    def process_request(self, request, client_address):
        """Override to add better logging and error handling for concurrent requests"""
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


def start_proxy(server_address: Tuple[str, int], tls_repo: TLSRepository,
                proxy_target: Tuple[str, int]):
    _log.info(f"Serving proxy at {server_address} -> {proxy_target}")
    try:
        _log.debug(f"Creating ProxyServer instance at {server_address}")
        httpd = ProxyServer(server_address=server_address,
                            proxy_target=proxy_target,
                            tls_repo=tls_repo,
                            RequestHandlerClass=RequestForwarder)
        _log.debug("ProxyServer instance created successfully")
    except Exception as e:
        _log.error(f"Error initializing ProxyServer: {e}", exc_info=True)
        raise

    try:
        _log.debug("Creating SSL context for proxy server")
        # Use PROTOCOL_TLS_SERVER instead of deprecated PROTOCOL_TLS
        sslctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

        # Configure SSL to require client certificates
        sslctx.verify_mode = ssl.CERT_REQUIRED    # Require client certificates
        sslctx.check_hostname = False
        _log.debug("SSL context configured with verify_mode=CERT_REQUIRED, check_hostname=False")

        # Load CA and server certificates
        if Path(tls_repo.ca_cert_file).exists():
            _log.debug(f"Loading CA certificate from {tls_repo.ca_cert_file}")
            sslctx.load_verify_locations(cafile=tls_repo.ca_cert_file)
        else:
            _log.warning(f"CA certificate file not found: {tls_repo.ca_cert_file}")

        if Path(tls_repo.server_cert_file).exists() and Path(tls_repo.server_key_file).exists():
            _log.debug(
                f"Loading server certificate: {tls_repo.server_cert_file}, {tls_repo.server_key_file}"
            )
            sslctx.load_cert_chain(certfile=tls_repo.server_cert_file,
                                   keyfile=tls_repo.server_key_file)
        else:
            _log.error(
                f"Server certificate files not found: {tls_repo.server_cert_file}, {tls_repo.server_key_file}"
            )
            return

        # Set cipher suites to be more permissive
        sslctx.set_ciphers('ALL:@SECLEVEL=1')
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

def build_address_tuple(hostname: str) -> Tuple[str, int]:
    """Create a Tuple[str, int] from the passed hostname.
    The hostname can be formatted using https://server:port or server:port
    :param: hostname
    """
    _log.debug(f"Parsing hostname: {hostname}")
    parsed = urlparse(hostname)
    if parsed.hostname:
        hostname_tuple = (parsed.hostname, parsed.port)
        _log.debug(f"Parsed URL format: {hostname_tuple}")
    else:
        parts = hostname.split(":")
        hostname_tuple = (parts[0], int(parts[1]) if len(parts) > 1 else None)
        _log.debug(f"Parsed host:port format: {hostname_tuple}")
    return hostname_tuple

def _main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(dest="config", help="Configuration file for the server.")
    parser.add_argument("--debug",
                      action="store_true",
                      default=False,
                      help="Turns debugging on for logging of the proxy.")
    opts = parser.parse_args()

    # Setup enhanced logging
    logger = setup_logging(debug=opts.debug)
    _log.debug(f"Starting 2030.5 proxy server with config: {opts.config}")

    try:
        _log.debug(f"Loading configuration from {opts.config}")
        cfg_path = Path(opts.config).expanduser().resolve(strict=True)
        cfg_dict = yaml.safe_load(cfg_path.read_text())
        _log.debug(f"Loaded configuration: {cfg_dict}")

        config = ServerConfiguration(**cfg_dict)

        if config.proxy_hostname is None:
            _log.error("Invalid proxy_hostname in config file.")
            return

        _log.debug(f"Initializing TLS repository: {config.tls_repository}")
        tls_repo = TLSRepository(repo_dir=config.tls_repository,
                               openssl_cnffile_template=config.openssl_cnf,
                               serverhost=config.server_hostname,
                               proxyhost=config.proxy_hostname,
                               clear=False)
        _log.debug("TLS repository initialized successfully")

        proxy_host = build_address_tuple(config.proxy_hostname)
        server_host = build_address_tuple(config.server_hostname)

        _log.debug(f"Proxy host tuple: {proxy_host}")
        _log.debug(f"Server host tuple: {server_host}")

        start_proxy(server_address=(proxy_host[0], int(proxy_host[1])),
                  tls_repo=tls_repo,
                  proxy_target=(server_host[0], int(server_host[1])))

    except Exception as e:
        _log.critical(f"Fatal error in proxy server: {e}", exc_info=True)
        return 1

if __name__ == '__main__':
    _main()
