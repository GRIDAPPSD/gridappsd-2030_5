import pytest

import ieee_2030_5.hrefs as hrefs
import ieee_2030_5.models as m
from ieee_2030_5.adapters import Adapter


def test_add_child_with_href():
    me = Adapter[m.EndDevice](hrefs.get_enddevice_href(), generic_type=m.EndDevice)
    ed = m.EndDevice(href="first")
    me.add(ed)
    derc = m.DERControl()
    me.add_child(ed, "test", derc, href="junk")
    assert "junk" == derc.href

def test_add_child_no_parent_throws_error():
    me = Adapter[m.EndDevice](hrefs.get_enddevice_href(), generic_type=m.EndDevice)
    ed = m.EndDevice(href="first")
    derc = m.DERControl()
    
    # Note parent ed hasn't been added to the me adapter yet.
    with pytest.raises(KeyError):
        me.add_child(ed, "test", derc)

def test_add_child_correct_href():
    me = Adapter[m.EndDevice](hrefs.get_enddevice_href(), generic_type=m.EndDevice)
    ed = m.EndDevice(href="first")
    me.add(ed)
    derc = m.DERControl()
    me.add_child(ed, "test", derc)
    assert hrefs.SEP.join(["first", "test", "0"]) == derc.href

def test_missing_type():
    
    with pytest.raises(ValueError):
        me = Adapter[m.EndDevice](hrefs.get_enddevice_href())

def test_add_invalid_type():
    me = Adapter[m.EndDevice](hrefs.get_enddevice_href(), generic_type=m.EndDevice)
    
    # Should only allow EndDevice to list
    der = m.DERControl()
    
    with pytest.raises(ValueError):
        me.add(der)
        
def test_fetch_missing_key_returns_empty():
    ed = m.EndDevice()
    me = Adapter[m.EndDevice](hrefs.get_enddevice_href(), generic_type=m.EndDevice)
    me.add(ed)
    me.add_child(ed, "foo", m.File())
    assert [] == me.fetch_children(ed, "bar")
    

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
    me = Adapter[m.DERProgram](hrefs.der_program_href(), generic_type=m.DERProgram)
    
    der_programs = [m.DERProgram() for x in range(5)]
    for index, program in enumerate(der_programs):
        me.add(program)
        assert program.href == hrefs.der_program_href(index)
    
    me.add_child(der_programs[0], name="derc", child=m.DERControl())
    with pytest.raises(ValueError):
        me.add_child(der_programs[0], name="derc", child=m.DefaultDERControl())
        
    me.add_child(der_programs[0], name="derc", child=m.DERControl())
    
    
    derc = me.fetch_children(der_programs[0], "derc", m.DERControlList())
    
    derc_list = me.fetch_children(der_programs[0], "derc")
    
    assert len(derc.DERControl) == len(derc_list)
    
    for index, obj in enumerate(derc_list):
        assert obj == derc.DERControl[index]

