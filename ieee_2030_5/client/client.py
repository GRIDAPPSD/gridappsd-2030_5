from __future__ import annotations

from http.client import HTTPSConnection
from os import PathLike
from pathlib import Path
import ssl
import atexit
from typing import Optional, Dict, Tuple
import xml.dom.minidom

import xsdata

from ieee_2030_5.models import DeviceCapability, EndDeviceListLink, MirrorUsagePointList, MirrorUsagePoint, \
    UsagePointList, EndDevice, Registration, FunctionSetAssignmentsListLink, Time

from ieee_2030_5.utils import dataclass_to_xml, parse_xml


class IEEE2030_5_Client:
    clients: set[IEEE2030_5_Client] = set()

    # noinspection PyUnresolvedReferences
    def __init__(self,
                 cafile: Path,
                 server_hostname: str,
                 keyfile: Path,
                 certfile: Path,
                 hostname: str,
                 server_ssl_port: Optional[int] = 443,
                 debug: bool = True):

        assert cafile.exists(), f"cafile doesn't exist ({cafile})"
        assert keyfile.exists(), f"keyfile doesn't exist ({keyfile})"
        assert certfile.exists(), f"certfile doesn't exist ({certfile})"
        assert hostname, "hostname not specified"

        self._ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS)
        self._ssl_context.verify_mode = ssl.CERT_REQUIRED
        self._ssl_context.load_verify_locations(cafile=cafile)

        # Loads client information from the passed cert and key files. For
        # client side validation.
        self._ssl_context.load_cert_chain(certfile=certfile, keyfile=keyfile)

        self._http_conn = HTTPSConnection(host=server_hostname,
                                          port=server_ssl_port,
                                          context=self._ssl_context)
        self._device_cap: Optional[DeviceCapability] = None
        self._mup: Optional[MirrorUsagePointList] = None
        self._upt: Optional[UsagePointList] = None
        self._edev: Optional[EndDeviceListLink] = None
        self._end_devices: Optional[EndDeviceListLink] = None
        self._fsa_list: Optional[FunctionSetAssignmentsListLink] = None

        self._hostname = hostname
        self._debug = debug
        IEEE2030_5_Client.clients.add(self)

    @property
    def hostname(self) -> str:
        return self._hostname

    @property
    def http_conn(self) -> HTTPSConnection:
        if self._http_conn.sock is None:
            self._http_conn.connect()
        return self._http_conn

    def new_uuid(self, url: str = "/uuid") -> str:
        res = self.__get_request__(url)
        return res

    def end_devices(self) -> EndDeviceListLink:
        self._end_devices = self.__get_request__(self._device_cap.EndDeviceListLink.href)
        return self._end_devices

    def end_device(self, index: Optional[int] = 0) -> EndDevice:
        if not self._end_devices:
            self.end_devices()

        return self._end_devices.EndDevice[index]

    def self_device(self) -> EndDevice:
        if not self._device_cap:
            self.device_capability()

        return self.__get_request__(self._device_cap.SelfDeviceLink.href)

    def function_set_assignment(self) -> FunctionSetAssignmentsListLink:
        fsa_list = self.__get_request__(self.self_device().FunctionSetAssignmentsListLink.href)
        return fsa_list

    def device_capability(self, url: str = "/dcap") -> DeviceCapability:
        self._device_cap = self.__get_request__(url)
        return self._device_cap

    def time(self) -> Time:
        timexml = self.__get_request__(self._device_cap.TimeLink.href)
        return timexml

    def mirror_usage_point_list(self) -> MirrorUsagePointList:
        self._mup = self.__get_request__(self._device_cap.MirrorUsagePointListLink.href)
        return self._mup

    def usage_point_list(self) -> UsagePointList:
        self._upt = self.__get_request__(self._device_cap.UsagePointListLink.href)
        return self._upt

    def registration(self, end_device: EndDevice) -> Registration:
        reg = self.__get_request__(end_device.RegistrationLink.href)
        return reg

    def timelink(self):
        if self._device_cap is None:
            raise ValueError("Request device capability first")
        return self.__get_request__(url=self._device_cap.TimeLink.href)

    def request(self, endpoint: str, body: dict = None, method: str = "GET",
                headers: dict = None):

        if method.upper() == 'GET':
            return self.__get_request__(endpoint, body, headers=headers)

        if method.upper() == 'POST':
            print("Doing post")
            return self.__post__(endpoint, body, headers=headers)

    def create_mirror_usage_point(self, mirror_usage_point: MirrorUsagePoint) -> Tuple[int, str]:
        data = dataclass_to_xml(mirror_usage_point)
        resp = self.__post__(self._device_cap.MirrorUsagePointListLink.href, data=data)
        return resp.status, resp.headers['Location']

    def __post__(self, url: str, data=None, headers: Optional[Dict[str, str]]=None):
        if not headers:
            headers = {'Content-Type': 'text/xml'}

        self.http_conn.request(method="POST", headers=headers,
                               url=url, body=data)
        response = self._http_conn.getresponse()
        # response_data = response.read().decode("utf-8")

        return response

    def __get_request__(self, url: str, body=None, headers: dict = None):
        if headers is None:
            headers = {}

        if self._debug:
            print(f"----> GET REQUEST")
            print(f"url: {url} body: {body}")
        self.http_conn.request(method="GET", url=url, body=body, headers=headers)
        response = self._http_conn.getresponse()
        response_data = response.read().decode("utf-8")

        response_obj = None
        try:
            response_obj = parse_xml(response_data)
            resp_xml = xml.dom.minidom.parseString(response_data)
            if resp_xml and self._debug:
                print(f"<---- GET RESPONSE")
                print(f"{resp_xml.toprettyxml()}")

        except xsdata.exceptions.ParserError as ex:
            if self._debug:
                print(f"<---- GET RESPONSE")
                print(f"{response_data}")
            response_obj = response_data

        return response_obj

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
    SERVER_CA_CERT = Path("~/tls/certs/ca.crt").expanduser().resolve()
    KEY_FILE = Path("~/tls/private/_def62366-746e-4fcb-b3ee-ebebb90d72d4.pem").expanduser().resolve()
    CERT_FILE = Path("~/tls/certs/_def62366-746e-4fcb-b3ee-ebebb90d72d4.crt").expanduser().resolve()

    h = IEEE2030_5_Client(cafile=SERVER_CA_CERT,
                          server_hostname="gridappsd_dev_2004",
                          server_ssl_port=8443,
                          keyfile=KEY_FILE,
                          certfile=CERT_FILE,
                          hostname='_def62366-746e-4fcb-b3ee-ebebb90d72d4')
    # h2 = IEEE2030_5_Client(cafile=SERVER_CA_CERT, server_hostname="me.com", ssl_port=8000,
    #                        keyfile=KEY_FILE, certfile=KEY_FILE)

    dcap = h.device_capability()
    # get device list
    dev_list = h.request(dcap.EndDeviceListLink.href).EndDevice

    ed = h.request(dev_list[0].href)
    print(ed)
    #
    # print(dcap.mirror_usage_point_list_link)
    # # print(h.request(dcap.mirror_usage_point_list_link.href))
    # print(h.request("/dcap", method="post"))


    # tl = h.timelink()
    #print(IEEE2030_5_Client.clients)
