import logging
from dataclasses import asdict

import werkzeug.exceptions
from flask import Response, request
from werkzeug.exceptions import BadRequest, NotFound

import ieee_2030_5.adapters as adpt
import ieee_2030_5.hrefs as hrefs
import ieee_2030_5.models as m
from ieee_2030_5.data.indexer import get_href
from ieee_2030_5.server.base_request import RequestOp
from ieee_2030_5.utils import xml_to_dataclass

_log = logging.getLogger(__name__)


class DERRequests(RequestOp):
    """
    Class supporting end devices and any of the subordinate calls to it.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def put(self) -> Response:
        """Allows putting of 2030.5 DER data to the server."""
        _log.info(f"=== DERRequests PUT ENTRY === Path: {request.path} - LFDI: {self.lfdi}")
        _log.info(f"Request method: {request.method}, Content-Type: {request.content_type}")

        try:
            if not request.path.startswith(hrefs.DEFAULT_DER_ROOT):
                _log.warning(f"Invalid DER path: {request.path}")
                raise ValueError(f"Invalid path for {self.__class__} {request.path}")

            if not request.data:
                _log.warning("PUT request missing data")
                raise BadRequest("Request data is required")

            _log.info(f"PUT data length: {len(request.data)}")
            _log.info(f"PUT data content: {request.data[:200]}...")  # First 200 chars

            parser = hrefs.HrefParser(request.path)
            _log.info(f"Parsed href parts: {[parser.at(i) for i in range(parser.count())]}")

            clstype = {
                hrefs.DER_SETTINGS: m.DERSettings,
                hrefs.DER_STATUS: m.DERStatus,
                hrefs.DER_CAPABILITY: m.DERCapability,
                hrefs.DER_AVAILABILITY: m.DERAvailability,
                hrefs.DER_PROGRAM: m.DERProgram,
            }

            data = request.get_data(as_text=True)
            data = xml_to_dataclass(data, clstype[parser.at(4)])

            _log.debug(f"Parsed DER object type: {type(data)}")

            # if request.path.endswith("ders") or request.path.endswith("derg"):
            #     print(f"----------------------DER PUT {request.path} {data}")

            _log.info(f"=== CALLING STORAGE === DER PUT {request.path} {asdict(data)}")
            result = adpt.ListAdapter.set_single(uri=f"{request.path}", obj=data, lfdi=self.lfdi)
            _log.info(f"Storage result - Success: {result.success}, Error: {result.error}")
            rep = adpt.ListAdapter.get_single(uri=f"{request.path}")
            print(f"REP-----------------------: {rep}")
            if not result.success:
                _log.error(f"Failed to store DER object: {result.error}")
                raise werkzeug.exceptions.InternalServerError(f"Failed to store DER object: {result.error}")

            response = self.build_response_from_dataclass(data)
            _log.info(f"=== DERRequests PUT COMPLETE === {request.path} - Status: {response.status_code}")
            return response

        except werkzeug.exceptions.HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            _log.error(f"Error in DERRequests PUT {request.path}: {e}", exc_info=True)
            raise werkzeug.exceptions.InternalServerError(f"Internal server error: {str(e)}")

    def get(self) -> Response:
        """Get DER resource data."""
        _log.debug(f"DERRequests GET: {request.path} - LFDI: {self.lfdi}")

        try:
            if not request.path.startswith(hrefs.DEFAULT_DER_ROOT):
                _log.warning(f"Invalid DER path: {request.path}")
                raise ValueError(f"Invalid path for {self.__class__} {request.path}")

            value = adpt.ListAdapter.get_single(request.path)
            _log.debug(f"Retrieved value from adapter: {value is not None}")

            if value is None:
                _log.debug(f"Creating default resource for path: {request.path}")
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
                    subpath = parser.at(4)
                    value = subpaths[subpath]
                    _log.debug(f"Created {subpath} resource for index {index}")

            if value is None:
                _log.warning(f"No DER resource found for path: {request.path}")
                raise NotFound(f"Resource not found: {request.path}")

            # pth_split = request.path.split(hrefs.SEP)

            # if len(pth_split) == 1:
            #     # TODO Add arguments
            #     value = adpt.DERAdapter.fetch_list()
            # else:
            #     value = adpt.DERAdapter.fetch_at(int(pth_split[1]))

            response = self.build_response_from_dataclass(value)
            _log.info(f"DERRequests GET {request.path} - Status: {response.status_code}")
            return response

        except werkzeug.exceptions.HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            _log.error(f"Error in DERRequests GET {request.path}: {e}", exc_info=True)
            raise werkzeug.exceptions.InternalServerError(f"Internal server error: {str(e)}")


class DERProgramRequests(RequestOp):
    """
    Class supporting end devices and any of the subordinate calls to it.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get(self) -> Response:
        """Get DER Program resources."""
        _log.debug(f"DERProgramRequests GET: {request.path} - LFDI: {self.lfdi}")

        try:
            _log.debug(f"Processing get request for: {request.path} with args: {[x for x in request.args.keys()]}")
            start = int(request.args.get("s", 0))
            after = int(request.args.get("a", 0))
            limit = int(request.args.get("l", 1))

            parsed = hrefs.HrefParser(request.path)
            _log.debug(f"Parsed path - count: {parsed.count()}, has_index: {parsed.has_index()}")

            if not parsed.has_index():
                _log.debug("Getting DER Program list")
                retval = adpt.ListAdapter.get_resource_list(hrefs.DEFAULT_DERP_ROOT, start, after, limit)
            elif parsed.count() == 2:
                _log.debug(f"Getting single DER Program at index {parsed.at(1)}")
                retval = adpt.ListAdapter.get(hrefs.DEFAULT_DERP_ROOT, parsed.at(1))
            elif parsed.count() == 4:
                _log.debug("Retrieving DER Control list")
                # Retrieve the list of controls from storage
                dercl = get_href(parsed.join(3))
                assert isinstance(dercl, m.DERControlList)
                # The index that we want to get the control from.
                retval = dercl.DERControl[parsed.at(3)]
            elif parsed.at(2) == hrefs.DERC:
                _log.debug("Retrieving DERC")
                retval = adpt.ListAdapter.get_resource_list(request.path, start, after, limit)
                if hasattr(retval, "mRID"):
                    # Use the global mRIDs registry to get the latest version
                    found_item = adpt.get_global_mrids().get_item(retval.mRID)
                    if found_item is not None:
                        retval = found_item
                        _log.debug(f"Found DERC in GlobalmRIDs registry: {retval.mRID}")
                # Note: IEEE 2030.5 does not define pollRate for DERControlList
                # Empty DERControlList means client should check DefaultDERControl if available
            elif parsed.at(2) == hrefs.DDERC:
                _log.debug("Retrieving DDERC")
                retval = adpt.ListAdapter.get_single(request.path)
                if hasattr(retval, "mRID"):
                    # Use the global mRIDs registry to get the latest version
                    found_item = adpt.get_global_mrids().get_item(retval.mRID)
                    if found_item is not None:
                        retval = found_item
                        _log.debug(f"Found DDERC in GlobalmRIDs registry: {retval.mRID}")
                _log.debug("Retrieving DDERC")
                retval = adpt.ListAdapter.get_single(request.path)
                if hasattr(retval, "mRID"):
                    retval = adpt.GlobalmRIDs.get_item(retval.mRID)
            elif parsed.at(2) == hrefs.DERCURVE:
                _log.debug("Retrieving DC")
                retval = adpt.ListAdapter.get_resource_list(request.path, start, after, limit)
            # elif parsed.at(2) == hrefs.DDERC:
            #     retval = adpt.DERControlAdapter.fetch_at(parsed.at(3))
            else:
                _log.debug(f"Getting resource from href: {request.path}")
                retval = get_href(request.path)

            if not retval:
                _log.warning(f"No DER Program resource found for path: {request.path}")
                raise NotFound(f"{request.path}")

            _log.debug(f"DERProgramRequests GET response type: {type(retval)}")

            response = self.build_response_from_dataclass(retval)
            _log.info(f"DERProgramRequests GET {request.path} - Status: {response.status_code}")
            return response

        except werkzeug.exceptions.HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            _log.error(f"Error in DERProgramRequests GET {request.path}: {e}", exc_info=True)
            raise werkzeug.exceptions.InternalServerError(f"Internal server error: {str(e)}")
