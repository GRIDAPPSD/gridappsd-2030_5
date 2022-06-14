from typing import Optional

from flask import Response, request

from ieee_2030_5 import hrefs
from ieee_2030_5.models import Registration
from ieee_2030_5.server.base_request import RequestOp
from ieee_2030_5.utils import dataclass_to_xml


class EDev(RequestOp):
    """
    Class supporting end devices and any of the subordinate calls to it.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get(self, index: Optional[int] = None, category: Optional[str] = None) -> Response:
        """
        Supports the get request for end_devices(EDev) and end_device_list_link.

        Paths:
            /edev
            /edev/0
            /edev/0/di

        """
        pth = request.environ['PATH_INFO']

        if not pth.startswith(hrefs.edev):
            raise ValueError(f"Invalid path for {self.__class__} {request.path}")

        # split returns a single value whether or not there was any characters found. if
        # this is the case then we want to return the list of the end devices.
        if index is None:
            retval = self._end_devices.get_end_device_list(self.lfid)
        else:
            # This should mean we have an index of an end device that we are going to return
            if category is None:
                retval = self._end_devices.get(index)
            else:

                if category == 'reg':
                    retval = self._reg(index)

                else:
                    raise NotImplementedError()

        retval = dataclass_to_xml(retval)
        return Response(retval)
        # return dataclass_to_xml(self._end_devices.get())

    def _reg(self, index) -> Registration:
        reg = self._end_devices.get_registration(index)
        return reg
