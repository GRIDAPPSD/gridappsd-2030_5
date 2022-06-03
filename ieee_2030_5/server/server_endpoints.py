from __future__ import annotations

import calendar
import json
import time
from datetime import datetime, timedelta
import logging
from typing import Callable

import pytz
from flask import Flask, Response, request
from werkzeug.exceptions import Forbidden

from ieee_2030_5.certs import TLSRepository
from ieee_2030_5.models import Time
from ieee_2030_5.models.end_devices import EndDevices
import ieee_2030_5.hrefs as hrefs
from ieee_2030_5.server.base_request import RequestOp
from ieee_2030_5.server.uuid_handler import UUIDHandler

# module level instance of hrefs class.
from ieee_2030_5.server.usage_points import MUP, UTP
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
        return dataclass_to_xml(self._end_devices.get_device_capability(self.lfid))


class EDev(RequestOp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get(self) -> Response:
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

        pth = request.path[len(hrefs.edev.strip()):].split("/")
        # split returns a single value whether or not there was any characters found. if
        # this is the case then we want to return the list of the end devices.
        if len(pth) == 1:
            retval = ServerList("EndDevice", end_devices=self._end_devices,
                                tls_repo=self._tls_repository, server_endpoints=self._server_endpoints).execute()
        else:
            # This should mean we have an index of an end device that we are going to return
            index = int(pth[1])
            if len(pth) == 2:
                retval = dataclass_to_xml(self._end_devices.get(index))
            else:
                sub_info = pth[3]

        return retval
        # return dataclass_to_xml(self._end_devices.get())


class ServerList(RequestOp):
    def __init__(self, list_type: str, **kwargs):
        super().__init__(**kwargs)
        self._list_type = list_type

    def get(self) -> Response:
        response = None
        if self._list_type == 'EndDevice':
            response = self._end_devices.get_end_device_list(self.lfid)

        if response:
            response = dataclass_to_xml(response)

        return response


class ServerEndpoints:

    def __init__(self, app: Flask, end_devices: EndDevices, tls_repo: TLSRepository):
        self.end_devices = end_devices
        self.tls_repo = tls_repo
        self.mimetype = "text/xml"
        self.app: Flask = app

        # internally flask uses the name of the view_func for the removal.
        # self.remove_endpoint(self._admin.__name__)

        self.add_endpoint(hrefs.admin,
                          view_func=self._admin, methods=['GET', 'POST'])
        # app.add_url_rule(hrefs.admin, view_func=self._admin, methods=['GET', 'POST'])

        self.add_endpoint(hrefs.dcap, view_func=self._dcap)
        self.add_endpoint(hrefs.edev, view_func=self._edev)
        self.add_endpoint(hrefs.mup, view_func=self._mup, methods=['GET', 'POST'])
        self.add_endpoint(hrefs.uuid_gen, view_func=self._generate_uuid)
        # app.add_url_rule(hrefs.rsps, view_func=None)
        # self.add_endpoint(hrefs.tm, view_func=self._tm)
        #
        # for index, ed in end_devices.all_end_devices.items():
        #     self.add_endpoint(hrefs.edev + f"/{index}", view_func=self._edev)
        #     self.add_endpoint(hrefs.mup + f"/{index}", view_func=self._mup)

    def add_endpoint(self, endpoint: str, view_func: Callable, **kwargs):
        """
        Dynamically add an endpoint to the flask application.  If the endpoint already exists
        then it will be overwritten.
        """
        self.app.add_url_rule(endpoint, view_func=view_func, **kwargs)

    def remove_endpoint(self, endpoint: str):
        """
        Remove an endpoint from the flask application.  The endpoint is the name of the view function
        not the actual endpoint.  So when registering:

        obj.add_endpoint('/foo', view_func=self._foo_method)

        The actual endpoint stored is the name of the function '_foo_method'.  To dynamically remove it
        call

        obj.remove_endpoint('_foo_method')
        """
        self.app.view_functions.pop(endpoint)

    @staticmethod
    def __format_time__(dt_obj: datetime, is_local: bool = False) -> TimeType:
        """ Return a proper IEEE2030_5 TimeType object for the dt_obj passed in.
                From IEEE 2030.5 spec:
                    TimeType Object (Int64)
                        Time is a signed 64 bit value representing the number of seconds
                        since 0 hours, 0 minutes, 0 seconds, on the 1st of January, 1970,
                        in UTC, not counting leap seconds.
            :param dt_obj: Datetime object to convert to IEEE2030_5 TimeType object.
            :param local: dt_obj is in UTC or Local time. Default to UTC time.
            :return: Time XSD object
            :raises: If utc_dt_obj is not UTC
        """

        if dt_obj.tzinfo is None:
            raise Exception("IEEE 2030.5 times should be timezone aware UTC or local")

        if dt_obj.utcoffset() != timedelta(0) and not is_local:
            raise Exception("IEEE 2030.5 TimeType should be based on UTC")

        if is_local:
            return TimeType(int(time.mktime(dt_obj.timetuple())))
        else:
            return TimeType(int(calendar.timegm(dt_obj.timetuple())))

    def _generate_uuid(self) -> Response:
        return Response(UUIDHandler().generate())

    def _admin(self) -> Response:
        return Admin(end_devices=self.end_devices, tls_repo=self.tls_repo, server_endpoints=self).execute()

    def _upt(self) -> Response:
        return UTP(end_devices=self.end_devices, tls_repo=self.tls_repo, server_endpoints=self).execute()

    def _mup(self) -> Response:
        return MUP(end_devices=self.end_devices, tls_repo=self.tls_repo, server_endpoints=self).execute()

    def _dcap(self) -> Response:
        return Dcap(end_devices=self.end_devices, tls_repo=self.tls_repo, server_endpoints=self).execute()

    def _edev(self) -> Response:
        return EDev(end_devices=self.end_devices, tls_repo=self.tls_repo, server_endpoints=self).execute()

        # self.__required_cert__()
        #
        # # Based upon the connecting client we need to filter usages
        # lfid = self.__request_lfid__()
        # return self.__response__(self.end_devices.get_device_capability(lfid))

    def _tm(self) -> Response:
        now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
        local_tz = datetime.now().astimezone().tzinfo
        now_local = datetime.now().replace(tzinfo=local_tz)

        start_dst_utc, end_dst_utc = [
            dt for dt in local_tz._utc_transition_times if dt.year == now_local.year
        ]

        utc_offset = local_tz.utcoffset(start_dst_utc - timedelta(days=1))
        dst_offset = local_tz.utcoffset(start_dst_utc + timedelta(days=1)) - utc_offset
        local_but_utc = datetime.now().replace(tzinfo=pytz.utc)

        tm = Time(current_time=self.__format_time__(now_utc),
                  dst_end_time=self.__format_time__(end_dst_utc.replace(tzinfo=pytz.utc)),
                  dst_offset=TimeOffsetType(int(dst_offset.total_seconds())),
                  local_time=self.__format_time__(local_but_utc),
                  quality=None,
                  tz_offset=TimeOffsetType(utc_offset.total_seconds()))

        return self.__response__(tm)
