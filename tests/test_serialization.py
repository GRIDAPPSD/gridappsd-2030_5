import base64

from ieee_2030_5.models.sep import EndDevice, EndDeviceList
from ieee_2030_5.utils import dataclass_to_xml, xml_to_dataclass


def test_serialize_bytes():
    # lfdi must be upper case
    enddevice = EndDevice(lFDI="2EFA234A10", sFDI=50000)

    xml = dataclass_to_xml(enddevice)

    new_dataclass = xml_to_dataclass(xml)

    assert enddevice.sFDI == new_dataclass.sFDI
    assert enddevice.lFDI.encode() == new_dataclass.lFDI


def test_from_string():

    xml = """<EndDeviceList xmlns="urn:ieee:std:2030.5:ns" subscribable="0" all="1" results="1" pollRate="900"> 
        <EndDevice href="/edev_0">
            <DERListLink href="/edev_0_der"/>
            <deviceCategory>20</deviceCategory>
            <DeviceInformationLink href="/edev_0_di"/>
            <DeviceStatusLink href="/edev_0_dstat"/>
            <lFDI>2EE1453C8A019B6BE4EC91317DCF6082C2F8090A</lFDI>
            <sFDI>125842441685</sFDI>
            <changedTime>1692685230</changedTime>
            <FunctionSetAssignmentsListLink href="/edev_0_fsa"/>
            <RegistrationLink href="/edev_0_rg"/>
        </EndDevice>
    </EndDeviceList>"""

    new_class: EndDeviceList = xml_to_dataclass(xml)

    assert len(new_class.EndDevice) == 1
    ed = new_class.EndDevice[0]
    assert 125842441685 == ed.sFDI
    assert b'2EE1453C8A019B6BE4EC91317DCF6082C2F8090A' == ed.lFDI
