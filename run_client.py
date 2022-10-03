import atexit
import ssl
import sys
from http.client import HTTPConnection, HTTPSConnection
from pathlib import Path
from pprint import pprint
import argparse

import OpenSSL

from ieee_2030_5.client import IEEE2030_5_Client


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("--cert", required=True,
                        help="Certificate file to use to connect to the 2030.5 server")
    parser.add_argument("--key", required=True,
                        help="Key file to use to connect to the 2030.5 server")
    parser.add_argument("--cacert", required=True,
                        help="CA Certificate file to use to connect to the 2030.5 server")
    parser.add_argument("--server", required=True,
                        help="The 2030.5 server to connect to")
    parser.add_argument("--port", default=443, type=int,
                        help="The port to connect to the 2030.5 server on. (Default 443)")
    parser.add_argument("--pin", required=True,
                        help="PIN to validate that the client is registered with the server.")

    opts = parser.parse_args()

    keys = "cert", "key", "cacert"

    for k in keys:
        # path that is going to be expanded and resolved
        test_path = getattr(opts, k)
        setattr(opts, k, str(Path(test_path).expanduser().resolve(strict=True)))

    x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM,
                                           open(opts.cert, "rb").read())

    print(f"Connecting to: {opts.server}:{opts.port} using subject: {x509.get_subject().CN}")

    client = IEEE2030_5_Client(cafile=opts.cacert,
                               server_hostname=opts.server,
                               keyfile=opts.key,
                               certfile=opts.cert,
                               server_ssl_port=int(opts.port))

    dcap = client.device_capability()
    devices = client.end_devices()

    if not client.is_end_device_registered(devices.EndDevice[0], opts.pin):
        print(f"End device ({x509.get_subject().CN}) not registered on server.  Check pin.")
        sys.exit(0)

    print(devices.EndDevice[0])



    # OpenSSL.crypto.
    # x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_ASN1, x509_binary)
    #         environ['ieee_2030_5_peercert'] = x509
    #         environ['ieee_2030_5_subject'] = x509.get_subject().CN

# cafile = "/home/gridappsd/tls/certs/ca.crt"
# certfile = "/home/gridappsd/tls/certs/dev1.crt"
# keyfile = "/home/gridappsd/tls/private/dev1.pem"
# hostname = "gridappsd_dev_2004"
# #hostname = "google.com"
# port = 8443
#
# context = ssl.SSLContext(ssl.PROTOCOL_TLS)
# context.verify_mode = ssl.CERT_OPTIONAL
# context.load_verify_locations(cafile=cafile)
#
# # Loads client information from the passed cert and key files. For
# # client side validation.
# context.load_cert_chain(certfile=certfile, keyfile=keyfile)
#
# conn = HTTPSConnection(host=hostname,
#                        port=port,
#                        context=context)
#
# conn.set_debuglevel(5)
# conn.connect()
# print(id(conn.sock))
# headers = {"Connection": "keep-alive"}
# conn.request("GET", "/admin/index.html", headers=headers) # /admin/index.html", headers=headers)
# resp = conn.getresponse()
# print(resp.read())
# pprint(resp.headers.items())
#
# print(id(conn.sock))
# conn.request("GET", "/", headers=headers)
# print(id(conn.sock))
# resp = conn.getresponse()
# print(resp.read())
# pprint(resp.headers.items())
# conn.close()
