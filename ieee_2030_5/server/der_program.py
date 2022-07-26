from typing import Optional

from flask import Response

from ieee_2030_5.server.base_request import RequestOp


class DERProgramRequests(RequestOp):
    """
    Class supporting end devices and any of the subordinate calls to it.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get(self, edev_id: Optional[int] = None, id: Optional[int] = None) -> Response:
        return Response("Foo")
