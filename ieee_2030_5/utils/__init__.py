from dataclasses import dataclass
from pathlib import Path
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
__config__ = SerializerConfig(xml_declaration=False, pretty_print=True)
__serializer__ = XmlSerializer(config=__config__)
__ns_map__ = {None: "urn:ieee:std:2030.5:ns"}

import ieee_2030_5.types_ as t
import ieee_2030_5.utils.tls_wrapper as tls


def serialize_dataclass(obj: dataclass) -> str:
    """
    Serializes a dataclass that was created via xsdata to an xml string for
    returning to a client.
    """
    return __serializer__.render(obj, ns_map=__ns_map__)


def xml_to_dataclass(xml: str, type: Optional[Type] = None) -> dataclass:
    """
    Parse the xml passed and return result from loaded classes.
    """
    return __xml_parser__.from_string(xml, type)


def dataclass_to_xml(dc: dataclass) -> str:
    return serialize_dataclass(dc)


def get_lfdi_from_cert(path: Path) -> t.Lfdi:
    """
    Using the fingerprint of the certifcate return the left truncation of 160 bits with no check digit.
    Example:
      From:
        3E4F-45AB-31ED-FE5B-67E3-43E5-E456-2E31-984E-23E5-349E-2AD7-4567-2ED1-45EE-213A
      Return:
        3E4F-45AB-31ED-FE5B-67E3-43E5-E456-2E31-984E-23E5
        as an integer.
    """

    # 160 / 4 == 40
    fp = tls.OpensslWrapper.tls_get_fingerprint_from_cert(path)
    fp = fp.replace(":", "")
    lfdi = t.Lfdi(fp[:40].encode('ascii'))
    return t.Lfdi(fp[:40].encode('ascii'))


def get_sfdi_from_lfdi(lfdi: t.Lfdi) -> int:
    """

    Args:
        lfdi:

    Returns:

    """
    assert len(lfdi) == 40, "lfdi must be 160-bits (40 hex characters) long."
    hex_str = str(int(lfdi[:9], 16))
    check_bit = 1
    while not (int(hex_str[-2:]) + check_bit) % 10 == 0:
        check_bit += 1
    return int(hex_str + str(check_bit))
