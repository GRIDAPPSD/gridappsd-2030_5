import json
import logging
import ssl
from pathlib import Path

import OpenSSL
import werkzeug.exceptions
from flask import Flask, render_template, request, redirect, Response
from werkzeug.serving import make_server, BaseWSGIServer

__all__ = ["build_server"]

# templates = Jinja2Templates(directory="templates")
from ieee_2030_5.config import ServerConfiguration
from ieee_2030_5.certs import TLSRepository, lfdi_from_fingerprint, sfdi_from_lfdi
from ieee_2030_5.data.indexer import get_href_all_names, get_href
from ieee_2030_5.server.admin_endpoints import AdminEndpoints
from ieee_2030_5.server.server_endpoints import ServerEndpoints
from ieee_2030_5.server.server_constructs import get_groups, EndDevices

_log = logging.getLogger(__file__)


class PeerCertWSGIRequestHandler(werkzeug.serving.WSGIRequestHandler):
    """
    We subclass this class so that we can gain access to the connection
    property. self.connection is the underlying client socket. When a TLS
    connection is established, the underlying socket is an instance of
    SSLSocket, which in turn exposes the getpeercert() method.

    The output from that method is what we want to make available elsewhere
    in the application.
    """
    tlsrepo: TLSRepository
    debug_device: str

    def make_environ(self):
        """
        The superclass method develops the environ hash that eventually
        forms part of the Flask request object.

        We allow the superclass method to run first, then we insert the
        peer certificate into the hash. That exposes it to us later in
        the request variable that Flask provides
        """
        environ = super(PeerCertWSGIRequestHandler, self).make_environ()

        # Assume browser is being hit with things that start with /admin allow
        # a pass through from web (should be protected via auth but not right now)
        if environ['PATH_INFO'].startswith("/admin"):
            return environ

        try:
            x509_binary = self.connection.getpeercert(True)

            x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_ASN1, x509_binary)
            environ['ieee_2030_5_peercert'] = x509
            environ['ieee_2030_5_subject'] = x509.get_subject().CN
            environ['ieee_2030_5_serial_number'] = x509.get_serial_number()
            environ['ieee_2030_5_lfdi'] = lfdi_from_fingerprint(x509.digest("sha1").decode('ascii'))
            environ['ieee_2030_5_sfdi'] = sfdi_from_lfdi(environ['ieee_2030_5_lfdi'])
            _log.debug(f"Environment lfdi: {environ['ieee_2030_5_lfdi']} sfdi: {environ['ieee_2030_5_sfdi']}")
        except OpenSSL.crypto.Error:
            # Only if we have a debug_device do we want to expose this device through the admin page.
            if self.debug_device:
                cert_file, key_file = self.tlsrepo.get_file_pair(self.debug_device)
                x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, Path(cert_file).read_bytes())
                environ['ieee_2030_5_peercert'] = x509
                environ['ieee_2030_5_subject'] = x509.get_subject().CN
                print(x509.get_serial_number())

            else:
                environ['peercert'] = None

        return environ


# based on
# https://stackoverflow.com/questions/19459236/how-to-handle-413-request-entity-too-large-in-python-flask-server#:~:text=server%20MAY%20close%20the%20connection,client%20from%20continuing%20the%20request.&text=time%20the%20client%20MAY%20try,you%20the%20Broken%20pipe%20error.&text=Great%20than%20the%20application%20is%20acting%20correct.
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
    _log.debug(f"HEADERS: {request.headers}")
    _log.debug(f"REQ_path: {request.path}")
    _log.debug(f"ARGS: {request.args}")
    _log.debug(f"DATA: {request.get_data()}")
    _log.debug(f"FORM: {request.form}")


def after_request(response: Response) -> Response:
    _log.debug(f"RESP:\n{response.get_data().decode('utf-8')}")
    return response


def __build_ssl_context__(tlsrepo: TLSRepository) -> ssl.SSLContext:
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
    ssl_context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH,
                                             cafile=str(ca_cert))

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
    return ssl_context


def __build_app__(config: ServerConfiguration, tlsrepo: TLSRepository,
                  enddevices: EndDevices) -> Flask:
    app = Flask(__name__, template_folder=str(Path(".").resolve().joinpath('templates')))

    # Debug headers path and request arguments
    app.before_request(before_request)
    # Allows for larger data to be sent through because of chunking types.
    app.before_request(handle_chunking)
    app.after_request(after_request)

    ServerEndpoints(app, end_devices=enddevices, tls_repo=tlsrepo, config=config)
    AdminEndpoints(app, end_devices=enddevices, tls_repo=tlsrepo, config=config)

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

    @app.route("/admin/resources")
    def admin_resource_list():
        resource = request.args.get("rurl")
        obj = get_href(resource)
        all_resources = sorted(get_href_all_names())
        if obj:
            return render_template("admin/resource_list.html",
                                   resource_urls=all_resources,
                                   href_shown=resource,
                                   object=obj)
        else:
            return render_template("admin/resource_list.html", resource_urls=all_resources)

    @app.route("/admin/clients")
    def admin_clients():
        clients = tlsrepo.client_list
        return json.dumps(
            clients)  # render_template("admin/clients.html", registered=clients, connected=[])

    @app.route("/admin/groups")
    def admin_groups():
        groups = get_groups()
        return render_template("admin/groups.html", groups=groups)

    @app.route("/admin/aggregators")
    def admin_aggregators():
        return Response("<h1>Aggregators</h1>")

    @app.route("/admin/routes")
    def admin_routes():
        routes = '<ul>'
        for p in app.url_map.iter_rules():
            routes += f"<li>{p.rule}</li>"
        routes += "</ul>"
        return Response(f"{routes}")

    return app


def run_server(config: ServerConfiguration,
               tlsrepo: TLSRepository,
               enddevices: EndDevices, **kwargs):
    app = __build_app__(config, tlsrepo, enddevices)
    ssl_context = __build_ssl_context__(tlsrepo)

    try:
        host, port = config.server_hostname.split(":")
    except ValueError:
        # host and port not available
        host = config.server_hostname
        port = 8443

    PeerCertWSGIRequestHandler.debug_device = config.debug_device
    PeerCertWSGIRequestHandler.tlsrepo = tlsrepo
    app.run(host=host,
            ssl_context=ssl_context,
            request_handler=PeerCertWSGIRequestHandler,
            port=port,
            **kwargs)


def build_server(config: ServerConfiguration,
                 tlsrepo: TLSRepository,
                 enddevices: EndDevices, **kwargs) -> BaseWSGIServer:

    app = __build_app__(config, tlsrepo, enddevices)
    ssl_context = __build_ssl_context__(tlsrepo)

    try:
        host, port = config.server_hostname.split(":")
    except ValueError:
        # host and port not available
        host = config.server_hostname
        port = 8443

    return make_server(app=app,
                       host=host,
                       ssl_context=ssl_context,
                       request_handler=PeerCertWSGIRequestHandler,
                       port=port, **kwargs)
