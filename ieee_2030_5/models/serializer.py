from dataclasses import dataclass

from xsdata.formats.dataclass.serializers import XmlSerializer

__serializer__ = XmlSerializer()


def serialize_xml(obj: dataclass) -> str:
    """
    Serializes a dataclass that was created via xdata to an xml string for
    returning to a client.
    """
    return __serializer__.render(obj)
