from __future__ import annotations

import json
import logging

from flask import Flask, Response, request
from werkzeug.exceptions import Forbidden
from werkzeug.routing import BaseConverter

import ieee_2030_5.adapters as adpt
import ieee_2030_5.hrefs as hrefs
import ieee_2030_5.models as m
from ieee_2030_5.certs import TLSRepository
from ieee_2030_5.config import ServerConfiguration
from ieee_2030_5.server.base_request import RequestOp
from ieee_2030_5.server.dcapfs import DcapRequest
from ieee_2030_5.server.derfs import DERProgramRequests, DERRequests
from ieee_2030_5.server.enddevicesfs import EDevRequests, FSARequests, SDevRequests

# module level instance of hrefs class.
from ieee_2030_5.server.meteringfs import MirrorUsagePointRequest, UsagePointRequest
from ieee_2030_5.server.timefs import TimeRequest
from ieee_2030_5.server.uuid_handler import UUIDHandler
from ieee_2030_5.utils import dataclass_to_xml

_log = logging.getLogger(__name__)

# Define constants for backward compatibility
MATCH_REG = "[a-zA-Z0-9_]*"
EDEV = "edev"
DER_PROGRAM = "derp"
DER = "der"
MUP = "mup"
UTP = "upt"  # Note: UTP and UPT are used interchangeably in the codebase
UPT = "upt"
CURVE = "dc"
FSA = "fsa"
LOG = "log"


class Admin(RequestOp):
    def get(self):
        if not self.is_admin_client:
            raise Forbidden()
        return Response("We are able to do stuff here")

    def post(self):
        if not self.is_admin_client:
            raise Forbidden()
        return Response(json.dumps({"abc": "def"}), headers={"Content-Type": "application/json"})


class ServerList(RequestOp):
    def __init__(self, list_type: str, **kwargs):
        super().__init__(**kwargs)
        self._list_type = list_type

    def get(self) -> Response:
        response = None
        if self._list_type == "EndDevice":
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
    def __init__(self, app: Flask, tls_repo: TLSRepository, config: ServerConfiguration):
        self.config = config
        self.tls_repo = tls_repo
        self.mimetype = "text/xml"
        self.app: Flask = app
        self.app.url_map.converters["regex"] = RegexConverter

        _log.debug(f"Adding rule: {hrefs.uuid_gen} methods: {['GET']}")
        app.add_url_rule(hrefs.uuid_gen, view_func=self._generate_uuid)

        _log.debug(f"Adding rule: {hrefs.get_dcap_href()} methods: {['GET']}")
        app.add_url_rule(hrefs.get_dcap_href(), view_func=self._dcap)

        _log.debug(f"Adding rule: {hrefs.get_time_href()} methods: {['GET']}")
        app.add_url_rule(hrefs.get_time_href(), view_func=self._tm)

        _log.debug(f"Adding rule: {hrefs.sdev} methods: {['GET']}")
        app.add_url_rule(hrefs.sdev, view_func=self._sdev)

        # All the energy devices
        app.add_url_rule(f"/<regex('{EDEV}{MATCH_REG}'):path>", view_func=self._edev, methods=["GET", "PUT", "POST"])

        # This rule must be before der
        app.add_url_rule(f"/<regex('{DER_PROGRAM}{MATCH_REG}'):path>", view_func=self._derp, methods=["GET"])

        app.add_url_rule(f"/<regex('{DER}{MATCH_REG}'):path>", view_func=self._der, methods=["GET", "PUT"])

        app.add_url_rule(f"/<regex('{MUP}{MATCH_REG}'):path>", view_func=self._mup, methods=["GET", "POST"])

        app.add_url_rule(f"/<regex('{UTP}{MATCH_REG}'):path>", view_func=self._upt, methods=["GET", "POST"])

        app.add_url_rule(f"/<regex('{CURVE}{MATCH_REG}'):path>", view_func=self._curves, methods=["GET"])

        app.add_url_rule(f"/<regex('{FSA}{MATCH_REG}'):path>", view_func=self._fsa, methods=["GET"])

        app.add_url_rule(f"/<regex('{LOG}{MATCH_REG}'):path>", view_func=self._log, methods=["GET", "POST"])

    def _log(self, path):
        return

    def _foo(self, bar):
        return Response("Foo Response")

    def _generate_uuid(self) -> Response:
        return Response(UUIDHandler().generate())

    def _fsa(self, path) -> Response:
        return FSARequests(server_endpoints=self).execute()

    def _upt(self, path) -> Response:
        return UsagePointRequest(server_endpoints=self).execute()

    def _mup(self, path) -> Response:
        return MirrorUsagePointRequest(server_endpoints=self).execute()

    # Needs to be before der
    def _derp(self, path) -> Response:
        return DERProgramRequests(server_endpoints=self).execute()

    def _der(self, path) -> Response:
        _log.debug(request.method)
        return DERRequests(server_endpoints=self).execute()

    def _dcap(self) -> Response:
        return DcapRequest(server_endpoints=self).execute()

    def _edev(self, path: str | None = None) -> Response:
        return EDevRequests(server_endpoints=self).execute()

    def _sdev(self) -> Response:
        return SDevRequests(server_endpoints=self).execute()

    def _tm(self) -> Response:
        return TimeRequest(server_endpoints=self).execute()

    def _curves(self, path) -> Response:
        _list = adpt.ListAdapter.get_list(request.path)
        obj = m.DERCurveList(href=path, DERCurve=_list, all=len(_list))
        return RequestOp(server_endpoints=self).build_response_from_dataclass(obj)
