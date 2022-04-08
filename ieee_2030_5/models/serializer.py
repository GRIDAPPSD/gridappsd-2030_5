import io
from dataclasses import dataclass
from typing import List

from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig
from xsdata.formats.dataclass.parsers.xml import XmlParser
from xsdata.formats.dataclass.context import XmlContext

__xml_context__ = XmlContext()
__xml_parser__ = XmlParser(context=__xml_context__)

__config__ = SerializerConfig(xml_declaration=True, )
__serializer__ = XmlSerializer(config=__config__)
__ns_map__ = {"xmlns": "http://zigbee.org/sep", "xsi": "http://www.w3.org/2001/XMLSchema-instance"}


def serialize_xml(obj: dataclass) -> str:
    """
    Serializes a dataclass that was created via xdata to an xml string for
    returning to a client.
    """
    return __serializer__.render(obj)


def parse_xml(xml: str) -> dataclass:
    """
    Parse the xml passed and return result from loaded classes.
    """
    return __xml_parser__.from_string(xml)
