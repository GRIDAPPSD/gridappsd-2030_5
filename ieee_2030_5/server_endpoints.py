import calendar
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional
import time

import pytz
import werkzeug
from flask import Flask, Response, request

from ieee_2030_5.certs import TLSRepository
from ieee_2030_5.models import Time, DeviceCapability, TimeType
from ieee_2030_5.models.end_devices import EndDevices, Lfid
from ieee_2030_5.models.hrefs import EndpointHrefs
from ieee_2030_5.models.serializer import serialize_xml


class ServerEndpoints:

    def __init__(self, app: Flask, end_devices: EndDevices, tls_repo: TLSRepository):
        self.hrefs = EndpointHrefs()
        self.end_devices = end_devices
        self.tls_repo = tls_repo
        self.mimetype = "text/xml"

        app.add_url_rule(self.hrefs.dcap, view_func=self._dcap)
        app.add_url_rule(self.hrefs.tm, view_func=self._tm)

    def __required_cert__(self):
        pass
        # if 'ieee_2030_5_peercert' not in request.environ:
        #     raise werkzeug.exceptions.Forbidden()

    def __response__(self, obj: dataclass) -> Response:
        return Response(serialize_xml(obj), mimetype=self.mimetype)

    def __request_lfid__(self) -> Lfid:
        return self.tls_repo.lfdi(request.environ['ieee_2030_5_subject'])

    def __request_sfid__(self):
        pass

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

    def _dcap(self) -> Response:
        self.__required_cert__()

        # Based upon the connecting client we need to filter usages
        lfid = self.__request_lfid__()
        end_device_list = self.end_devices.get_device_by_lfid(lfid)

        cap = DeviceCapability()
        return self.__response__(self.end_devices.get_list(0, self.end_devices.num_devices))

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
