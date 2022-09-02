from __future__ import annotations

import logging
from dataclasses import dataclass
from http.client import HTTPSConnection
from http.server import HTTPServer, BaseHTTPRequestHandler
import ssl
from pathlib import Path
from typing import Tuple
from urllib.parse import urlparse

import OpenSSL
import yaml

from ieee_2030_5.certs import TLSRepository
from ieee_2030_5.config import ServerConfiguration


@dataclass
class ContextWithPaths:
    context: ssl.SSLContext
    certpath: str
    keypath: str


class RequestForwarder(BaseHTTPRequestHandler):

    def get_context_cert_pair(self) -> ContextWithPaths:
        x509_binary = self.connection.getpeercert(True)
        cert_file = None
        key_file = None
        if x509_binary:
            x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_ASN1, x509_binary)
            cn = x509.get_subject().CN
            cert_file, key_file = self.server.tls_repo.get_file_pair(cn)

        context = ssl.SSLContext(ssl.PROTOCOL_TLS)
        context.verify_mode = ssl.CERT_OPTIONAL

        context.load_verify_locations(cafile="/home/gridappsd/tls/certs/ca.crt")
        if cert_file is not None and key_file is not None and \
                Path(cert_file).exists() and Path(key_file).exists():
            context.load_cert_chain(certfile=cert_file, keyfile=key_file)
        return ContextWithPaths(context=context, certpath=cert_file, keypath=key_file)

    def do_GET(self):
        ccp = self.get_context_cert_pair()

        host, port = self.server.proxy_target
        conn = HTTPSConnection(host=host, port=port,
                               context=ccp.context)
        conn.connect()

        headers = {}
        for k, v in self.headers.items():
            headers[k] = v

        conn.request(method="GET",
                     url=self.path,
                     headers=headers,
                     encode_chunked=True)
        response = conn.getresponse()
        data = response.read()
        self.wfile.write(f'HTTP/1.1 {response.status}\n'.encode('utf-8'))

        for k, v in response.headers.items():
            print(f"Key is: {k}")
            if k not in ('Connection',):
                if k == 'Content-Length':
                    print(k, v)
                    print(k, len(data))
                    self.send_header(k, str(len(data)))
                else:
                    print(f"header is: {k}")
                    self.send_header(k, v)
        self.end_headers()

        print(data)
        # self.wfile.write(data)
        # self.send_response(response.status, data.decode("utf-8"))
        self.wfile.write(data)
        self.close_connection = False
        # self.wfile.write(response.read())
        # self.wfile.flush()

    def do_POST(self):
        print("Handling Post")


class ProxyServer(HTTPServer):

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


def start_proxy(server_address: Tuple[str, int], tls_repo: TLSRepository, proxy_target: Tuple[str, int]):
    logging.getLogger().info(f"Serving {server_address} proxied to {proxy_target}")
    RequestForwarder.protocol_version = "HTTP/1.1"
    httpd = ProxyServer(server_address=server_address,
                        proxy_target=proxy_target,
                        tls_repo=tls_repo,
                        RequestHandlerClass=RequestForwarder)
    # Since version 3.10: SSLContext without protocol argument is deprecated.
    # sslctx = ssl.SSLContext()
    sslctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

    # Use optional, because we need the cert for 2030.5 but not the admin
    # interface.
    sslctx.verify_mode = ssl.CERT_OPTIONAL
    sslctx.load_verify_locations(cafile=tls_repo.ca_cert_file)

    sslctx.check_hostname = False  # If set to True, only the hostname that matches the certificate will be accepted
    sslctx.load_cert_chain(certfile=tls_repo.server_cert_file,
                           keyfile=tls_repo.server_key_file)
    httpd.socket = sslctx.wrap_socket(httpd.socket, server_side=True)
    httpd.serve_forever()


def _main():
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(dest="config", help="Configuration file for the server.")

    # parser.add_argument("bind_address")
    # parser.add_argument("forward_address")
    # parser.add_argument("--tls-repo", default="~/tls")
    # parser.add_argument("--opensslcnf", default="~/tls/openssl.cnf")
    # parser.add_argument("--ca-file")
    # parser.add_argument("--key-file")
    # parser.add_argument("--cert-file")

    opts = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)

    cfg_dict = yaml.safe_load(Path(opts.config).expanduser().resolve(strict=True).read_text())

    config = ServerConfiguration(**cfg_dict)

    tls_repo = TLSRepository(repo_dir=config.tls_repository,
                             openssl_cnffile=config.openssl_cnf,
                             serverhost=config.server_hostname,
                             proxyhost=config.proxy_hostname,
                             clear=False)

    proxy_host = config.proxy_hostname.split(":")
    server_host = config.server_hostname.split(":")

    start_proxy(server_address=(proxy_host[0], int(proxy_host[1])),
                tls_repo=tls_repo,
                proxy_target=(server_host[0], int(server_host[1])))


if __name__ == '__main__':
    _main()
    # context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH,
    #                                      cafile=str(tls_repo.ca_cert_file))
    #
    # context.load_cert_chain(certfile=tls_repo.proxy_cert_file, keyfile=tls_repo.proxy_key_file)
    # context.verify_mode = ssl.CERT_OPTIONAL  # ssl.CERT_REQUIRED #  ssl.CERT_OPTIONAL  # ssl.CERT_REQUIRED
    #
    # start_proxy((proxy_url.hostname, proxy_url.port),
    #             (forward_url.hostname, forward_url.port), context=context, tls_repo=tls_repo)

# import datetime
# import email
# import json
# import logging
# import socket
# import ssl
# from http.client import HTTPSConnection, HTTPResponse
# from pathlib import Path
# from typing import Tuple, Iterable
# from urllib.parse import urlparse
#
# import OpenSSL
# import gevent
# import h11
# from gevent import Greenlet
# from gevent import monkey
# import grequests
#
# from ieee_2030_5.certs import TLSRepository
# from ieee_2030_5.types_ import StrPath
#
# monkey.patch_all()
#
# MAX_RECV = 2 ** 16
# TIMEOUT = 10
#
#
# # We are using email.utils.format_datetime to generate the Date header.
# # It may sound weird, but it actually follows the RFC.
# # Please see: https://stackoverflow.com/a/59416334/14723771
# #
# # See also:
# # [1] https://www.rfc-editor.org/rfc/rfc9110#section-5.6.7
# # [2] https://www.rfc-editor.org/rfc/rfc7231#section-7.1.1.1
# # [3] https://www.rfc-editor.org/rfc/rfc5322#section-3.3
# def format_date_time(dt=None):
#     """Generate a RFC 7231 / RFC 9110 IMF-fixdate string"""
#     if dt is None:
#         dt = datetime.datetime.now(datetime.timezone.utc)
#     return email.utils.format_datetime(dt, usegmt=True)
#
#
# __next__id__ = 0
#
#
# def next_id():
#     global __next__id__
#     __next__id__ += 1
#     return __next__id__
#
#
# class ForwardedClient:
#     def __init__(self, host, port, server_cert, key_file, cert_file):
#         context = ssl.SSLContext(ssl.PROTOCOL_TLS)
#         context.verify_mode = ssl.CERT_REQUIRED
#         context.load_verify_locations(cafile="/home/gridappsd/tls/certs/ca.crt")
#         context.load_cert_chain(certfile=cert_file, keyfile=key_file)
#
#         self.conn = HTTPSConnection(host=host,
#                                     port=port,
#                                     context=context)
#         self.conn.set_debuglevel(5)
#         # self.sock = socket.create_connection((host, port))
#         #
#         # ctx = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH, cafile=server_cert)
#         # ctx.load_cert_chain(certfile=cert_file, keyfile=key_file)
#         # self.sock = ctx.wrap_socket(self.sock, server_hostname=host)
#         # self.conn = h11.Connection(our_role=h11.CLIENT)
#         self._log = logging.getLogger("ForwarderClient")
#         # self._log.debug(f"States: {self.conn.states}")
#         self._response = None
#
#     def get_response(self) -> HTTPResponse:
#         return self.conn.getresponse()
#
#     def send(self, request: h11.Request):
#         self._log.debug(f"Sending request: {request}")
#         headers = {}
#         for k, v in request.headers:
#             headers[k.decode('utf-8')] = v.decode('utf-8')
#         self.conn.connect()
#         self._log.debug(f"Headers: {headers}")
#         self.conn.request(method=request.method.decode("utf-8"),
#                           url=request.target.decode("utf-8"),
#                           headers=headers)
#
#         # self._log.debug(f"States: {self.conn.states}")
#         # self._log.debug(f"Sending event: {events}")
#         # for event in events:
#         #     data = self.conn.send(event)
#         #     if data is None:
#         #         # event was a ConnectionClosed(), meaning that we won't be
#         #         # sending any more data:
#         #         self.sock.shutdown(socket.SHUT_WR)
#         #     else:
#         #         self._log.debug(f"Sending data {data}")
#         #         self.sock.sendall(data)
#
#     # max_bytes_per_recv intentionally set low for pedagogical purposes
#     # def next_event(self, max_bytes_per_recv=MAX_RECV):
#     #     while True:
#     #         self._log.debug(f"States: {self.conn.states}")
#     #         # If we already have a complete event buffered internally, just
#     #         # return that. Otherwise, read some data, add it to the internal
#     #         # buffer, and then try again.
#     #         event = self.conn.next_event()
#     #         self._log.debug(f"Event is {event}")
#     #         if event is h11.NEED_DATA:
#     #             data = self.sock.recv(max_bytes_per_recv)
#     #             self._log.debug(f"Received from proxy: {data}")
#     #             self.conn.receive_data(data)
#     #
#     #             continue
#     #         self._log.debug(f"States: {self.conn.states}")
#     #         return event
#
#
# class ConnectionWrapper(Greenlet):
#
#     def __init__(self, stream: ssl.SSLSocket,
#                  proxy_to: Tuple[str, int] = None,
#                  cert_file: str = None,
#                  key_file: str = None,
#                  server_cert: str = None):
#         super().__init__()
#
#         if not proxy_to:
#             raise ValueError("Proxy to must be set to (ip, port)")
#
#         if not isinstance(proxy_to, Iterable):
#             raise ValueError("proxy_to is not iterable.")
#
#         self.proxy_to = proxy_to
#         self.address_passthrough = f"https://{proxy_to[0]}:{proxy_to[1]}"
#
#         if cert_file is not None:
#             assert Path(cert_file).exists()
#         if key_file is not None:
#             assert Path(key_file).exists()
#         if cert_file is not None and key_file is None:
#             raise ValueError("Both key_file and cert_file must have values if one does.")
#         self.cert_file = cert_file
#         self.key_file = key_file
#         self.server_cert = server_cert
#         self.h11Conn = h11.Connection(h11.SERVER)
#         self.stream = stream
#         self.ident = "This is my ident string"
#         self._id = next_id()
#         self._log = logging.getLogger("ConnectionWrapper")
#
#     def _run(self):
#         gevent.sleep()
#         times = 1
#         self.debug("Running greenlet now")
#         while True:
#             self.debug(f"h11 states: {self.h11Conn.states}")
#             # if times > 20:
#             #     print("Loop")
#             #     times += 1
#             data = self.stream.recv(MAX_RECV)
#
#             event = self.next_event()
#             if type(event) is h11.ConnectionClosed:
#                 self.info("Connection closed.")
#                 break
#             self.debug(event)
#             gevent.sleep()
#         self.stream.close()
#         self.debug(f"Stream closed for {self._id}")
#         self.kill()
#
#     def error(self, *args):
#         self._log.error(f"{self._id}: {args}")
#
#     def info(self, *args):
#         self._log.info(f"{self._id}: {args}")
#
#     def debug(self, *args):
#         self._log.debug(f"{self._id}: {args}")
#
#     def next_event(self):
#         while True:
#             self.debug(f"Next event states: {self.h11Conn.states}")
#             if self.h11Conn.our_state == h11.MUST_CLOSE and \
#                     self.h11Conn.their_state == h11.MUST_CLOSE:
#                 self.debug("Starting next cycle.")
#                 self.h11Conn.start_next_cycle()
#             event = self.h11Conn.next_event()
#             self.debug(f"Event is: {event}")
#             if event is h11.NEED_DATA:
#                 self.info("reading from peer?")
#                 self._read_from_peer()
#                 continue
#             elif type(event) is h11.Request:
#                 self.info(f"Request: {event}")
#                 response = self.forward_request(event)
#                 self.debug(response.headers)
#                 self.debug(response.status)
#                 self.debug(response.msg)
#                 headers = []
#                 for k, v in response.headers.items():
#                     headers.append((k, v))
#                 self.send(h11.Response(status_code=response.status, headers=headers))
#                 self.send(h11.Data(response.read()))
#                 # for e in self.forward_request(event):
#                 #     self.send(e)
#
#                 # send_echo_response(self, event)
#             # elif type(event) == h11.EndOfMessage:
#             #     self.info("EndOfMesssage")
#             #     self.stream.send()
#
#             return event
#
#     def forward_request(self, event: h11.Request):
#
#         fwd = ForwardedClient(*self.proxy_to, self.server_cert, self.key_file, self.cert_file)
#         fwd.send(event)
#         # responses = []
#         #
#         # next_event = fwd.next_event()
#         # responses.append(next_event)
#         # while type(next_event) != h11.EndOfMessage:
#         #     next_event = fwd.next_event()
#         #     responses.append(next_event)
#         response = fwd.get_response()
#         return response
#         #
#         # forward_context = ssl.create_default_context()
#         # sock = forward_context.wrap_socket(socket.create_connection(self.proxy_to),
#         #                                    server_hostname=self.proxy_to[0])
#         # h11conn = h11.Connection(our_role=h11.CLIENT)
#         # request = h11.Request(method=event.method,
#         #                       target=event.target,
#         #                       headers=event.headers)
#         # bytes_to_send = h11conn.send(request)
#         # sock.sendall(bytes_to_send)
#         # end_of_message_bytes_to_send = h11conn.send(h11.EndOfMessage())
#         # sock.sendall(end_of_message_bytes_to_send)
#         # bytes_received = sock.recv(MAX_RECV)
#         # response = h11conn.next_event()
#         # data = h11conn.next_event()
#
#     def _read_from_peer(self):
#         self.debug("Reading from peer")
#         if self.h11Conn.they_are_waiting_for_100_continue:
#             self.info("Sending 100 Continue")
#             go_ahead = h11.InformationalResponse(
#                 status_code=100, headers=self.basic_headers()
#             )
#             self.info(f"Send {go_ahead}")
#             self.send(go_ahead)
#         try:
#             data = self.stream.recv(MAX_RECV)
#
#         except ConnectionError:
#             # They've stopped listening. Not much we can do about it here.
#             data = b""
#             self.info("Connection error")
#
#         self.debug(f"Received data: {data}")
#         self.h11Conn.receive_data(data)
#
#     def send(self, event):
#         # The code below doesn't send ConnectionClosed, so we don't bother
#         # handling it here either -- it would require that we do something
#         # appropriate when 'data' is None.
#         assert type(event) is not h11.ConnectionClosed
#         data = self.h11Conn.send(event)
#         self.info(f"Sending data to client {data}")
#         try:
#             # if data is empty then we shouldn't send it across at least this
#             # is a fix for
#             # ssl.SSLEOFError: EOF occurred in violation of protocol (_ssl.c:2485)
#             if data:
#                 self.stream.send(data)
#         except BaseException as ex:
#             self.info(f"Base exception {ex}")
#             # If send_all raises an exception (especially trio.Cancelled),
#             # we have no choice but to give it up.
#             self.info("Send failed now.")
#             self.h11Conn.send_failed()
#             raise
#
#         self.debug(f"After sending states: {self.h11Conn.states}")
#
#     def basic_headers(self):
#         # HTTP requires these headers in all responses (client would do
#         # something different here)
#         return [
#             ("Date", format_date_time().encode("ascii")),
#             ("Server", self.ident),
#         ]
#
#
# def send_simple_response(wrapper, status_code, content_type, body):
#     wrapper.info("Sending", status_code, "response with", len(body), "bytes")
#     headers = wrapper.basic_headers()
#     headers.append(("Content-Type", content_type))
#     headers.append(("Content-Length", str(len(body))))
#     res = h11.Response(status_code=status_code, headers=headers)
#     wrapper.send(res)
#     wrapper.send(h11.Data(data=body))
#     wrapper.send(h11.EndOfMessage())
#
#
# def send_echo_response(wrapper, request):
#     wrapper.info("Preparing echo response")
#     if request.method not in {b"GET", b"POST"}:
#         # Laziness: we should send a proper 405 Method Not Allowed with the
#         # appropriate Accept: header, but we don't.
#         raise RuntimeError("unsupported method")
#     response_json = {
#         "method": request.method.decode("ascii"),
#         "target": request.target.decode("ascii"),
#         "headers": [
#             (name.decode("ascii"), value.decode("ascii"))
#             for (name, value) in request.headers
#         ],
#         "body": "",
#     }
#     while True:
#         event = wrapper.next_event()
#         if type(event) is h11.EndOfMessage:
#             break
#         assert type(event) is h11.Data
#         response_json["body"] += event.data.decode("ascii")
#     response_body_unicode = json.dumps(
#         response_json, sort_keys=True, indent=4, separators=(",", ": ")
#     )
#     response_body_bytes = response_body_unicode.encode("utf-8")
#     send_simple_response(
#         wrapper, 200, "application/json; charset=utf-8", response_body_bytes
#     )
#
#
# def validate_path(path: StrPath) -> str:
#     if isinstance(path, str):
#         path = Path(path)
#     path = path.expanduser().resolve()
#     if not path.exists():
#         raise ValueError(f"Invalid path: {path}")
#
#     return str(path)
#
#
# def start_proxy(bind_address: Tuple[str, int], forward_address: Tuple[str, int],
#                 context: ssl.SSLContext, tls_repo: TLSRepository):
#     greenlets = []
#     proxy_to = forward_address
#     with socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) as sock:
#         sock.bind(bind_address)
#         # specify backlog (if not specified then a "reasonable default" is sspecified
#         sock.listen()
#         with context.wrap_socket(sock, server_side=True) as ssock:
#             while True:
#
#                 conn, addr = ssock.accept()
#
#                 try:
#                     x509_binary = conn.getpeercert(True)
#                     if x509_binary:
#                         x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_ASN1, x509_binary)
#                         cn = x509.get_subject().CN
#                         cert_file, key_file = tls_repo.get_file_pair(cn)
#                         wrapper = ConnectionWrapper(conn, proxy_to, cert_file, key_file, str(tls_repo.server_cert_file))
#                     else:
#                         wrapper = ConnectionWrapper(conn, proxy_to)
#                 except ssl.SSLError as ex:
#                     wrapper = ConnectionWrapper(conn, proxy_to)
#                 wrapper.info("Started new wrapper.")
#                 gevent.spawn(wrapper.run)
#                 greenlets.append(wrapper)
#                 logging.getLogger().debug(f"# greenlets: {len(greenlets)}")
#                 logging.getLogger().debug(f"live greenlets: {[x for x in greenlets if not x.dead]}")
#                 logging.getLogger().debug(f"dead greenlets: {[x for x in greenlets if x.dead]}")
#                 # trim greenlets that have exited.
#                 greenlets = [x for x in greenlets if not x.dead]
#
#
# if __name__ == '__main__':
#     import argparse
#
#     parser = argparse.ArgumentParser()
#
#     parser.add_argument("bind_address")
#     parser.add_argument("forward_address")
#     parser.add_argument("--tls-repo", default="~/tls")
#     parser.add_argument("--opensslcnf", default="~/tls/openssl.cnf")
#     # parser.add_argument("--ca-file")
#     # parser.add_argument("--key-file")
#     # parser.add_argument("--cert-file")
#
#     args = parser.parse_args()
#
#     logging.basicConfig(level=logging.DEBUG)
#
#     cnf_file = Path(args.opensslcnf).expanduser().resolve()
#     repo_dir = Path(args.tls_repo).expanduser().resolve()
#
#     if not repo_dir.exists():
#         raise ValueError(f"Invalid repo directory {str(repo_dir)}")
#
#     if not cnf_file.exists():
#         raise ValueError(f"Invalid opensslcnf file {str(cnf_file)}")
#
#     forward_url = urlparse(args.forward_address)
#     proxy_url = urlparse(args.bind_address)
#
#     if not forward_url.scheme == 'https':
#         raise ValueError("Forward address must be https")
#     if not proxy_url.scheme == 'https':
#         raise ValueError("Bind address must be https")
#
#     args.forward_address = f"{forward_url.hostname}:{forward_url.port}"
#     args.bind_address = f"{proxy_url.hostname}:{proxy_url.port}"
#     tls_repo = TLSRepository(repo_dir=repo_dir, openssl_cnffile=cnf_file,
#                              serverhost=args.forward_address, proxyhost=args.bind_address,
#                              clear=False)
#
#     context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH,
#                                          cafile=str(tls_repo.ca_cert_file))
#
#     context.load_cert_chain(certfile=tls_repo.proxy_cert_file, keyfile=tls_repo.proxy_key_file)
#     context.verify_mode = ssl.CERT_OPTIONAL  # ssl.CERT_REQUIRED #  ssl.CERT_OPTIONAL  # ssl.CERT_REQUIRED
#
#     start_proxy((proxy_url.hostname, proxy_url.port),
#                 (forward_url.hostname, forward_url.port), context=context, tls_repo=tls_repo)
