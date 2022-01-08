from http.client import HTTPSConnection
from pathlib import Path
import ssl

from icecream import ic


SERVER_CA_CERT = Path("~/tls/certs/ca.crt").expanduser().resolve()
KEY_FILE = Path("~/tls/private/dev1.me.com.pem").expanduser().resolve()
CERT_FILE = Path("~/tls/certs/dev1.me.com.crt").expanduser().resolve()

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS)
ssl_context.verify_mode = ssl.CERT_REQUIRED
ssl_context.load_verify_locations(cafile=SERVER_CA_CERT)

certfile = CERT_FILE
keyfile = KEY_FILE

ic(certfile, keyfile)

# Loads client information from the passed cert and key files. For
# client side validation.
ssl_context.load_cert_chain(certfile=certfile, keyfile=keyfile)

http_conn = HTTPSConnection(host="me.com",
                            port=8000,
                            context=ssl_context)

http_conn.connect()

http_conn.request(method="GET", url="/", body=None)
response = http_conn.getresponse()
response_data = response.read().decode("utf-8")
ic(response.reason, response.getcode(), response_data)

http_conn.close()

