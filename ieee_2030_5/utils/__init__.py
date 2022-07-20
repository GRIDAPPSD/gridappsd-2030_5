from dataclasses import dataclass
from typing import Type, Optional

from xsdata.formats.dataclass.context import XmlContext
from xsdata.formats.dataclass.parsers.config import ParserConfig
from xsdata.formats.dataclass.parsers.xml import XmlParser
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig

__xml_context__ = XmlContext()
__parser_config__ = ParserConfig(fail_on_unknown_attributes=False,
                                 fail_on_unknown_properties=False)
__xml_parser__ = XmlParser(config=__parser_config__, context=__xml_context__)
__config__ = SerializerConfig(xml_declaration=True, pretty_print=True)
__serializer__ = XmlSerializer(config=__config__)
__ns_map__ = {None: "urn:ieee:std:2030.5:ns"}


def serialize_dataclass(obj: dataclass) -> str:
    """
    Serializes a dataclass that was created via xsdata to an xml string for
    returning to a client.
    """
    return __serializer__.render(obj, ns_map=__ns_map__)


def parse_xml(xml: str, type: Optional[Type] = None) -> dataclass:
    """
    Parse the xml passed and return result from loaded classes.
    """
    return __xml_parser__.from_string(xml, type)


def dataclass_to_xml(dc: dataclass) -> str:
    return serialize_dataclass(dc)
