"""
This module handles MirrorUsagePoint and UsagePoint constructs for a server.
"""
from __future__ import annotations

from typing import Dict

from flask import Response, request
from werkzeug.exceptions import BadRequest

from ieee_2030_5.models import MirrorUsagePointList, MirrorUsagePoint, MirrorReadingSet
from ieee_2030_5.models.serializer import parse_xml
from ieee_2030_5.server import RequestOp
from ieee_2030_5 import hrefs
from ieee_2030_5.utils import dataclass_to_xml


class MUP(RequestOp):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Load from repository or data storage after passed data?
        self.__mup_info__: Dict[int, MirrorUsagePointList] = {}
        self.__mup_point_readings__: Dict[str, str | int] = {}
        self._last_added = 0

    def get(self) -> Response:
        pth_info = request.environ['PATH_INFO']

        if not pth_info.startswith(hrefs.mup):
            raise ValueError(f"Invalid path for {self.__class__} {request.path}")

        pths = request.path[len(hrefs.mup.strip()):].split("/")
        an_mup_list = self.__mup_info__.get(self.device_id)

        if not an_mup_list:
            an_mup_list = MirrorUsagePointList(href=pth_info)
            self.__mup_info__[self.device_id] = an_mup_list
            self._last_added += 1

        retval = an_mup_list

        if len(pths) == 2:
            retval = an_mup_list.results[pths[1]]
        return dataclass_to_xml(retval)

    def post(self):
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
        self.__mup_info__[self._last_added] = data

        return Response(headers={'Location': f'/mup/{self._last_added}'},
                        status='201 Created')
