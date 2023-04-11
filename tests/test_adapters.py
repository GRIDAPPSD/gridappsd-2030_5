import pytest

import ieee_2030_5.hrefs as hrefs
import ieee_2030_5.models as m
from ieee_2030_5.adapters import Adapter


def test_missing_type():
    
    with pytest.raises(ValueError):
        me = Adapter[m.EndDevice](hrefs.get_enddevice_href())

def test_add_invalid_type():
    me = Adapter[m.EndDevice](hrefs.get_enddevice_href(), generic_type=m.EndDevice)
    
    # Should only allow EndDevice to list
    der = m.DERControl()
    
    with pytest.raises(ValueError):
        me.add(der)

def test_verify_href_populated_correctly():
    me = Adapter[m.EndDevice](hrefs.get_enddevice_href(), generic_type=m.EndDevice)
    ed = m.EndDevice()
    me.add(ed)
    
    assert ed.href.startswith(hrefs.get_enddevice_href())
    assert ed.href == hrefs.get_enddevice_href(0)
    ed2 = m.EndDevice()
    me.add(ed2)
    assert ed2.href == hrefs.get_enddevice_href(1)
    
    
    me = Adapter[m.EndDevice](hrefs.get_enddevice_href(), generic_type=m.EndDevice)
    ed = m.EndDevice(href='FooFar')
    me.add(ed)
    assert ed.href == 'FooFar'
    
def test_fetch_all_without_list():
    me = Adapter[m.EndDevice](hrefs.get_enddevice_href(), generic_type=m.EndDevice)
    ed, ed2 = m.EndDevice(),  m.EndDevice()
    me.add(ed)
    me.add(ed2)
    
    
    with pytest.raises(ValueError):
        ed_list = me.fetch_all(m.EndDevice(), "EndDevice")
        
    
def test_fetch_all():
    me = Adapter[m.EndDevice](hrefs.get_enddevice_href(), generic_type=m.EndDevice)
    ed, ed2 = m.EndDevice(),  m.EndDevice()
    me.add(ed)
    me.add(ed2)
    
    ed_list = me.fetch_all(m.EndDeviceList(), limit=2)
    
    assert ed_list.all == 2
    assert ed_list.results == 2
    assert ed_list.EndDevice[0] == ed
    assert ed_list.EndDevice[1] == ed2
    
def test_fetch_all_part():
    me = Adapter[m.EndDevice](hrefs.get_enddevice_href(), generic_type=m.EndDevice)
    ed, ed2 = m.EndDevice(),  m.EndDevice()
    me.add(ed)
    me.add(ed2)
    
    ed_list = me.fetch_all(m.EndDeviceList(), start=1, limit=2)
    
    assert ed_list.all == 2
    assert ed_list.results == 1
    assert len(ed_list.EndDevice) == 1
    
    me = Adapter[m.EndDevice](hrefs.get_enddevice_href(), generic_type=m.EndDevice)
    eds = [m.EndDevice() for x in range(5)]
    for ed in eds:
        me.add(ed)
    
    ed_list = me.fetch_all(m.EndDeviceList(), limit=len(eds))
    
    assert len(eds) == len(ed_list.EndDevice)
    
    ed_list2 = me.fetch_all(m.EndDeviceList(), start=1, limit=2)
    
    assert 2, len(ed_list2)
    assert ed_list.EndDevice[1] == ed_list2.EndDevice[0]
    assert ed_list.EndDevice[2] == ed_list2.EndDevice[1]
    

def test_add_child():
    me = Adapter[m.EndDevice](hrefs.get_enddevice_href(), generic_type=m.EndDevice)
    
    eds = [m.EndDevice() for x in range(5)]
    for ed in eds:
        me.add(ed)
        
    fsa = m.FunctionSetAssignmentsList()
    
    me.add_child(ed, m.FunctionSetAssignmentsList, fsa)
    
    fsa_return = me.fetch_child(ed, m.FunctionSetAssignmentsList, 0)
    
    assert fsa_return == fsa
    

    