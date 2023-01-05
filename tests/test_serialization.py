

from ieee_2030_5.models.sep import EndDevice
from ieee_2030_5.utils import dataclass_to_xml, xml_to_dataclass


def test_serialize_bytes():
    enddevice = EndDevice(lFDI="wheataniad", sFDI=50000)
    
    xml = dataclass_to_xml(enddevice)

    new_dataclass = xml_to_dataclass(xml)
    
    assert enddevice.sFDI == new_dataclass.sFDI
    assert enddevice.lFDI == new_dataclass.lFDI