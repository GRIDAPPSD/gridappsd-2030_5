import logging
from typing import Optional

import werkzeug.exceptions
from flask import Response, request

import ieee_2030_5.adapters as adpt
import ieee_2030_5.hrefs as hrefs
import ieee_2030_5.models as m
from ieee_2030_5.adapters.enddevices import EndDeviceAdapter
from ieee_2030_5.adapters.fsa import FSAAdapter
from ieee_2030_5.data.indexer import get_href
from ieee_2030_5.models import Registration
from ieee_2030_5.server.base_request import RequestOp
from ieee_2030_5.types_ import Lfdi
from ieee_2030_5.utils import dataclass_to_xml, xml_to_dataclass

_log = logging.getLogger(__name__)

class EDevRequests(RequestOp):
    """
    Class supporting end devices and any of the subordinate calls to it.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
    def put(self) -> Response:
        parsed = hrefs.edev_parse(request.path)
        
        if parsed.der_sub not in [x.value for x in hrefs.DERSubType]:
            raise ValueError("Invalid subtype specified.")
        
        response_code = adpt.DERAdapter.store(parsed, xml_to_dataclass(request.data.decode('utf-8')))
        return Response(status=int(response_code))                                              
                                              
                        
        
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

        ed: m.EndDevice = xml_to_dataclass(request.data.decode('utf-8'))

        if not isinstance(ed, m.EndDevice):
            raise werkzeug.exceptions.Forbidden()

        # This is what we should be using to get the device id of the registered end device.
        device_id = self.tls_repo.find_device_id_from_sfdi(ed.sFDI)
        ed.lFDI = self.tls_repo.lfdi(device_id)
        if end_device := adpt.EndDeviceAdapter.fetch_by_lfdi(ed.lfdi):
            status = 200
            ed_href = end_device.href
        else:
            if not ed.href:
                ed = adpt.EndDeviceAdapter.store(device_id, ed)

            ed_href = ed.href
            status = 201

        return Response(status=status, headers={'Location': ed_href})

    def get(self) -> Response:
        """
        Supports the get request for end_devices(EDev) and end_device_list_link.

        Paths:
            /edev
            /edev/0
            /edev/0/di
            /edev/0/rg
            /edev/0/der

        """
        pth = request.path

        if not pth.startswith(hrefs.DEFAULT_EDEV_ROOT):
            raise ValueError(f"Invalid path for {self.__class__} {request.path}")

        pth_split = pth.split(hrefs.SEP)
        
        if len(pth_split) == 1:
            retval = adpt.EndDeviceAdapter.fetch_list_by_lfdi(self.lfdi)
        elif len(pth_split) == 3:
            if pth_split[2] == "rg":
                retval = adpt.EndDeviceAdapter.fetch_registration(edev_index=int(pth_split[1]))
            elif pth_split[2] == "di":
                retval = "foo"
            elif pth_split[2] == "fsa":
                retval = adpt.EndDeviceAdapter.fetch_fsa_list(edev_index=int(pth_split[1]))
            elif pth_split[2] == "der":
                retval = adpt.DERAdapter.fetch_list(edev_index=int(pth_split[1]))
            
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

class FSARequests(RequestOp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
    def get(self):
        pth_split = request.path.split(hrefs.SEP)
        
        if len(pth_split) == 1:
            retval = FSAAdapter.fetch_list()
        elif len(pth_split) == 2:
            retval = FSAAdapter.fetch_at(int(pth_split[1]))
        elif len(pth_split) == 3:
            retval = EndDeviceAdapter.fetch_fsa_list(edev_index=int(pth_split[1]))
        elif len(pth_split) == 4:
            retval = EndDeviceAdapter.fetch_fsa(edev_index=int(pth_split[1]), fsa_index=int(pth_split[3]))
        else:
            raise ValueError(f"Path split is {pth_split}")
            
        return self.build_response_from_dataclass(retval)