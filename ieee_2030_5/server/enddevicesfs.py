import logging
from typing import Optional

import werkzeug.exceptions
from flask import Response, request

import ieee_2030_5.adapters as adpt
import ieee_2030_5.hrefs as hrefs
import ieee_2030_5.models as m
from ieee_2030_5.data.indexer import add_href, get_href
from ieee_2030_5.models import Registration
from ieee_2030_5.server.base_request import RequestOp
from ieee_2030_5.types_ import Lfdi
from ieee_2030_5.utils import dataclass_to_xml, xml_to_dataclass

_log = logging.getLogger(__name__)


class EDevRequests(RequestOp):
    """
    Class supporting end devices and any of the subordinate calls to it.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def put(self) -> Response:
        parsed = hrefs.EdevHref.parse(request.path)

        mysubobj = xml_to_dataclass(request.data.decode('utf-8'))

        if get_href(request.path):
            response_status = 204
        else:
            response_status = 201

        add_href(request.path, mysubobj)

        return Response(status=response_status)

    def post(self, path: Optional[str] = None) -> Response:
        """
        Handle post request to /edev
        
        The expectation is that data will be an xml object like the following:
        
            <EndDevice xmlns="urn:ieee:std:2030.5:ns">
                <sFDI>231589308001</sFDI>
                <changedTime>0</changedTime>
            </EndDevice>
        
        Args:
            path: 

        Returns:

        """
        # request.data should have xml data.
        if not request.data:
            raise werkzeug.exceptions.Forbidden()

        ed: m.EndDevice = xml_to_dataclass(request.data.decode('utf-8'))

        if not isinstance(ed, m.EndDevice):
            raise werkzeug.exceptions.Forbidden()

        # This is what we should be using to get the device id of the registered end device.
        device_id = self.tls_repo.find_device_id_from_sfdi(ed.sFDI)
        ed.lFDI = self.tls_repo.lfdi(device_id)
        if end_device := adpt.EndDeviceAdapter.fetch_by_lfdi(ed.lfdi):
            status = 200
            ed_href = end_device.href
        else:
            if not ed.href:
                ed = adpt.EndDeviceAdapter.store(device_id, ed)

            ed_href = ed.href
            status = 201

        return Response(status=status, headers={'Location': ed_href})

    def get(self) -> Response:
        """
        Supports the get request for end_devices(EDev) and end_device_list_link.

        Paths:
            /edev
            /edev/0
            /edev/0/di
            /edev/0/rg
            /edev/0/der

        """
        # TODO start implementing these.
        start = int(request.args.get("s", 0))
        limit = int(request.args.get("l", 1))
        after = int(request.args.get("a", 0))

        edev_href = hrefs.HrefParser(request.path)

        ed = adpt.EndDeviceAdapter.fetch_by_property('lFDI', self.lfdi)

        # /edev_0_dstat
        if request.path == ed.DERListLink.href:
            retval = adpt.ListAdapter.get_resource_list(request.path, start, after, limit)
        elif request.path == ed.LogEventListLink.href:
            retval = adpt.ListAdapter.get_resource_list(request.path, start, after, limit)
        elif request.path == ed.FunctionSetAssignmentsListLink.href:
            retval = adpt.ListAdapter.get_resource_list(request.path, start, after, limit)
        elif edev_href.count() > 2:
            retval = get_href(request.path)
        elif not edev_href.has_index():
            retval = m.EndDeviceList(href=request.path, all=1, results=1, EndDevice=[ed])
        else:
            retval = get_href(request.path)

        # if adpt.ListAdapter.has_list(request.path):
        #     retval = adpt.ListAdapter.get_resource_list(request.path)

        return self.build_response_from_dataclass(retval)


class SDevRequests(RequestOp):
    """
    SelfDevice is an alias for the end device of a client.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get(self) -> Response:
        """
        Supports the get request for end_devices(EDev) and end_device_list_link.

        Paths:
            /sdev

        """
        end_device = self._end_devices.get_end_device_list(self.lfdi).EndDevice[0]
        return self.build_response_from_dataclass(end_device)


class FSARequests(RequestOp):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get(self):
        """ Retrieve a FSA or Program List
        """
        start = int(request.args.get("s", 0))
        limit = int(request.args.get("l", 0))
        after = int(request.args.get("a", 0))

        fsa_href = hrefs.fsa_parse(request.path)

        if fsa_href.fsa_index == hrefs.NO_INDEX:
            retval = adpt.ListAdapter.get_resource_list(request.path, start, after, limit)
            # retval = adpt.FunctionSetAssignmentsAdapter.fetch_all(m.FunctionSetAssignmentsList(),
            #                                                       "FunctionSetAssignments")
        elif fsa_href.fsa_sub == hrefs.FSASubType.DERProgram.value:
            retval = adpt.ListAdapter.get_resource_list(request.path, start, after, limit)
            # fsa = adpt.FunctionSetAssignmentsAdapter.fetch(fsa_href.fsa_index)
            # retval = adpt.FunctionSetAssignmentsAdapter.fetch_children(
            #     fsa, "fsa", m.DERProgramList())
            # # retval = FSAAdapter.fetch_children_list_container(fsa_href.fsa_index, m.DERProgram, m.DERProgramList(href="/derp"), "DERProgram")
        # else:
        #     retval = adpt.FunctionSetAssignmentsAdapter.fetch(fsa_href.fsa_index)

        return self.build_response_from_dataclass(retval)