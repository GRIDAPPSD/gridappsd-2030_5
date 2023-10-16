from dataclasses import dataclass
import pytest

import ieee_2030_5.hrefs as hrefs
import ieee_2030_5.models as m
from ieee_2030_5.adapters import Adapter, GenericListAdapter, NotFoundError
import os


def test_missing_type():

    with pytest.raises(ValueError):
        me = Adapter[m.EndDevice](hrefs.get_enddevice_href())


def test_add_invalid_type():
    me = Adapter[m.EndDevice](hrefs.get_enddevice_href(), generic_type=m.EndDevice)

    # Should only allow EndDevice to list
    der = m.DERControl()

    with pytest.raises(ValueError):
        me.add(der)


def test_verify_href_populated_correctly(ignore_adapter_load):
    for k in sorted(os.environ):
        print(f"{k} => {os.environ[k]}")
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
    ed, ed2 = m.EndDevice(), m.EndDevice()
    me.add(ed)
    me.add(ed2)

    with pytest.raises(ValueError):
        ed_list = me.fetch_all(m.EndDevice(), "EndDevice")


def test_fetch_all():
    me = Adapter[m.EndDevice](hrefs.get_enddevice_href(), generic_type=m.EndDevice)
    ed, ed2 = m.EndDevice(), m.EndDevice()
    me.add(ed)
    me.add(ed2)

    ed_list = me.fetch_all(m.EndDeviceList(), limit=2)

    assert ed_list.all == 2
    assert ed_list.results == 2
    assert ed_list.EndDevice[0] == ed
    assert ed_list.EndDevice[1] == ed2


def test_fetch_all_part():
    me = Adapter[m.EndDevice](hrefs.get_enddevice_href(), generic_type=m.EndDevice)
    ed, ed2 = m.EndDevice(), m.EndDevice()
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


@dataclass
class Foo:
    alpha: str
    beta: int


@dataclass
class Bar:
    alpha: str
    beta: int


def test_generic_list(ignore_adapter_load):

    foo_list = [
        Foo("c", 1),
        Foo("b", 2),
        Foo("a", 3),
    ]

    foo_href = "/foo"
    me = GenericListAdapter()
    for foo in foo_list:
        me.append(foo_href, foo)

    assert len(foo_list) == me.count()
    assert foo_list[0] == me.get(foo_href, 0)
    assert foo_list[1] == me.get(foo_href, 1)
    assert foo_list[2] == me.get(foo_href, 2)

    with pytest.raises(ValueError):
        me.append(foo_href, Bar("a", 1))

    me.remove(foo_href, 1)
    assert len(foo_list) - 1 == me.count()
    assert foo_list[0] == me.get(foo_href, 0)
    assert foo_list[2] == me.get(foo_href, 2)

    # Because we remove the second element, the third element is now at index 1
    # when we get values even though it has the same href key
    sorted_alpha = me.get_values(foo_href, sort_by="alpha")
    assert foo_list[2] == sorted_alpha[0]
    assert foo_list[0] == sorted_alpha[1]

    assert foo_list[2] == me.get_item_by_prop(foo_href, "alpha", "a")

    with pytest.raises(NotFoundError):
        me.get_item_by_prop(foo_href, "alpha", "d")

    with pytest.raises(KeyError):
        me.get("alpha", 5)

    with pytest.raises(NotFoundError):
        me.get(foo_href, 5)

    foo_list[0].alpha = "d"
    assert "d" == me.get(foo_href, 0).alpha
    assert sorted_alpha[1].alpha != "d"
