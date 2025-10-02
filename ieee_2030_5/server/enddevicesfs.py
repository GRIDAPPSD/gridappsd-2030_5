import logging

import werkzeug.exceptions
from flask import Response, request

import ieee_2030_5.adapters as adpt
import ieee_2030_5.hrefs as hrefs
import ieee_2030_5.models as m
from ieee_2030_5.data.indexer import add_href, get_href
from ieee_2030_5.server.base_request import RequestOp
from ieee_2030_5.utils import xml_to_dataclass

_log = logging.getLogger(__name__)


class EDevRequests(RequestOp):
    """
    Class supporting end devices and any of the subordinate calls to it.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def put(self) -> Response:
        """Handle PUT request to update or create EndDevice resources."""
        _log.debug(f"EDevRequests PUT: {request.path} - LFDI: {self.lfdi}")

        try:
            if not request.data:
                _log.warning("PUT request missing data")
                raise werkzeug.exceptions.BadRequest("Request data is required")

            _log.debug(f"PUT data length: {len(request.data)}")

            parsed = hrefs.EdevHref.parse(request.path)
            mysubobj = xml_to_dataclass(request.data.decode("utf-8"))

            _log.debug(f"Parsed object type: {type(mysubobj)}")

            if get_href(request.path):
                response_status = 204
                _log.debug(f"Updated existing resource at {request.path}")
            else:
                response_status = 201
                _log.debug(f"Created new resource at {request.path}")

            add_href(request.path, mysubobj)

            response = Response(status=response_status)
            _log.info(f"EDevRequests PUT {request.path} - Status: {response_status}")
            return response

        except werkzeug.exceptions.HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            _log.error(f"Error in EDevRequests PUT {request.path}: {e}", exc_info=True)
            raise werkzeug.exceptions.InternalServerError(f"Internal server error: {str(e)}")

    def post(self, path: str | None = None) -> Response:
        """
        Handle post request to /edev

        The expectation is that data will be an xml object like the following:

            <EndDevice xmlns="urn:ieee:std:2030.5:ns">
                <sFDI>231589308001</sFDI>
                <changedTime>0</changedTime>
            </EndDevice>

        Args:
            path: Optional path parameter

        Returns:
            Response with status 200/201 and Location header
        """
        _log.debug(f"EDevRequests POST: {request.path} - LFDI: {self.lfdi}")

        try:
            # request.data should have xml data.
            if not request.data:
                _log.warning("POST request missing data")
                raise werkzeug.exceptions.BadRequest("Request data is required")

            _log.debug(f"POST data length: {len(request.data)}")

            ed: m.EndDevice = xml_to_dataclass(request.data.decode("utf-8"))

            if not isinstance(ed, m.EndDevice):
                _log.warning(f"Invalid data type received: {type(ed)}")
                raise werkzeug.exceptions.BadRequest("Invalid EndDevice data")

            _log.debug(f"Parsed EndDevice with sFDI: {ed.sFDI}")

            # This is what we should be using to get the device id of the registered end device.
            device_id = self.tls_repo.find_device_id_from_sfdi(ed.sFDI)
            if device_id is None:
                _log.error(f"No device ID found for sFDI: {ed.sFDI}")
                raise werkzeug.exceptions.NotFound(f"Device not registered for sFDI: {ed.sFDI}")

            ed.lFDI = self.tls_repo.lfdi(device_id)
            _log.debug(f"Device ID: {device_id}, lFDI: {ed.lFDI}")

            if end_device := adpt.EndDeviceAdapter.fetch_by_lfdi(ed.lFDI):
                status = 200
                ed_href = end_device.href
                _log.debug(f"Updated existing EndDevice: {ed_href}")
            else:
                if not ed.href:
                    ed = adpt.EndDeviceAdapter.store(device_id, ed)

                ed_href = ed.href
                status = 201
                _log.debug(f"Created new EndDevice: {ed_href}")

            response = Response(status=status, headers={"Location": ed_href})
            _log.info(f"EDevRequests POST {request.path} - Status: {status}, Location: {ed_href}")
            return response

        except werkzeug.exceptions.HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            _log.error(f"Error in EDevRequests POST {request.path}: {e}", exc_info=True)
            raise werkzeug.exceptions.InternalServerError(f"Internal server error: {str(e)}")

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
        _log.debug(f"EDevRequests GET: {request.path} - LFDI: {self.lfdi}")

        try:
            # TODO start implementing these.
            start = int(request.args.get("s", 0))
            limit = int(request.args.get("l", 1))
            after = int(request.args.get("a", 0))

            edev_href = hrefs.HrefParser(request.path)

            ed = adpt.EndDeviceAdapter.fetch_by_property("lFDI", self.lfdi)

            if ed is None:
                _log.warning(f"No EndDevice found for LFDI: {self.lfdi}")
                raise werkzeug.exceptions.NotFound(f"No device found for LFDI {self.lfdi}")

            _log.debug(f"Found EndDevice: {ed.href}")

            # /edev_0_dstat
            if hasattr(ed, "DERListLink") and ed.DERListLink and request.path == ed.DERListLink.href:
                _log.debug(f"Getting DER list for path: {request.path}")
                retval = adpt.ListAdapter.get_resource_list(request.path, start, after, limit)
            elif hasattr(ed, "LogEventListLink") and ed.LogEventListLink and request.path == ed.LogEventListLink.href:
                _log.debug(f"Getting LogEvent list for path: {request.path}")
                retval = adpt.ListAdapter.get_resource_list(request.path, start, after, limit)
            elif (
                hasattr(ed, "FunctionSetAssignmentsListLink")
                and ed.FunctionSetAssignmentsListLink
                and request.path == ed.FunctionSetAssignmentsListLink.href
            ):
                _log.debug(f"Getting FunctionSetAssignments list for path: {request.path}")
                retval = adpt.ListAdapter.get_resource_list(request.path, start, after, limit)
            elif edev_href.count() > 2:
                _log.debug(f"Getting nested resource for path: {request.path}")
                if retval := get_href(request.path):
                    pass
                elif request.path.endswith("_rg"):
                    # Handle registration requests - these are single Registration objects, not lists
                    _log.debug(f"Getting Registration object for path: {request.path}")
                    retval = adpt.ListAdapter.get_single(request.path)
                else:
                    retval = adpt.ListAdapter.get_resource_list(request.path, start, after, limit)
            elif not edev_href.has_index():
                _log.debug(f"Getting EndDevice list for path: {request.path}")
                # Ensure EndDevice has all its links populated
                if ed and ed.href:
                    try:
                        edev_href_helper = hrefs.EndDeviceHref(edev_href=ed.href)
                        ed = edev_href_helper.fill_hrefs(ed)
                        _log.debug(f"Populated EndDevice links for {ed.href}")
                    except Exception as e:
                        _log.warning(f"Failed to populate EndDevice links: {e}")
                retval = m.EndDeviceList(
                    href=request.path, all=1, results=1, pollRate=adpt.get_poll_rate("end_device_list"), EndDevice=[ed]
                )
            else:
                _log.debug(f"Getting single resource for path: {request.path}")
                if retval := get_href(request.path):
                    pass
                else:
                    retval = adpt.ListAdapter.get_resource_list(request.path, start, after, limit)

            _log.debug(f"EDevRequests GET response type: {type(retval)}")

            response = self.build_response_from_dataclass(retval)
            _log.info(f"EDevRequests GET {request.path} - Status: {response.status_code}")
            return response

        except werkzeug.exceptions.HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            _log.error(f"Error in EDevRequests GET {request.path}: {e}", exc_info=True)
            raise werkzeug.exceptions.InternalServerError(f"Internal server error: {str(e)}")

        # if adpt.ListAdapter.has_list(request.path):
        #     retval = adpt.ListAdapter.get_resource_list(request.path)


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
        _log.debug(f"SDevRequests GET: {request.path} - LFDI: {self.lfdi}")

        try:
            end_device_list = self._end_devices.get_end_device_list(self.lfdi)
            if not end_device_list or not end_device_list.EndDevice:
                _log.warning(f"No EndDevice found in list for LFDI: {self.lfdi}")
                raise werkzeug.exceptions.NotFound(f"No self device found for LFDI {self.lfdi}")

            end_device = end_device_list.EndDevice[0]
            _log.debug(f"Found SelfDevice: {getattr(end_device, 'href', 'no href')}")

            response = self.build_response_from_dataclass(end_device)
            _log.info(f"SDevRequests GET {request.path} - Status: {response.status_code}")
            return response

        except werkzeug.exceptions.HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            _log.error(f"Error in SDevRequests GET {request.path}: {e}", exc_info=True)
            raise werkzeug.exceptions.InternalServerError(f"Internal server error: {str(e)}")


class FSARequests(RequestOp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get(self) -> Response:
        """Retrieve a FSA or Program List"""
        _log.debug(f"FSARequests GET: {request.path} - LFDI: {self.lfdi}")

        try:
            start = int(request.args.get("s", 0))
            limit = int(request.args.get("l", 0))
            after = int(request.args.get("a", 0))

            fsa_href = hrefs.fsa_parse(request.path)
            _log.debug(f"Parsed FSA href - index: {fsa_href.fsa_index}, sub: {getattr(fsa_href, 'fsa_sub', None)}")

            if fsa_href.fsa_index == hrefs.NO_INDEX:
                _log.debug(f"Getting FSA list for path: {request.path}")
                retval = adpt.ListAdapter.get_resource_list(request.path, start, after, limit)
                # retval = adpt.FunctionSetAssignmentsAdapter.fetch_all(m.FunctionSetAssignmentsList(),
                #                                                       "FunctionSetAssignments")
            elif fsa_href.fsa_sub == hrefs.FSASubType.DERProgram.value:
                _log.debug(f"Getting DER Program list for path: {request.path}")
                retval = adpt.ListAdapter.get_resource_list(request.path, start, after, limit)
                # fsa = adpt.FunctionSetAssignmentsAdapter.fetch(fsa_href.fsa_index)
                # retval = adpt.FunctionSetAssignmentsAdapter.fetch_children(
                #     fsa, "fsa", m.DERProgramList())
                # # retval = FSAAdapter.fetch_children_list_container(fsa_href.fsa_index, m.DERProgram, m.DERProgramList(href="/derp"), "DERProgram")
            # else:
            #     retval = adpt.FunctionSetAssignmentsAdapter.fetch(fsa_href.fsa_index)

            _log.debug(f"FSARequests GET response type: {type(retval)}")

            response = self.build_response_from_dataclass(retval)
            _log.info(f"FSARequests GET {request.path} - Status: {response.status_code}")
            return response

        except werkzeug.exceptions.HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            _log.error(f"Error in FSARequests GET {request.path}: {e}", exc_info=True)
            raise werkzeug.exceptions.InternalServerError(f"Internal server error: {str(e)}")
