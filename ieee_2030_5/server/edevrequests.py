from typing import Optional

from flask import Response, request

from ieee_2030_5 import hrefs
from ieee_2030_5.data.indexer import get_href
from ieee_2030_5.models import Registration
from ieee_2030_5.server.base_request import RequestOp
from ieee_2030_5.utils import dataclass_to_xml


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

    def get(self, path) -> Response:
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
        # the lfid of the connection.
        if pth == hrefs.DEFAULT_EDEV_ROOT:
            retval = self._end_devices.get_end_device_list(self.lfid)
        else:
            retval = get_href(pth)

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
        end_device = self._end_devices.get_end_device_list(self.lfid).EndDevice[0]
        return self.build_response_from_dataclass(end_device)
