from dataclasses import dataclass

from flask import Response

from ieee_2030_5.models.serializer import serialize_xml


def dataclass_to_xml(dc: dataclass) -> Response:
    return Response(serialize_xml(dc), mimetype="text/xml")
