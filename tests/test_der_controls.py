import logging
import time
from datetime import datetime

import pytest

import ieee_2030_5.hrefs as hrefs
import ieee_2030_5.models as m
from ieee_2030_5.adapters.der import DERProgramAdapter, time_updated
from ieee_2030_5.adapters.timeadapter import TimeAdapter
from ieee_2030_5.utils import uuid_2030_5

logging.basicConfig(level=logging.DEBUG)


def test_der_activate_deactivate():
    
    original_timestamp = int(time.mktime(datetime.utcnow().timetuple()))
    was_active = False
    was_deactive = False
    
    def _updating(timestamp):
        nonlocal was_active, was_deactive
        
        print(TimeAdapter.user_readable(timestamp))
        
        # This is the function that updates the der program and controls
        time_updated(timestamp)
                
        try:
            active = DERProgramAdapter.fetch_children(der_program, hrefs.DER_CONTROL_ACTIVE)
        except KeyError:
            active = []
        if active:
            was_active = True
        
        if was_active:
            active = DERProgramAdapter.fetch_children(der_program, hrefs.DER_CONTROL_ACTIVE)
            if not active:
                was_deactive = True                
    
    der_program = m.DERProgram(mRID=uuid_2030_5())
    der_control = m.DERControl(
        mRID=uuid_2030_5(),
        interval=m.DateTimeInterval(duration=20,
                                    start=original_timestamp + 10)
    )
    
    DERProgramAdapter.add(der_program)
    DERProgramAdapter.add_child(der_program, hrefs.DERC, der_control)
    
    while True:
        next_timestamp = int(time.mktime(datetime.utcnow().timetuple()))
        
        if was_active and was_deactive:
            break
        _updating(next_timestamp)
        
        if next_timestamp > original_timestamp + 45:
            break
        time.sleep(1)
    

    if not was_deactive or not was_active:
        pytest.fail("Didn't meet requirements.")