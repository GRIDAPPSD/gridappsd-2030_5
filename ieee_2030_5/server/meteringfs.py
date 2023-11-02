"""
This module handles MirrorUsagePoint and UsagePoint constructs for a server.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

from flask import Response, request
from werkzeug.exceptions import BadRequest

import ieee_2030_5.adapters as adpt
import ieee_2030_5.hrefs as hrefs
import ieee_2030_5.models as m
from ieee_2030_5.data.indexer import get_href
from ieee_2030_5.server.base_request import RequestOp
from ieee_2030_5.server.uuid_handler import UUIDHandler
from ieee_2030_5.utils import dataclass_to_xml, xml_to_dataclass


class Error(Exception):
    pass


@dataclass
class ResponseStatus:
    location: str
    status: str


class UsagePointRequest(RequestOp):

    def get(self) -> Response:

        start = int(request.args.get("s", 0))
        limit = int(request.args.get("l", 1))
        after = int(request.args.get("a", 0))
        parsed = hrefs.ParsedUsagePointHref(request.path)

        handled = False
        sort_by = []
        reversed = True

        if parsed.has_reading_list():
            sort_by = "timePeriod.start"
            if handled := parsed.reading_index is not None:
                obj = adpt.ListAdapter.get(parsed.last_list(), parsed.reading_index)

        elif parsed.has_reading_set_list():
            sort_by = "timePeriod.start"
            if handled := parsed.reading_set_index is not None:
                obj = adpt.ListAdapter.get(parsed.last_list(), parsed.reading_set_index)

        elif parsed.has_meter_reading_list():
            if handled := parsed.has_reading_type():
                obj = get_href(request.path)
            elif handled := parsed.meter_reading_index is not None:
                obj = adpt.ListAdapter.get(parsed.last_list(), parsed.meter_reading_index)
        else:
            obj = adpt.ListAdapter.get_resource_list(request.path,
                                                     start=start,
                                                     limit=limit,
                                                     after=after,
                                                     reverse=reversed)

        if not handled:
            obj = adpt.ListAdapter.get_resource_list(request.path,
                                                     start=start,
                                                     limit=limit,
                                                     after=after,
                                                     sort_by=sort_by,
                                                     reverse=reversed)
        # # /upt
        # if not parsed.has_usage_point_index():
        #     obj = adpt.UsagePointAdapter.fetch_all(m.UsagePointList(request.path),
        #                                            start=start,
        #                                            limit=limit,
        #                                            after=after)
        # elif parsed.has_meter_reading_list() and not parsed.meter_reading_index:
        #     obj = adpt.MirrorUsagePointAdapter.fetch_all(m.MeterReadingList(request.path),
        #                                                  start=start,
        #                                                  limit=limit,
        #                                                  after=after)

        # else:
        #     obj = adpt.UsagePointAdapter.fetch(parsed.usage_point_index)

        # if parsed.has_extra():
        #     obj = get_href(request.path)

        return self.build_response_from_dataclass(obj)


class MirrorUsagePointRequest(RequestOp):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get(self) -> Response:
        pth_info = request.path

        if not pth_info.startswith(hrefs.DEFAULT_MUP_ROOT):
            raise ValueError(f"Invalid path for {self.__class__} {request.path}")

        mup_href = hrefs.ParsedUsagePointHref(request.path)

        if not mup_href.has_usage_point_index():
            # /mup
            mup: m.MirrorUsagePointList = adpt.ListAdapter.get_resource_list(request.path)
            # Because our resource_list doesn't include other properties than the list we set
            # them here before returning.
            mup.pollRate = self.server_config.mirror_usage_point_post_rate
        else:
            # /mup_0
            mup = adpt.ListAdapter.get(hrefs.DEFAULT_MUP_ROOT, mup_href.usage_point_index)

        return self.build_response_from_dataclass(mup)

    def post(self) -> Response:
        xml = request.data.decode('utf-8')
        data = xml_to_dataclass(request.data.decode('utf-8'))
        data_type = type(data)
        if data_type not in (m.MirrorUsagePoint, m.MirrorReadingSet, m.MirrorMeterReading):
            raise BadRequest()

        pth_info = request.path
        pths = pth_info.split(hrefs.SEP)
        if len(pths) == 1 and data_type is not m.MirrorUsagePoint:
            # Check to make sure not a new mrid
            raise BadRequest("Must post MirrorUsagePoint to top level only")

        # Creating a new mup
        if data_type == m.MirrorUsagePoint:
            if data.postRate is None:
                data.postRate = self.server_config.mirror_usage_point_post_rate
            result = adpt.create_mirror_usage_point(mup=data)
            #result = adpt.MirrorUsagePointAdapter.create(mup=data)
        else:
            result = adpt.create_mirror_meter_reading(mup_href=request.path, mmr_input=data)

        if result.success:
            status = '204' if result.was_update == True else '201'
        else:
            status = '405'

        if status.startswith('20'):
            if result.location:
                return Response(headers={'Location': result.location}, status=status)
            return Response(headers={'Location': result.an_object.href}, status=status)
        else:
            return Response(result.an_object, status=status)
