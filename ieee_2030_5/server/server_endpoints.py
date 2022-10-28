from __future__ import annotations

import json
from datetime import datetime, timedelta
import logging
from typing import Optional

import pytz
import tzlocal
import werkzeug.exceptions
from flask import Flask, Response, request
from werkzeug.exceptions import Forbidden
from werkzeug.routing import BaseConverter

from ieee_2030_5.config import ServerConfiguration
from ieee_2030_5.certs import TLSRepository
from ieee_2030_5.data.indexer import get_href, get_href_filtered
from ieee_2030_5.models import Time, DERCurveList, DERProgramList
from ieee_2030_5.server.server_constructs import EndDevices
import ieee_2030_5.hrefs as hrefs
from ieee_2030_5.server.der_program import DERProgramRequests
from ieee_2030_5.server.edevrequests import EDevRequests, SDevRequests, DERRequests
from ieee_2030_5.server.base_request import RequestOp
from ieee_2030_5.server.uuid_handler import UUIDHandler

# module level instance of hrefs class.
from ieee_2030_5.server.usage_points import MUP, UTP
from ieee_2030_5.types_ import TimeOffsetType, format_time
from ieee_2030_5.utils import dataclass_to_xml

_log = logging.getLogger(__name__)


class Admin(RequestOp):
    def get(self):
        if not self.is_admin_client:
            raise Forbidden()
        return Response("We are able to do stuff here")

    def post(self):
        if not self.is_admin_client:
            raise Forbidden()
        return Response(json.dumps({'abc': 'def'}), headers={'Content-Type': 'application/json'})


class Dcap(RequestOp):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get(self) -> Response:
        # TODO: Test for allowed dcap here.
        # if not self._end_devices.allowed_to_connect(self.lfdi):
        #     raise werkzeug.exceptions.Unauthorized()

        return self.build_response_from_dataclass(self._end_devices.get_device_capability(self.lfdi))


class TimeRequest(RequestOp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get(self) -> Response:
        # TODO fix for new stuff.
        # local_tz = datetime.now().astimezone().tzinfo
        # now_local = datetime.now().replace(tzinfo=local_tz)

        now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
        # now_utc = pytz.utc.localize(datetime.utcnow())
        local_tz = pytz.timezone(tzlocal.get_localzone().zone)
        now_local = datetime.now().replace(tzinfo=local_tz)

        start_dst_utc, end_dst_utc = [
            dt for dt in local_tz._utc_transition_times if dt.year == now_local.year
        ]

        utc_offset = local_tz.utcoffset(start_dst_utc - timedelta(days=1))
        dst_offset = local_tz.utcoffset(start_dst_utc + timedelta(days=1)) - utc_offset
        local_but_utc = datetime.now().replace(tzinfo=pytz.utc)

        tm = Time(currentTime=format_time(now_utc),
                  dstEndTime=format_time(end_dst_utc.replace(tzinfo=pytz.utc)),
                  dstOffset=TimeOffsetType(int(dst_offset.total_seconds())),
                  localTime=format_time(local_but_utc),
                  quality=None,
                  tzOffset=TimeOffsetType(utc_offset.total_seconds()))

        return self.build_response_from_dataclass(tm)


class ServerList(RequestOp):
    def __init__(self, list_type: str, **kwargs):
        super().__init__(**kwargs)
        self._list_type = list_type

    def get(self) -> Response:
        response = None
        if self._list_type == 'EndDevice':
            response = self._end_devices.get_end_device_list(self.lfdi)

        if response:
            response = dataclass_to_xml(response)

        return response


class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]
        _log.debug(f"regex is {self.regex}")


class ServerEndpoints:

    def __init__(self, app: Flask, end_devices: EndDevices, tls_repo: TLSRepository, config: ServerConfiguration):
        self.end_devices = end_devices
        self.config = config
        self.tls_repo = tls_repo
        self.mimetype = "text/xml"
        self.app: Flask = app
        self.app.url_map.converters['regex'] = RegexConverter

        _log.debug(f"Adding rule: {hrefs.uuid_gen} methods: {['GET']}")
        app.add_url_rule(hrefs.uuid_gen, view_func=self._generate_uuid)
        _log.debug(f"Adding rule: {hrefs.get_dcap_href()} methods: {['GET']}")
        app.add_url_rule(hrefs.get_dcap_href(), view_func=self._dcap)
        _log.debug(f"Adding rule: {hrefs.get_time_href()} methods: {['GET']}")
        app.add_url_rule(hrefs.get_time_href(), view_func=self._tm)
        _log.debug(f"Adding rule: {hrefs.sdev} methods: {['GET']}")
        app.add_url_rule(hrefs.sdev, view_func=self._sdev)
        # _log.debug(f"Adding rule: {hrefs.derp} methods: {['GET']}")
        # app.add_url_rule(hrefs.derp, view_func=self._derp)

        # All the energy devices
        app.add_url_rule(f"/{hrefs.EDEV}", methods=["GET", "POST"],
                         view_func=self._edev)
        app.add_url_rule(f"/<regex('{hrefs.EDEV}{hrefs.MATCH_REG}'):path>",
                         view_func=self._edev, methods=["GET"])
        app.add_url_rule(f"/<regex('{hrefs.DER}{hrefs.MATCH_REG}'):path>",
                         view_func=self._der, methods=["GET"])
        app.add_url_rule(f"/<regex('{hrefs.MUP}{hrefs.MATCH_REG}'):path>",
                         view_func=self._mup, methods=["GET"])
        app.add_url_rule(f"/<regex('{hrefs.CURVE}{hrefs.MATCH_REG}'):path>",
                         view_func=self._curves, methods=["GET"])
        app.add_url_rule(f"/<regex('{hrefs.PROGRAM}{hrefs.MATCH_REG}'):path>",
                         view_func=self._programs, methods=["GET"])
        # rulers = (
        #     (hrefs.der_urls, self._der),
        #     #(hrefs.edev_urls, self._edev),
        #     (hrefs.mup_urls, self._mup),
        #     (hrefs.curve_urls, self._curves),
        #     (hrefs.program_urls, self._programs)
        # )
        #
        # for endpoints, view_func in rulers:
        #     # Item should either be a single rule or a rule with a second element having the methods
        #     # in it.
        #     # edev = [
        #     #   /edev,
        #     #   (f"/edev/<int: index>", ["GET", "POST"])
        #     # ]
        #     for item in endpoints:
        #         try:
        #             rule, methods = item
        #         except ValueError:
        #             rule = item
        #             methods = ["GET"]
        #         _log.debug(f"Adding rule: {rule} methods: {methods}")
        #         app.add_url_rule(rule, view_func=view_func, methods=methods)
        #
        # self.add_endpoint(hrefs.dcap, view_func=self._dcap)
        # self.add_endpoint(hrefs.edev, view_func=self._edev)
        # self.add_endpoint(hrefs.mup, view_func=self._mup, methods=['GET', 'POST'])
        # self.add_endpoint(hrefs.uuid_gen, view_func=self._generate_uuid)
        # app.add_url_rule(hrefs.rsps, view_func=None)
        # self.add_endpoint(hrefs.tm, view_func=self._tm)
        #
        # for index, ed in end_devices.all_end_devices.items():
        #     self.add_endpoint(hrefs.edev + f"/{index}", view_func=self._edev)
        #     self.add_endpoint(hrefs.mup + f"/{index}", view_func=self._mup)

    def _foo(self, bar):
        return Response("Foo Response")

    def _generate_uuid(self) -> Response:
        return Response(UUIDHandler().generate())
    #
    # def _admin(self) -> Response:
    #     return Admin(server_endpoints=self).execute()

    def _upt(self, path) -> Response:
        return UTP(server_endpoints=self).execute(path=path)

    def _mup(self, path) -> Response:
        return MUP(server_endpoints=self).execute(path=path)

    def _der(self, path) -> Response:
        return DERRequests(server_endpoints=self).execute(path=path)

    def _dcap(self) -> Response:
        return Dcap(server_endpoints=self).execute()

    def _edev(self, path: Optional[str] = None) -> Response:
        return EDevRequests(server_endpoints=self).execute(path=path)
    # def _edev(self, index: Optional[int] = None, category: Optional[str] = None) -> Response:
    #     return EDevRequests(server_endpoints=self).execute(index=index, category=category)

    def _sdev(self) -> Response:
        return SDevRequests(server_endpoints=self).execute()

    def _tm(self) -> Response:
        return TimeRequest(server_endpoints=self).execute()

    def _derp(self, path) -> Response:
        return DERProgramRequests(server_endpoints=self).execute(path=path)

    def _curves(self, path) -> Response:
        pth = request.environ['PATH_INFO']
        obj = get_href(pth)
        # if index is None:
        #     items = get_href_filtered(hrefs.curve)
        #     curve_list = DERCurveList(DERCurve=items, all=len(items), href=request.path, results=len(items))
        #     response = Response(dataclass_to_xml(curve_list))
        # else:
        #     response = Response(dataclass_to_xml(get_href(request.path)))
        return RequestOp(server_endpoints=self).build_response_from_dataclass(obj)

    def _programs(self, path) -> Response:
        pth = request.environ['PATH_INFO']
        obj = get_href(pth)
        return RequestOp(server_endpoints=self).build_response_from_dataclass(obj)
        # if index is None:
        #     items = get_href_filtered(href_prefix=hrefs.program)
        #     program_list = DERProgramList(DERProgram=items, all=len(items), href=request.path, results=len(items))
        #     response = Response(dataclass_to_xml(program_list))
        # else:
        #     response = Response(dataclass_to_xml(get_href(request.path)))
        # return response
