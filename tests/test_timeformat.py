import time
from datetime import datetime

from ieee_2030_5.adapters.timeadapter import TimeAdapter


def test_timestamp():
    ts = int(time.mktime(datetime.utcnow().timetuple()))
    
    assert ts == TimeAdapter.from_iso(TimeAdapter.user_readable(ts))
    