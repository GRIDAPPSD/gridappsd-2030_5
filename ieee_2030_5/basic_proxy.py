from __future__ import annotations

import logging
import os
import socket
import ssl
from dataclasses import dataclass
from http.client import HTTPSConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Tuple
from urllib.parse import urlparse

import OpenSSL
import yaml

from ieee_2030_5.certs import (TLSRepository, lfdi_from_fingerprint,
                               sfdi_from_lfdi)
from ieee_2030_5.config import ServerConfiguration

_log = logging.getLogger(__name__)


@dataclass
class ContextWithPaths:
    context: ssl.SSLContext
    certpath: str
    keypath: str

connections: dict[str, HTTPSConnection] = {}

class RequestForwarder(BaseHTTPRequestHandler):

    def get_context_cert_pair(self) -> ContextWithPaths:
        """
        Dynamically establish SSL/TLS context based on the client's certificate.
        """
        x509_binary = self.connection.getpeercert(True)
        cert_file = None
        key_file = None
        if x509_binary:
            x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_ASN1, x509_binary)
            cn = x509.get_subject().CN
            cert_file, key_file = self.server.tls_repo.get_file_pair(cn)

        context = ssl.SSLContext(ssl.PROTOCOL_TLS)
        context.verify_mode = ssl.CERT_OPTIONAL

        assert cert_file, "Client certificate file not found."
        ca_file = str(Path(cert_file).parent.joinpath("ca.crt"))
        context.load_verify_locations(cafile=ca_file)
        if Path(cert_file).exists() and Path(key_file).exists():
            context.load_cert_chain(certfile=cert_file, keyfile=key_file)

        return ContextWithPaths(context=context, certpath=cert_file, keypath=key_file)

    def __start_request__(self) -> HTTPSConnection:
        """
        Handles the creation or resetting of the client's connection.
        Drops previous connection if the client sends a new request.
        """
        ccp = self.get_context_cert_pair()

        # Identify the client's connection by its keypath (unique per cert/key pair)
        connection_name = ccp.keypath

        # Check if a connection with this client already exists
        conn = connections.get(connection_name)

        if conn:
            _log.info(f"Existing connection for client '{connection_name}' found. Closing it...")
            try:
                conn.close()  # Forcefully close stale connection
                connections.pop(connection_name, None)
            except Exception as e:
                _log.error(f"Error closing stale connection '{connection_name}': {e}")
        
        # Create a fresh HTTPSConnection for the new request
        host, port = self.server.proxy_target
        conn = HTTPSConnection(host=host, port=port, context=ccp.context)
        conn.connect()
        _log.info(f"Created new connection for client '{connection_name}'.")

        # Save the connection name for tracking
        self.request.connection_name = connection_name
        connections[connection_name] = conn

        return conn

    def __handle_response__(self, conn: HTTPSConnection):
        response = conn.getresponse()
        data = response.read()

        _log.debug(f"Response from server:\n{data.decode('utf-8')}")
        self.wfile.write(f'HTTP/1.1 {response.status}\n'.encode('utf-8'))

        for k, v in response.headers.items():
            if k not in ('Connection', ):
                if k == 'Content-Length':
                    self.send_header(k, str(len(data)))
                else:
                    self.send_header(k, v)
        self.end_headers()

        # Send back the response data
        self.wfile.write(data)
        self.close_connection = False
        return response


    def do_GET(self):
        conn = self.__start_request__()
        conn.request(method="GET", url=self.path, headers=self.headers, encode_chunked=True)
        response = self.__handle_response__(conn)
        _log.info(f"GET {self.path}, Response Status: {response.status}, Content-Length: {self.headers.get('Content-Length')}")
    
    def do_POST(self):
        conn = self.__start_request__()
        read_data = self.rfile.read(int(self.headers.get('Content-Length')))
        conn.request(method="POST", url=self.path, headers=self.headers, body=read_data, encode_chunked=True)
        response = self.__handle_response__(conn)
        _log.info(f"POST {self.path}, Response Status: {response.status}, Content-Length: {self.headers.get('Content-Length')}")
    
    def do_DELETE(self):
        conn = self.__start_request__()
        read_data = self.rfile.read(int(self.headers.get('Content-Length')))
        conn.request(method="DELETE", url=self.path, headers=self.headers, body=read_data, encode_chunked=True)
        response = self.__handle_response__(conn)
        _log.info(f"DELETE {self.path}, Response Status: {response.status}, Content-Length: {self.headers.get('Content-Length')}")

    def do_PUT(self):
        conn = self.__start_request__()
        read_data = self.rfile.read(int(self.headers.get('Content-Length')))
        conn.request(method="PUT", url=self.path, headers=self.headers, body=read_data, encode_chunked=True)
        response = self.__handle_response__(conn)
        _log.info(f"PUT {self.path}, Response Status: {response.status}, Content-Length: {self.headers.get('Content-Length')}")



class ProxyServer(ThreadingHTTPServer):

    def __init__(self, tls_repo: TLSRepository, proxy_target: Tuple[str, int], **kwargs):
        super().__init__(**kwargs)
        self._tls_repo = tls_repo
        self._proxy_target = proxy_target

    @property
    def proxy_target(self) -> Tuple[str, int]:
        return self._proxy_target

    @property
    def tls_repo(self) -> TLSRepository:
        return self._tls_repo

    def finish_request(self, request, client_address):
        """
        Called after handling a request.
        """
        super().finish_request(request, client_address)

    def shutdown_request(self, request: socket.socket):
        """
        Cleans up connections when requests are closed.
        Handles cases where the client has already disconnected.
        """
        try:
            peer_name = request.getpeername()  # Try to get the peer name
            _log.info(f"Shutting down request from {peer_name}")
        except OSError as e:
            # Handle scenarios where the client has already disconnected
            if e.errno == 107:  # Transport endpoint is not connected
                _log.warning("Client disconnected before shutdown. Cleaning up anyway...")
            else:
                _log.error(f"Unexpected error getting peer name: {e}")
        
        # Clean up connection if connection_name exists
        connection_name = getattr(request, 'connection_name', None)
        if connection_name and connection_name in connections:
            try:
                _log.info(f"Closing connection: {connection_name}")
                conn = connections.pop(connection_name, None)
                if conn:
                    conn.close()
            except Exception as e:
                _log.error(f"Error closing connection '{connection_name}': {e}")

        super().shutdown_request(request)


    def clean_up_connection(self):
        """
        Ensures all stale connections are closed explicitly during cleanup operations.
        """
        to_remove = []
        for connection_name, conn in connections.items():
            try:
                conn.close()
                to_remove.append(connection_name)
            except Exception as e:
                _log.error(f"Error during connection cleanup: {e}")
        
        for connection_name in to_remove:
            connections.pop(connection_name, None)
            _log.info(f"Removed stale connection: {connection_name}")


def start_proxy(server_address: Tuple[str, int], tls_repo: TLSRepository,
                proxy_target: Tuple[str, int]):
    logging.getLogger().info(f"Serving {server_address} proxied to {proxy_target}")
    RequestForwarder.protocol_version = "HTTP/1.1"

    # Initialize ProxyServer with a cleanup method
    try:
        httpd = ProxyServer(
            server_address=server_address,
            proxy_target=proxy_target,
            tls_repo=tls_repo,
            RequestHandlerClass=RequestForwarder
        )
    except Exception as e:
        _log.error(f"Error initializing ProxyServer: {e}")
        raise

    try:
        sslctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        sslctx.verify_mode = ssl.CERT_OPTIONAL
        sslctx.load_verify_locations(cafile=tls_repo.ca_cert_file)
        sslctx.check_hostname = False
        sslctx.load_cert_chain(certfile=tls_repo.server_cert_file, keyfile=tls_repo.server_key_file)

        httpd.socket = sslctx.wrap_socket(httpd.socket, server_side=True)

        _log.info("Starting proxy server...")
        httpd.serve_forever()
    except KeyboardInterrupt:
        _log.warning("Proxy server shutting down...")
        httpd.clean_up_connection()  # Clean up all connections explicitly
    except Exception as e:
        _log.error(f"Unexpected error: {e}")
    finally:
        httpd.server_close()



def build_address_tuple(hostname: str) -> Tuple[str, int]:
    """Create a Tuple[str, int] from the passed hostname.

    The hostname can be formatted using https://server:port or server:port

    :param: hostname
    """
    parsed = urlparse(hostname)

    if parsed.hostname:
        hostname = (parsed.hostname, parsed.port)
    else:
        hostname = hostname.split(":")
        hostname = (hostname[0], int(hostname[1]))
    return hostname


def _main():
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(dest="config", help="Configuration file for the server.")
    parser.add_argument("--debug",
                        action="store_true",
                        default=False,
                        help="Turns debugging on for logging of the proxy.")

    opts = parser.parse_args()

    debug_level = logging.DEBUG if opts.debug else logging.DEBUG
    logging.basicConfig(level=debug_level)

    cfg_dict = yaml.safe_load(Path(opts.config).expanduser().resolve(strict=True).read_text())

    config = ServerConfiguration(**cfg_dict)

    if config.proxy_hostname is None:
        print("Invalid proxy_hostname in config file.")

    tls_repo = TLSRepository(repo_dir=config.tls_repository,
                             openssl_cnffile_template=config.openssl_cnf,
                             serverhost=config.server_hostname,
                             proxyhost=config.proxy_hostname,
                             clear=False)

    proxy_host = build_address_tuple(config.proxy_hostname)
    server_host = build_address_tuple(config.server_hostname)

    _log.debug(f"Proxy host tuple: {proxy_host}")
    _log.debug(f"Server host tuple: {server_host}")

    start_proxy(server_address=(proxy_host[0], int(proxy_host[1])),
                tls_repo=tls_repo,
                proxy_target=(server_host[0], int(server_host[1])))


if __name__ == '__main__':
    _main()
