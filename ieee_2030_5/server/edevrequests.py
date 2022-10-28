from typing import Optional

import werkzeug.exceptions
from flask import Response, request

from ieee_2030_5 import hrefs
from ieee_2030_5.data.indexer import get_href
import ieee_2030_5.models as m
from ieee_2030_5.models import Registration
from ieee_2030_5.server.base_request import RequestOp
from ieee_2030_5.utils import dataclass_to_xml, xml_to_dataclass


class DERRequests(RequestOp):
    """
    Class supporting end devices and any of the subordinate calls to it.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get(self, edev_id: Optional[int] = None, id: Optional[int] = None) -> Response:
        return Response("Foo")


class EDevRequests(RequestOp):
    """
    Class supporting end devices and any of the subordinate calls to it.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def post(self, path: Optional[str] = None) -> Response:
        """
        Handle post request to /edev
        
        The expectation is that data will be an xml object like the following:
        
            <EndDevice xmlns="urn:ieee:std:2030.5:ns">
                <sFDI>231589308001</sFDI>
                <changedTime>0</changedTime>
            </EndDevice>
        
        Args:
            path: 

        Returns:

        """
        # request.data should have xml data.
        if not request.data:
            raise werkzeug.exceptions.Forbidden()
        
        ed = xml_to_dataclass(request.data.decode('utf-8'))

        if not isinstance(ed, m.EndDevice):
            raise werkzeug.exceptions.Forbidden()

        # TODO Use the passed sfdi from the data to get the correct addition to the data
        # there is currently a discrepancy between our generation of sfdi and the client.
        device_id = request.environ['ieee_2030_5_subject']

        # This is what we should be using to get the device id of the registered end device.
        # device_id = self.tls_repo.find_device_id_from_sfdi(ed.sFDI)
        ed.lFDI = self.tls_repo.lfdi(device_id)
        if end_device := self._end_devices.get_device_by_lfdi(ed.lFDI):
            status = 200
            ed_href = end_device.href
        else:
            ed_href = self._end_devices.add_end_device(ed)
            status = 201

        return Response(status=status, headers={'Location': ed_href})

    def get(self, path: Optional[str] = None) -> Response:
        """
        Supports the get request for end_devices(EDev) and end_device_list_link.

        Paths:
            /edev
            /edev/0
            /edev/0/di
            /edev/0/reg

        """
        pth = request.environ['PATH_INFO']

        if not pth.startswith(hrefs.DEFAULT_EDEV_ROOT):
            raise ValueError(f"Invalid path for {self.__class__} {request.path}")

        # top level /edev should return specific end device list based upon
        # the lfdi of the connection.
        if pth == hrefs.DEFAULT_EDEV_ROOT:
            retval = self._end_devices.get_end_device_list(self.lfdi)
            retval.EndDevice[0].lFDI = retval.EndDevice[0].lFDI.decode('utf-8')
        else:
            retval = get_href(pth)
            retval.lFDI = retval.lFDI.decode('utf-8')
        return self.build_response_from_dataclass(retval)


class SDevRequests(RequestOp):
    """
    SelfDevice is an alias for the end device of a client.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get(self) -> Response:
        """
        Supports the get request for end_devices(EDev) and end_device_list_link.

        Paths:
            /sdev

        """
        end_device = self._end_devices.get_end_device_list(self.lfdi).EndDevice[0]
        return self.build_response_from_dataclass(end_device)
