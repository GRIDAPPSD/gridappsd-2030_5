from flask import Flask, render_template, request, redirect
import werkzeug.serving
import werkzeug.exceptions
import ssl
import OpenSSL
from pathlib import Path

from icecream import ic


__all__ = ["run_server"]

# templates = Jinja2Templates(directory="templates")
# from IEEE2030_5.endpoints import dcap, IEEE2030_5Renderer
from ieee_2030_5 import ServerConfiguration
from ieee_2030_5.certs import TLSRepository
from ieee_2030_5.models.end_devices import EndDevices


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

    def make_environ(self):
        """
        The superclass method develops the environ hash that eventually
        forms part of the Flask request object.

        We allow the superclass method to run first, then we insert the
        peer certificate into the hash. That exposes it to us later in
        the request variable that Flask provides
        """
        environ = super(PeerCertWSGIRequestHandler, self).make_environ()
        ic(environ)
        # Assume browser is being hit with things that start with /admin
        if environ['PATH_INFO'].startswith("/admin"):
            return environ

        try:
            x509_binary = self.connection.getpeercert(True)

            x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_ASN1, x509_binary)
            environ['peercert'] = x509
            ic(x509.digest("sha1"))
            ic(x509.get_subject())
            ic(x509.get_serial_number())
            ic()
        except OpenSSL.crypto.Error:
            environ['peercert'] = None

        return environ


def run_server(config: ServerConfiguration, tlsrepo: TLSRepository, enddevices: EndDevices):

    app = Flask(__name__,
                template_folder="/repos/gridappsd-2030_5/templates")

    # to establish an SSL socket we need the private key and certificate that
    # we want to serve to users.
    SERVER_KEY_FILE = str(tlsrepo.server_key_file)
    SERVER_CERT_FILE = str(tlsrepo.server_cert_file)

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
    ssl_context.load_cert_chain(certfile=SERVER_CERT_FILE,
                                keyfile=SERVER_KEY_FILE,
                                # password=app_key_password
                                )
    ssl_context.verify_mode = ssl.CERT_OPTIONAL #  ssl.CERT_REQUIRED

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

    @app.route("/admin/clients")
    def admin_clients():
        clients = tlsrepo.client_list
        return render_template("admin/clients.html", registered=clients, connected=[])

    @app.route("/dcap", methods=['GET'])
    def route_dcap():

        # all routes for 2030.5 should have a peercert so they
        # can be authenticated by the server.
        if not request.environ['peercert']:
            raise werkzeug.exceptions.Forbidden()

        return dcap()

    @app.route("/dcap/edev", defaults={'index': None, 'part': None})
    @app.route("/dcap/edev/<index>", defaults={'part': None})
    @app.route("/dcap/edev/<index>/<part>")
    #@app.route("/dcap/edev/")
    def route_edev(index: int, part: str):
        args = request.args.to_dict()
        return {
            "args": args,
            "index": index,
            "part": part
        }

    try:
        host, port = config.server.split(":")
    except ValueError:
        # host and port not available
        host = config.server
        port = 8443

    app.run(host=host,
            ssl_context=ssl_context,
            request_handler=PeerCertWSGIRequestHandler,
            port=port,
            debug=True)
            #,
            #debug=True)
#
# # start our webserver!
# if __name__ == "__main__":
#     app.run(host="0.0.0.0", ssl_context=ssl_context, request_handler=PeerCertWSGIRequestHandler, port=8000)
