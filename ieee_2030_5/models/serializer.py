from dataclasses import dataclass
from typing import List

from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig

__config__ = SerializerConfig(xml_declaration=True, )
__serializer__ = XmlSerializer(config=__config__)
__ns_map__ = {
    "xmlns": "http://zigbee.org/sep",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance"
}


def serialize_xml(obj: dataclass) -> str:
    """
    Serializes a dataclass that was created via xdata to an xml string for
    returning to a client.
    """
    return __serializer__.render(obj)
