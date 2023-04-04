from typing import Optional

from flask import Response, request

import ieee_2030_5.adapters as adpt
import ieee_2030_5.hrefs as hrefs
from ieee_2030_5.server.base_request import RequestOp


class DERRequests(RequestOp):
    """
    Class supporting end devices and any of the subordinate calls to it.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get(self) -> Response:
        
        if not request.path.startswith(hrefs.DEFAULT_DER_ROOT):
            raise ValueError(f"Invalid path for {self.__class__} {request.path}")
        
        pth_split = request.path.split(hrefs.SEP)
        
        if len(pth_split) == 1:
            # TODO Add arguments
            value = adpt.DERAdapter.fetch_list()
        else:
            value = adpt.DERAdapter.fetch_at(int(pth_split[1]))

        return self.build_response_from_dataclass(value)
    

class DERProgramRequests(RequestOp):
    """
    Class supporting end devices and any of the subordinate calls to it.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get(self) -> Response:
        pth = request.path
        
        if not pth.startswith(hrefs.DEFAULT_DER_ROOT):
            raise ValueError("Invalid path passed to ")
        obj = self.get_path("foo")
        return self.build_response_from_dataclass(obj)
    
