from http.client import HTTPSConnection
from os import PathLike
from pathlib import Path
import ssl
import atexit
from typing import Optional

from icecream import ic

from IEEE2030_5.xsd_models import DeviceCapability
from IEEE2030_5.end_device import IEEE2030_5Parser


SERVER_CA_CERT = Path("~/tls/certs/ca.crt").expanduser().resolve()
KEY_FILE = Path("~/tls/private/dev1.me.com.pem").expanduser().resolve()
CERT_FILE = Path("~/tls/certs/dev1.me.com.crt").expanduser().resolve()


class IEEE2030_5_Client:
    clients: "IEEE2030_5_Client" = set()

    # noinspection PyUnresolvedReferences
    def __init__(self, cafile: Path, server_hostname: str, keyfile: Path,
                 certfile: Path, ssl_port: Optional[int] = None):
        self._ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS)
        self._ssl_context.verify_mode = ssl.CERT_REQUIRED
        self._ssl_context.load_verify_locations(cafile=cafile)
        ic(certfile, keyfile)
        # Loads client information from the passed cert and key files. For
        # client side validation.
        self._ssl_context.load_cert_chain(certfile=certfile, keyfile=keyfile)

        self._http_conn = HTTPSConnection(host=server_hostname,
                                          port=ssl_port,
                                          context=self._ssl_context)
        self._device_cap: Optional[DeviceCapability] = None
        IEEE2030_5_Client.clients.add(self)

    def request_device_capability(self, url: str = "/dcap") -> DeviceCapability:
        self.__connect__()
        self._device_cap = self.__get_request__(url)
        return self._device_cap

    def request_timelink(self):
        if self._device_cap is None:
            raise ValueError("Request device capability first")
        return self.__get_request__(url=self._device_cap.TimeLink.href)

    def __connect__(self):
        self._http_conn.connect()

    def __get_request__(self, url: str, body=None):
        ic("request:", url, body)
        self._http_conn.request(method="GET", url=url, body=body)
        response = self._http_conn.getresponse()
        response_data = response.read().decode("utf-8")
        ic(response.reason, response.getcode(), response_data)
        data = IEEE2030_5Parser.parse(response_data)
        ic(data.href)
        ic(data.EndDeviceListLink.href)
        return data

    def __close__(self):
        self._http_conn.close()
        self._ssl_context = None
        self._http_conn = None


# noinspection PyTypeChecker
def __release_clients__():
    for x in IEEE2030_5_Client.clients:
        x.__close__()
    IEEE2030_5_Client.clients = None


atexit.register(__release_clients__)

#
# ssl_context = ssl.create_default_context(cafile=str(SERVER_CA_CERT))
#
#
# con = HTTPSConnection("me.com", 8000,
#                       key_file=str(KEY_FILE),
#                       cert_file=str(CERT_FILE),
#                       context=ssl_context)
# con.request("GET", "/dcap")
# print(con.getresponse().read())
# con.close()


if __name__ == '__main__':
    h = IEEE2030_5_Client(cafile=SERVER_CA_CERT, server_hostname="me.com",
                          ssl_port=8000, keyfile=KEY_FILE, certfile=CERT_FILE)
    # h2 = IEEE2030_5_Client(cafile=SERVER_CA_CERT, server_hostname="me.com", ssl_port=8000,
    #                        keyfile=KEY_FILE, certfile=KEY_FILE)
    dcap = h.request_device_capability()
    tl = h.request_timelink()
    print(dcap.pollRate)
    print(IEEE2030_5_Client.clients)