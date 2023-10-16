import time
from datetime import datetime

import ieee_2030_5.adapters as adpt


def test_timestamp():
    ts = int(time.mktime(datetime.utcnow().timetuple()))

    assert ts == adpt.TimeAdapter.from_iso(adpt.TimeAdapter.user_readable(ts))
