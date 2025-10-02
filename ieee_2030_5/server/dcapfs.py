import logging

import werkzeug
from flask import Response, request

import ieee_2030_5.adapters as adpt
import ieee_2030_5.hrefs as hrefs
import ieee_2030_5.models as m
from ieee_2030_5.server.base_request import RequestOp

_log = logging.getLogger(__name__)


class DcapRequest(RequestOp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get(self) -> Response:
        """Get Device Capability for the authenticated device."""
        _log.debug(f"DcapRequest GET: {request.path} - LFDI: {self.lfdi}")

        try:
            # TODO: Test for allowed dcap here.
            # if not self._end_devices.allowed_to_connect(self.lfdi):
            #     raise werkzeug.exceptions.Unauthorized()

            # Fast LFDI metadata lookup - much faster than loading full device
            lfdi_metadata = adpt.EndDeviceAdapter.fetch_lfdi_metadata(self.lfdi)
            if not lfdi_metadata:
                _log.warning(f"No device found for LFDI: {self.lfdi}")
                raise werkzeug.exceptions.NotFound(f"No device found for LFDI {self.lfdi}")

            device_index = lfdi_metadata["device_index"]
            _log.debug(f"Found device via fast LFDI lookup - Index: {device_index}, mRID: {lfdi_metadata.get('mRID')}")

            # Construct dcap_href using the proper URL builder from hrefs
            dcap_href = f"{hrefs.DEFAULT_DCAP_ROOT}{hrefs.SEP}{device_index}"
            _log.debug(f"Device capability href: {dcap_href}")

            # Ensure specialized adapters are initialized
            adpt.ensure_specialized_adapters_initialized()

            # Get the DeviceCapability
            cap = adpt.DeviceCapabilityAdapter.get_single(dcap_href)
            if not cap:
                _log.debug(f"Creating new DeviceCapability for index {device_index}")
                try:
                    # Create a DeviceCapability using DeviceCapabilityHref helper
                    dcap_href_helper = hrefs.DeviceCapabilityHref(device_index)
                    cap = dcap_href_helper.fill_hrefs(m.DeviceCapability())
                    # Set the poll rate for device capability
                    cap.pollRate = adpt.get_poll_rate("device_capability")
                    # Store it for future requests
                    result = adpt.DeviceCapabilityAdapter.set_single(dcap_href, cap)
                    if not result.success:
                        _log.error(f"Failed to store device capability: {result.error}")
                except Exception as e:
                    _log.error(f"Failed to create device capability: {e}")
                    raise werkzeug.exceptions.InternalServerError(
                        f"Failed to create device capability for index {device_index}"
                    )

            if not cap:
                _log.error(f"No device capability found or created for index {device_index}")
                raise werkzeug.exceptions.NotFound(f"No device capability found for index {device_index}")

            # Always return the canonical /dcap href regardless of device index
            # This is required by IEEE 2030.5 standard
            cap.href = hrefs.DEFAULT_DCAP_ROOT
            _log.debug(f"Returning DeviceCapability: {hrefs.DEFAULT_DCAP_ROOT}")

            response = self.build_response_from_dataclass(cap)
            _log.info(f"DcapRequest GET {request.path} - Status: {response.status_code}")
            return response

        except werkzeug.exceptions.HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            _log.error(f"Error in DcapRequest GET {request.path}: {e}", exc_info=True)
            raise werkzeug.exceptions.InternalServerError(f"Internal server error: {str(e)}")
