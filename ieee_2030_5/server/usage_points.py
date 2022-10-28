"""
This module handles MirrorUsagePoint and UsagePoint constructs for a server.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, List

from flask import Response, request
from werkzeug.exceptions import BadRequest

from ieee_2030_5.models import MirrorUsagePointList, MirrorUsagePoint, MirrorReadingSet, UsagePointList, UsagePoint
from ieee_2030_5.server.uuid_handler import UUIDHandler
from ieee_2030_5.server.base_request import RequestOp
from ieee_2030_5 import hrefs
from ieee_2030_5.utils import dataclass_to_xml, xml_to_dataclass

class Error(Exception):
    pass

@dataclass
class ResponseStatus:
    location: str
    status: str


class UsagePointsContainer:
    __upt__: Dict[bytes, UsagePoint] = {}
    __mup__: Dict[bytes, MirrorUsagePoint] = {}
    __sorted_mrid__: List = []
    __mup_href__: Dict[str, MirrorUsagePoint] = {}
    __mup_readings__: Dict[bytes, MirrorReadingSet] = {}

    def get_mup_list(self,
                     start: Optional[int] = None,
                     after: Optional[int] = None,
                     length: Optional[int] = None) -> MirrorUsagePointList:

        if start is not None and after is not None:
            # after takes precedence
            index = after + 1 + start
        elif start is not None:
            index = start
        elif after is not None:
            index = after + 1
        else:
            index = 0

        mup_list = MirrorUsagePointList(all=len(self.__sorted_mrid__))

        if length is None:
            for x in self.__sorted_mrid__[index: len(self.__sorted_mrid__)]:
                mup_list.MirrorUsagePoint.append(self.__mup__[x])
        elif length - index < len(self.__sorted_mrid__):
            for x in self.__sorted_mrid__[index: index + length]:
                mup_list.MirrorUsagePoint.append(self.__mup__[x])
        else:
            for x in self.__sorted_mrid__[index:]:
                mup_list.MirrorUsagePoint.append(self.__mup__[x])

        mup_list.results = len(mup_list.MirrorUsagePoint)

        return mup_list

    def get_upt_list(self) -> UsagePointList:
        pass

    def get_mup_href(self, href: str) -> Optional[MirrorUsagePoint]:
        return self.__mup_href__.get(href)

    def create_reading_set(self, mup_href: str, mrs: MirrorReadingSet) -> ResponseStatus | Error:
        mup = point_container.get_mup_href(mup_href)
        if mup is None:
            return Error(f"No MirrorUsagePoint found at posted: {mup_href}")


        #     point_container.create_reading_set(mup_href=)

    def create_update_mup(self, mup: MirrorUsagePoint) -> ResponseStatus | Error:
        required = ["mRID", "MirrorMeterReading", "deviceLFDI"]
        invalid = []
        for p in required:
            if not getattr(mup, p):
                invalid.append(f"{p} not specified for MirrorUsagePoint")
        # Error out top level required data
        if invalid:
            return Error("\n".join(invalid))

        required_meter_reading = ["mRID", "ReadingType"]
        for indx, reading in enumerate(mup.MirrorMeterReading):
            for p in required_meter_reading:
                if not getattr(reading, p):
                    invalid.append(f"Reading {indx} missing {p}")
        # Error out if meter reading invalid.
        if invalid:
            return Error("\n".join(invalid))

        created = self.__mup__.get(mup.mRID) is None
        self.__mup__[mup.mRID] = mup
        self.__sorted_mrid__.append(mup.mRID)
        # Sort mrids descending
        self.__sorted_mrid__ = sorted(self.__sorted_mrid__, reverse=True)

        item_in_list = 0
        for indx, mrid in enumerate(self.__sorted_mrid__):
            if mrid == mup.mRID:
                item_in_list = indx
                break
        mup.href = hrefs.build_link(hrefs.mup, item_in_list)
        return ResponseStatus(mup.href,
                              '201 Created' if created else '204 Updated')


point_container = UsagePointsContainer()


class UTP(RequestOp):
    __next_index__: int = 0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get(self) -> Response:
        pass

    def create(self, mrid: Optional[str] = None) -> UsagePoint:
        up = UsagePoint(href=f"{hrefs.build_link(hrefs.upt, UTP.__next_index__)}",
                        mRID=mrid)
        UTP.__next_index__ += 1


class MUP(RequestOp):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get(self, index: Optional[int] = None) -> Response:
        pth_info = request.environ['PATH_INFO']

        if not pth_info.startswith(hrefs.mup):
            raise ValueError(f"Invalid path for {self.__class__} {request.path}")

        if pth_info == hrefs.mup:
            # Getting list of elements
            start = request.args.get("s")
            after = request.args.get("a")
            length = request.args.get("l")
            ret_value = point_container.get_mup_list(start, after, length)
        else:
            ret_value = point_container.get_mup_href(pth_info)
        if ret_value:
            return self.build_response_from_dataclass(ret_value)

        return Response("Not Found", status=404)

    def post(self, index: Optional[int] = None) -> Response:
        xml = request.data.decode('utf-8')
        data = xml_to_dataclass(request.data.decode('utf-8'))
        data_type = type(data)
        if data_type not in (MirrorUsagePoint, MirrorReadingSet):
            raise BadRequest()

        pth_info = request.path
        pths = pth_info.split("/")
        if len(pths) == 1 and data_type is not MirrorUsagePoint:
            # Check to make sure not a new mrid
            raise BadRequest("Must post MirrorUsagePoint to top level only")

        # Creating a new mup
        if data_type == MirrorUsagePoint:
            result = point_container.create_update_mup(mup=data)

        else:
            # MirrorReadingSet
            result = point_container.create_reading_set(mup_href=pth_info, mrs=data)

        if isinstance(result, Error):
            return Response(result.args[1], status=500)
        # Note response to the post is different due to added endpoint.
        return Response(headers={'Location': result.location},
                        status=result.status)
