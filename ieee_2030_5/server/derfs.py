from typing import Optional

from flask import Response, request
from werkzeug.exceptions import NotFound

import ieee_2030_5.adapters as adpt
from ieee_2030_5.data.indexer import add_href, get_href
import ieee_2030_5.hrefs as hrefs
import ieee_2030_5.models as m
from ieee_2030_5.server.base_request import RequestOp
from ieee_2030_5.utils import xml_to_dataclass

import logging

_log = logging.getLogger(__name__)


class DERRequests(RequestOp):
    """
    Class supporting end devices and any of the subordinate calls to it.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def put(self) -> Response:
        """Allows putting of 2030.5 DER data to the server.
        """
        if not request.path.startswith(hrefs.DEFAULT_DER_ROOT):
            raise ValueError(f"Invalid path for {self.__class__} {request.path}")

        parser = hrefs.HrefParser(request.path)

        clstype = {
            hrefs.DER_SETTINGS: m.DERSettings,
            hrefs.DER_STATUS: m.DERStatus,
            hrefs.DER_CAPABILITY: m.DERCapability,
            hrefs.DER_AVAILABILITY: m.DERAvailability,
            hrefs.DER_PROGRAM: m.DERProgram,
        }

        data = request.get_data(as_text=True)
        data = xml_to_dataclass(data, clstype[parser.at(2)])

        _log.debug(f"DER PUT {request.path} {data}")

        #orig = get_href(request.path)
        # if orig is None:
        #     raise NotFound(f"{request.path}")
        # data.href = orig.href
        add_href(request.path, data)
        return self.build_response_from_dataclass(data)

    def get(self) -> Response:

        if not request.path.startswith(hrefs.DEFAULT_DER_ROOT):
            raise ValueError(f"Invalid path for {self.__class__} {request.path}")

        value = get_href(request.path)

        if value is None:

            parser = hrefs.HrefParser(request.path)

            subpaths = {
                hrefs.DER_SETTINGS: m.DERSettings(href=request.path),
                hrefs.DER_STATUS: m.DERStatus(href=request.path),
                hrefs.DER_CAPABILITY: m.DERCapability(href=request.path),
                hrefs.DER_AVAILABILITY: m.DERAvailability(href=request.path),
                hrefs.DER_PROGRAM: m.DERProgram(href=request.path),
            }

            if parser.has_index():
                index = parser.at(1)
                subpath = parser.at(2)
                value = subpaths[subpath]

        # pth_split = request.path.split(hrefs.SEP)

        # if len(pth_split) == 1:
        #     # TODO Add arguments
        #     value = adpt.DERAdapter.fetch_list()
        # else:
        #     value = adpt.DERAdapter.fetch_at(int(pth_split[1]))

        return self.build_response_from_dataclass(value)


class DERProgramRequests(RequestOp):
    """
    Class supporting end devices and any of the subordinate calls to it.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get(self) -> Response:

        start = int(request.args.get('s', 0))
        after = int(request.args.get('a', 0))
        limit = int(request.args.get('l', 1))

        parsed = hrefs.HrefParser(request.path)

        if not parsed.has_index():
            retval = adpt.ListAdapter.get_resource_list(hrefs.DEFAULT_DERP_ROOT, start, after,
                                                        limit)
        elif parsed.count() == 2:
            retval = adpt.ListAdapter.get(hrefs.DEFAULT_DERP_ROOT, parsed.at(1))
        elif parsed.count() == 4:
            # Retrive the list of controls from storage
            dercl = get_href(parsed.join(3))
            assert isinstance(dercl, m.DERControlList)
            # The index that we want to get the control from.
            retval = dercl.DERControl[parsed.at(3)]
        elif parsed.at(2) == hrefs.DERC:
            retval = adpt.ListAdapter.get_resource_list(request.path, start, after, limit)
        # elif parsed.at(2) == hrefs.DDERC:
        #     retval = adpt.DERControlAdapter.fetch_at(parsed.at(3))
        else:
            retval = get_href(request.path)

        if not retval:
            raise NotFound(f"{request.path}")

        return self.build_response_from_dataclass(retval)
