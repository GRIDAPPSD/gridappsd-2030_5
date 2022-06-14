"""
This module handles MirrorUsagePoint and UsagePoint constructs for a server.
"""
from __future__ import annotations

from typing import Dict, Optional

from flask import Response, request
from werkzeug.exceptions import BadRequest

from ieee_2030_5.models import MirrorUsagePointList, MirrorUsagePoint, MirrorReadingSet, UsagePointList
from ieee_2030_5.server.uuid_handler import UUIDHandler
from ieee_2030_5.server.base_request import RequestOp
from ieee_2030_5 import hrefs
from ieee_2030_5.utils import dataclass_to_xml, parse_xml

__mup_info__: Dict[int, MirrorUsagePointList] = {}
__mup_point_readings__: Dict[str, str | int] = {}

__utp_info__: Dict[int, UsagePointList] = {}
__uuid_handler__: UUIDHandler = UUIDHandler()


class UTP(RequestOp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get(self) -> Response:
        pass


class MUP(RequestOp):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._last_added = 0

    def get(self, index: Optional[int] = None) -> Response:
        pth_info = request.environ['PATH_INFO']

        if not pth_info.startswith(hrefs.mup):
            raise ValueError(f"Invalid path for {self.__class__} {request.path}")

        pths = request.path[len(hrefs.mup.strip()):].split("/")
        an_mup_list = __mup_info__.get(self.device_id)

        if not an_mup_list:
            an_mup_list = MirrorUsagePointList(href=pth_info)
            __mup_info__[self.device_id] = an_mup_list
            self._last_added += 1

        retval = an_mup_list

        if len(pths) == 2:
            retval = an_mup_list.results[pths[1]]
        return Response(dataclass_to_xml(retval), headers={'Content-Type': 'application/xml'})

    def post(self, index: Optional[int] = None) -> Response:
        xml = request.data.decode('utf-8')
        data = parse_xml(request.data.decode('utf-8'))
        data_type = type(data)
        if data_type not in (MirrorUsagePoint, MirrorReadingSet):
            raise BadRequest()

        pth_info = request.path
        pths = pth_info.split("/")
        if len(pths) == 1 and data_type is not MirrorUsagePoint:
            # Check to make sure not a new mrid
            raise BadRequest("Must post MirrorUsagePoint to top level only")

        # Creating a new mup
        self._last_added += 1
        __mup_info__[self._last_added] = data

        return Response(headers={'Location': f'{hrefs.mup}/{self._last_added}'},
                        status='201 Created')
