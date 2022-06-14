import calendar
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Union

PathStr = Union[Path, str]
StrPath = PathStr
TimeType = int
TimeOffsetType = int
Lfid = int

SEP_XML = "application/sep+xml"


def format_time(dt_obj: datetime, is_local: bool = False) -> TimeType:
    """ Return a proper IEEE2030_5 TimeType object for the dt_obj passed in.
            From IEEE 2030.5 spec:
                TimeType Object (Int64)
                    Time is a signed 64 bit value representing the number of seconds
                    since 0 hours, 0 minutes, 0 seconds, on the 1st of January, 1970,
                    in UTC, not counting leap seconds.
        :param dt_obj: Datetime object to convert to IEEE2030_5 TimeType object.
        :param is_local: dt_obj is in UTC or Local time. Default to UTC time.
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
