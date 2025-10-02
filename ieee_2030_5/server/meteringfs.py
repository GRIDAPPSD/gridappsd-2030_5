"""
This module handles MirrorUsagePoint and UsagePoint constructs for a server.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import werkzeug.exceptions
from flask import Response, request
from werkzeug.exceptions import BadRequest

import ieee_2030_5.adapters as adpt
import ieee_2030_5.hrefs as hrefs
import ieee_2030_5.models as m
from ieee_2030_5.adapters import _get_href_generation_lock
from ieee_2030_5.data.indexer import get_href
from ieee_2030_5.server.base_request import RequestOp
from ieee_2030_5.utils import xml_to_dataclass

_log = logging.getLogger(__name__)


class Error(Exception):
    pass


@dataclass
class ResponseStatus:
    location: str
    status: str


class UsagePointRequest(RequestOp):
    def get(self) -> Response:
        start = int(request.args.get("s", 0))
        limit = int(request.args.get("l", 1))
        after = int(request.args.get("a", 0))
        parsed = hrefs.ParsedUsagePointHref(request.path)

        handled = False
        sort_by = []
        reversed = True

        if parsed.has_reading_list():
            sort_by = "timePeriod.start"
            if handled := parsed.reading_index is not None:
                obj = adpt.ListAdapter.get(parsed.last_list(), parsed.reading_index)

        elif parsed.has_reading_set_list():
            sort_by = "timePeriod.start"
            if handled := parsed.reading_set_index is not None:
                obj = adpt.ListAdapter.get(parsed.last_list(), parsed.reading_set_index)

        elif parsed.has_meter_reading_list():
            if handled := parsed.has_reading_type():
                obj = get_href(request.path)
            elif handled := parsed.meter_reading_index is not None:
                obj = adpt.ListAdapter.get(parsed.last_list(), parsed.meter_reading_index)
        else:
            obj = adpt.ListAdapter.get_resource_list(
                request.path, start=start, limit=limit, after=after, reverse=reversed
            )

        if not handled:
            obj = adpt.ListAdapter.get_resource_list(
                request.path, start=start, limit=limit, after=after, sort_by=sort_by, reverse=reversed
            )
        # # /upt
        # if not parsed.has_usage_point_index():
        #     obj = adpt.UsagePointAdapter.fetch_all(m.UsagePointList(request.path),
        #                                            start=start,
        #                                            limit=limit,
        #                                            after=after)
        # elif parsed.has_meter_reading_list() and not parsed.meter_reading_index:
        #     obj = adpt.MirrorUsagePointAdapter.fetch_all(m.MeterReadingList(request.path),
        #                                                  start=start,
        #                                                  limit=limit,
        #                                                  after=after)

        # else:
        #     obj = adpt.UsagePointAdapter.fetch(parsed.usage_point_index)

        # if parsed.has_extra():
        #     obj = get_href(request.path)

        return self.build_response_from_dataclass(obj)

    def post(self) -> Response:
        xml = request.data.decode("utf-8")
        data = xml_to_dataclass(request.data.decode("utf-8"))
        data_type = type(data)
        if data_type not in (m.MeterReading, m.ReadingSet):
            raise BadRequest("Only MeterReading and ReadingSet can be posted to UsagePoints")

        # Call the adapter function to handle the reading
        result = adpt.create_or_update_usage_point_reading(up_href=request.path, reading_input=data)

        if result.success:
            status = "204" if result.was_update == True else "201"
        else:
            status = "405"

        if status.startswith("20"):
            if result.location:
                return Response(headers={"Location": result.location}, status=status)
            return Response(headers={"Location": result.data.href}, status=status)
        else:
            return Response(result.data, status=status)


class MirrorUsagePointRequest(RequestOp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get(self) -> Response:
        pth_info = request.path
        if not pth_info.startswith(hrefs.DEFAULT_MUP_ROOT):
            raise ValueError(f"Invalid path for {self.__class__} {request.path}")
        mup_href = hrefs.ParsedUsagePointHref(request.path)
        if not mup_href.has_usage_point_index():
            # /mup - return filtered list for this client only

            # Get pagination parameters from query string
            start = int(request.args.get("s", 0))  # Start index (default 0)
            limit = int(request.args.get("l", 10))  # Limit (default 10 per IEEE 2030.5)
            after = int(request.args.get("a", 0))  # After time (for time-based filtering)

            _log.debug(f"MUP list request with pagination: start={start}, limit={limit}, after={after}")

            try:
                # WRITE-THEN-READ CONSISTENCY: Use per-client lock for reads to ensure consistency
                # but don't block reads from different clients (only block against writes)
                client_lock = _get_href_generation_lock(self.lfdi)

                with client_lock:
                    _log.debug(f"Acquired per-client lock for MUP list filtering - client LFDI: {self.lfdi}")

                    # Get all MUPs from the list (protected by lock to ensure consistency)
                    all_mups = adpt.ListAdapter.get_list(hrefs.DEFAULT_MUP_ROOT)

                    # Filter MUPs by client LFDI for privacy/security
                    # Use the metadata-based approach to check ownership
                    client_lfdi = self.lfdi  # Client's LFDI from certificate
                    filtered_mups = adpt.get_mups_for_client(client_lfdi)

                    _log.debug(
                        f"Filtered {len(filtered_mups)} MUPs from {len(all_mups)} total for client LFDI: {client_lfdi}"
                    )

                    # Apply pagination to the filtered list
                    total_count = len(filtered_mups)
                    end_index = min(start + limit, total_count)
                    paginated_mups = filtered_mups[start:end_index] if start < total_count else []

                    # Create filtered and paginated MirrorUsagePointList
                    mup = m.MirrorUsagePointList(
                        href=request.path,
                        MirrorUsagePoint=paginated_mups,
                        all=total_count,  # Total count of filtered MUPs
                        results=len(paginated_mups),  # Count of MUPs in this response
                    )

                    _log.debug(
                        f"Returning {len(paginated_mups)} of {total_count} MUPs for client {client_lfdi} (start={start}, limit={limit})"
                    )

            except KeyError:
                # Initialize the URI if it doesn't exist yet
                adpt.ListAdapter.initialize_uri(request.path, m.MirrorUsagePoint)

                # Create an empty MirrorUsagePointList
                mup = m.MirrorUsagePointList(href=request.path, MirrorUsagePoint=[], all=0, results=0)

            # Set the poll rate for mirror usage point
            mup.pollRate = adpt.get_poll_rate("mirror_usage_point")
        else:
            # /mup/0 - accessing specific MUP
            # WRITE-THEN-READ CONSISTENCY: Use per-client lock to ensure MUP access
            # doesn't see inconsistent state during concurrent MUP operations
            client_lock = _get_href_generation_lock(self.lfdi)

            with client_lock:
                _log.debug(
                    f"Acquired per-client lock for specific MUP access - client LFDI: {self.lfdi}, requested href: {request.path}"
                )

                # Find the MUP by its complete href instead of using index (which is global, not client-specific)
                all_mups = adpt.ListAdapter.get_list(hrefs.DEFAULT_MUP_ROOT)
                mup = None

                for candidate_mup in all_mups:
                    if hasattr(candidate_mup, "href") and candidate_mup.href == request.path:
                        mup = candidate_mup
                        break

                if mup is None:
                    raise werkzeug.exceptions.NotFound(f"Mirror usage point {request.path} not found")

                # Security check: Verify the MUP belongs to the requesting client
                # Use metadata to check authorization
                authorized = False
                client_lfdi_normalized = str(self.lfdi).lower().replace("\\x", "").replace(" ", "").replace("-", "")

                # Check metadata for ownership
                metadata = adpt.get_mup_metadata(mup.href)
                if metadata:
                    created_by_lfdi = metadata.get("createdByLFDI")
                    if created_by_lfdi and created_by_lfdi == client_lfdi_normalized:
                        authorized = True
                        _log.debug(
                            f"MUP AUTHORIZATION: Client {self.lfdi} authorized as creator of MUP {request.path} (from metadata)"
                        )

                # Also check deviceLFDI for backward compatibility and multi-device scenarios
                if not authorized and hasattr(mup, "deviceLFDI") and mup.deviceLFDI:
                    if isinstance(mup.deviceLFDI, bytes):
                        mup_lfdi_normalized = mup.deviceLFDI.hex().lower()
                    else:
                        mup_lfdi_normalized = (
                            str(mup.deviceLFDI).lower().replace("\\x", "").replace(" ", "").replace("-", "")
                        )

                    if mup_lfdi_normalized == client_lfdi_normalized:
                        authorized = True
                        _log.debug(
                            f"MUP AUTHORIZATION: Client {self.lfdi} authorized via deviceLFDI match for MUP {request.path}"
                        )

                if not authorized:
                    _log.warning(f"Client {self.lfdi} attempted unauthorized access to MUP {request.path}")
                    raise werkzeug.exceptions.Forbidden("Access denied to this MirrorUsagePoint")

        return self.build_response_from_dataclass(mup)

    def post(self) -> Response:
        xml = request.data.decode("utf-8")
        data = xml_to_dataclass(request.data.decode("utf-8"))
        data_type = type(data)
        if data_type not in (m.MirrorUsagePoint, m.MirrorReadingSet, m.MirrorMeterReading):
            raise BadRequest()

        pth_info = request.path

        # For top-level /mup posts, only allow MirrorUsagePoint creation if no existing MUPs exist
        # Allow MirrorMeterReading and MirrorReadingSet if there are existing MUPs to associate with
        if pth_info == hrefs.DEFAULT_MUP_ROOT and data_type is not m.MirrorUsagePoint:
            # Check if there are any existing MirrorUsagePoints
            try:
                existing_mups = adpt.ListAdapter.get_list(hrefs.DEFAULT_MUP_ROOT)
                if not existing_mups:
                    raise BadRequest("Must post MirrorUsagePoint to top level first before posting readings")
            except KeyError:
                # No MUPs exist yet
                raise BadRequest("Must post MirrorUsagePoint to top level first before posting readings")

        # Creating a new mup
        if data_type == m.MirrorUsagePoint:
            if data.postRate is None:
                data.postRate = self.server_config.post_rate
            _log.debug(f"POST /mup request - Client LFDI: {self.lfdi}")
            _log.debug(f"POST /mup request - MUP deviceLFDI from XML: {getattr(data, 'deviceLFDI', 'None')}")
            _log.debug(f"POST /mup request - MUP deviceLFDI type: {type(getattr(data, 'deviceLFDI', None))}")

            # Allow client to specify deviceLFDI for multi-device scenarios
            # If not provided, default to the authenticated client's LFDI
            if not hasattr(data, "deviceLFDI") or data.deviceLFDI is None:
                data.deviceLFDI = self.lfdi  # Already normalized in flask_server.py
                _log.debug(f"POST /mup request - No deviceLFDI provided, using client LFDI: {data.deviceLFDI}")
            else:
                _log.debug(f"POST /mup request - Preserving provided deviceLFDI: {data.deviceLFDI}")

            # Pass the client LFDI to the adapter for metadata tracking
            _log.debug(
                f"POST /mup request - About to call create_mirror_usage_point for client LFDI: {self.lfdi}, MUP mRID: {getattr(data, 'mRID', None)}"
            )
            result = adpt.create_mirror_usage_point(mup=data, client_lfdi=self.lfdi)
            _log.debug(f"POST /mup request - Created MUP with client LFDI tracking: {self.lfdi}")
            _log.debug(
                f"POST /mup request - Adapter result: success={result.success}, was_update={getattr(result, 'was_update', None)}, location={getattr(result, 'location', None)}, data.href={getattr(result.data, 'href', None) if result.data else None}"
            )
            # result = adpt.MirrorUsagePointAdapter.create(mup=data)
        else:
            # For readings posted to /mup, find the appropriate MirrorUsagePoint for this client
            if pth_info == hrefs.DEFAULT_MUP_ROOT:
                # WRITE-THEN-READ CONSISTENCY: Use per-client lock to ensure MUP finding
                # doesn't see inconsistent state during concurrent MUP operations
                client_lock = _get_href_generation_lock(self.lfdi)

                with client_lock:
                    _log.debug(
                        f"Acquired per-client lock for MUP finding during reading POST - client LFDI: {self.lfdi}"
                    )

                    # Find MUP that matches this client's LFDI
                    existing_mups = adpt.ListAdapter.get_list(hrefs.DEFAULT_MUP_ROOT)
                    target_mup_href = None

                    _log.debug(f"Looking for MUP for client LFDI: {self.lfdi}")
                    _log.debug(f"Found {len(existing_mups)} existing MUPs")

                    # Use metadata-based approach to find MUPs for this client
                    client_mups = adpt.get_mups_for_client(self.lfdi)

                    _log.debug(f"Found {len(client_mups)} MUPs for client LFDI: {self.lfdi}")

                    if client_mups:
                        # Use the first MUP for this client (or could implement logic to select specific one)
                        target_mup_href = client_mups[0].href
                        _log.debug(f"Using MUP: {target_mup_href} for client")
                    else:
                        target_mup_href = None

                    if target_mup_href is None:
                        _log.warning(
                            f"No MirrorUsagePoint found for client LFDI {self.lfdi} among {len(existing_mups)} MUPs"
                        )
                        raise BadRequest("No MirrorUsagePoint found for this client")

                    _log.debug(f"Using target MUP href: {target_mup_href} (with per-client lock protection)")

                # Call meter reading creation outside the lock (it has its own locking)
                result = adpt.create_or_update_meter_reading(
                    mup_href=target_mup_href, mmr_input=data, client_lfdi=self.lfdi
                )
            else:
                # Direct href provided (e.g., /mup_12_0)
                result = adpt.create_or_update_meter_reading(
                    mup_href=request.path, mmr_input=data, client_lfdi=self.lfdi
                )

        if result.success:
            status = "204" if result.was_update == True else "201"
        else:
            # Use specific status code from result if available
            status = str(getattr(result, "status_code", 400))

        if status.startswith("20"):
            if result.location:
                _log.debug(
                    f"POST /mup response - Returning Location header: {result.location} to client LFDI: {self.lfdi}"
                )
                return Response(headers={"Location": result.location}, status=status)
            _log.debug(
                f"POST /mup response - Returning data.href Location header: {result.data.href} to client LFDI: {self.lfdi}"
            )
            return Response(headers={"Location": result.data.href}, status=status)
        else:
            return Response(result.error if hasattr(result, "error") else result.data, status=status)
