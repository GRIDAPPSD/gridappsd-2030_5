from typing import Optional

from flask import Response, request
from werkzeug.exceptions import NotFound

import ieee_2030_5.adapters as adpt
from ieee_2030_5.data.indexer import get_href
import ieee_2030_5.hrefs as hrefs
import ieee_2030_5.models as m
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
        
        parsed = hrefs.HrefParser(request.path)
        
        if not parsed.has_index():
            retval = adpt.DERProgramAdapter.fetch_all(m.DERProgramList(href=request.path, all=adpt.DERProgramAdapter.size()))
        elif parsed.count() == 2:
            retval = adpt.DERProgramAdapter.fetch(parsed.at(1))
        else:
            retval = get_href(request.path)
                    
        
        if not retval:
            raise NotFound(f"{request.path}")

        return self.build_response_from_dataclass(retval)
    
