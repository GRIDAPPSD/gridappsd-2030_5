# ieee_2030_5/adapters/__init__.py
"""
Thread-safe adapters for IEEE 2030.5 server.
"""

import logging
import threading
import time
from pathlib import Path

import OpenSSL
from blinker import Signal
from flask import Response, g, request

import ieee_2030_5.models as m
from ieee_2030_5 import hrefs
from ieee_2030_5.certs import TLSRepository, lfdi_from_fingerprint, sfdi_from_lfdi
from ieee_2030_5.config import DeviceConfiguration, ServerConfiguration
from ieee_2030_5.persistance.points import atomic_operation, get_db
from ieee_2030_5.utils import dataclass_to_xml, xml_to_dataclass

from .base import (
    AdapterResult,
    ThreadSafeEndDeviceAdapter,
    ThreadSafeListAdapter,
    get_adapter_stats,
    initialize_adapters,
)


# Import the global instances
# Dynamic adapter access functions to get updated references after initialization
def get_list_adapter():
    """Get the current ListAdapter instance after initialization."""
    from .base import ListAdapter

    return ListAdapter


def get_end_device_adapter():
    """Get the current EndDeviceAdapter instance after initialization."""
    from .base import EndDeviceAdapter

    return EndDeviceAdapter


# For backward compatibility, create module-level references that will be updated
ListAdapter = None
EndDeviceAdapter = None

# Global poll rate settings for different resource types
# These can be individually configured as needed
_poll_rates = {
    "default": 120,  # 2 minutes for all resources
    "device_capability": 120,
    "end_device_list": 120,
    "der_list": 120,
    "der_program_list": 120,
    # Note: 'der_control_list' removed - DERControlList does not have pollRate per IEEE 2030.5
    "fsa_list": 120,
    "mirror_usage_point": 120,
    "usage_point": 120,
    "registration": 120,
    "log_event_list": 120,
    # Note: 'meter_reading' removed - MeterReadingList does not have pollRate per IEEE 2030.5
    "reading_set": 120,
    "time": 120,
}


def set_poll_rate(resource_type: str, poll_rate: int):
    """Set the poll rate for a specific resource type."""
    _poll_rates[resource_type] = poll_rate
    _log.debug(f"Poll rate for {resource_type} set to {poll_rate} seconds")


def get_poll_rate(resource_type: str = "default") -> int:
    """Get the poll rate for a specific resource type."""
    return _poll_rates.get(resource_type, _poll_rates["default"])


def configure_poll_rates(config):
    """Configure poll rates from server configuration."""
    # Set the default poll rate
    if hasattr(config, "poll_rate"):
        _poll_rates["default"] = config.poll_rate
        # Also set as default for all unspecified types
        for key in _poll_rates:
            if key != "default":
                _poll_rates[key] = config.poll_rate

    # Override with specific poll rates if configured
    if hasattr(config, "device_capability_poll_rate"):
        _poll_rates["device_capability"] = config.device_capability_poll_rate

    if hasattr(config, "log_event_list_poll_rate"):
        _poll_rates["log_event_list"] = config.log_event_list_poll_rate

    if hasattr(config, "mirror_usage_point_post_rate"):
        _poll_rates["mirror_usage_point"] = config.mirror_usage_point_post_rate

    # Future poll rates can be added here
    # if hasattr(config, 'der_control_poll_rate'):
    #     _poll_rates['der_control_list'] = config.der_control_poll_rate

    _log.info(f"Poll rates configured: {_poll_rates}")


# Backward compatibility
def set_global_poll_rate(poll_rate: int):
    """Set the default poll rate (backward compatibility)."""
    set_poll_rate("default", poll_rate)


def get_global_poll_rate() -> int:
    """Get the default poll rate (backward compatibility)."""
    return get_poll_rate("default")


def _update_global_adapters():
    """Update the global adapter references after initialization."""
    global ListAdapter, EndDeviceAdapter
    from .base import EndDeviceAdapter as BaseEndDeviceAdapter
    from .base import ListAdapter as BaseListAdapter

    ListAdapter = BaseListAdapter
    EndDeviceAdapter = BaseEndDeviceAdapter


_log = logging.getLogger(__name__)

# Thread-safe locks for HREF generation per client LFDI to prevent race conditions
_href_generation_locks = {}
_href_lock_manager = threading.RLock()

# Pre-loaded EndDevice mapping cache to eliminate lookup race conditions
_enddevice_cache = {}
_enddevice_cache_lock = threading.RLock()
_enddevice_cache_initialized = False

# MUP metadata storage for tracking which client created each MUP
# Key: MUP href, Value: dict with metadata including createdByLFDI
_mup_metadata = {}
_mup_metadata_lock = threading.RLock()


def _normalize_lfdi_for_cache(lfdi):
    """Normalize LFDI to consistent format for cache key."""
    if isinstance(lfdi, bytes):
        return lfdi.hex().lower()
    else:
        # Remove any non-hex characters and convert to lowercase
        return str(lfdi).lower().replace("\\x", "").replace(" ", "").replace("-", "")


def _initialize_enddevice_cache():
    """Pre-load all EndDevices into a thread-safe cache for fast lookups."""
    global _enddevice_cache_initialized

    with _enddevice_cache_lock:
        if _enddevice_cache_initialized:
            return  # Already initialized

        try:
            _log.info("Initializing EndDevice cache for fast LFDI lookups...")

            # Get all EndDevices from the system
            EndDeviceAdapter = get_end_device_adapter()
            if EndDeviceAdapter is None:
                _log.warning("EndDeviceAdapter not available, skipping cache initialization")
                return

            all_devices_list = EndDeviceAdapter.fetch_all()

            # Clear and rebuild cache
            _enddevice_cache.clear()

            # Extract the actual devices from the EndDeviceList
            all_devices = all_devices_list.EndDevice if hasattr(all_devices_list, "EndDevice") else []

            for device in all_devices:
                if hasattr(device, "lFDI") and device.lFDI:
                    # Normalize LFDI for consistent lookups
                    normalized_lfdi = _normalize_lfdi_for_cache(device.lFDI)

                    # Extract client_index from device href
                    client_index = None
                    if device.href:
                        href_parts = device.href.strip("/").split(hrefs.SEP)
                        if len(href_parts) >= 2:
                            client_index = href_parts[-1]

                    # Cache the device with normalized LFDI as key
                    _enddevice_cache[normalized_lfdi] = {
                        "device": device,
                        "client_index": client_index,
                        "lfdi_bytes": device.lFDI if isinstance(device.lFDI, bytes) else bytes.fromhex(normalized_lfdi),
                        "lfdi_normalized": normalized_lfdi,
                    }

                    _log.debug(
                        f"Cached EndDevice: LFDI={normalized_lfdi}, client_index={client_index}, href={device.href}"
                    )

            _enddevice_cache_initialized = True
            _log.info(f"EndDevice cache initialized with {len(_enddevice_cache)} devices")

        except Exception as e:
            _log.error(f"Failed to initialize EndDevice cache: {e}")
            # Don't set initialized flag so it can be retried


def _get_enddevice_from_cache(lfdi):
    """Get EndDevice from cache with fallback to dynamic lookup."""
    normalized_lfdi = _normalize_lfdi_for_cache(lfdi)

    with _enddevice_cache_lock:
        # Initialize cache if not done yet
        if not _enddevice_cache_initialized:
            _initialize_enddevice_cache()

        # Lookup device in cache
        device_info = _enddevice_cache.get(normalized_lfdi)
        if device_info:
            _log.debug(
                f"Cache HIT: Found EndDevice for LFDI {normalized_lfdi}, client_index={device_info['client_index']}"
            )
            return device_info
        else:
            _log.warning(f"Cache MISS: No EndDevice found for LFDI {normalized_lfdi}")

            # FALLBACK: Try dynamic lookup and cache the result
            try:
                EndDeviceAdapter = get_end_device_adapter()
                if EndDeviceAdapter is not None:
                    # Convert LFDI to bytes for the adapter
                    if isinstance(lfdi, bytes):
                        lfdi_bytes = lfdi
                    else:
                        try:
                            lfdi_bytes = bytes.fromhex(str(lfdi))
                        except ValueError:
                            lfdi_bytes = str(lfdi).encode("utf-8")

                    _log.debug(f"Fallback: Attempting dynamic lookup for LFDI {normalized_lfdi}")
                    device = EndDeviceAdapter.fetch_by_lfdi(lfdi_bytes)

                    if device:
                        # Extract client_index from device href
                        client_index = None
                        if device.href:
                            href_parts = device.href.strip("/").split(hrefs.SEP)
                            if len(href_parts) >= 2:
                                client_index = href_parts[-1]

                        # Cache the dynamically found device for future use
                        device_info = {
                            "device": device,
                            "client_index": client_index,
                            "lfdi_bytes": lfdi_bytes,
                            "lfdi_normalized": normalized_lfdi,
                        }
                        _enddevice_cache[normalized_lfdi] = device_info

                        _log.info(
                            f"Fallback SUCCESS: Cached EndDevice for LFDI {normalized_lfdi}, client_index={client_index}"
                        )
                        return device_info
                    else:
                        _log.error(f"Fallback FAILED: No EndDevice found for LFDI {normalized_lfdi}")
                        return None
                else:
                    _log.error("Fallback FAILED: EndDeviceAdapter not available")
                    return None
            except Exception as e:
                _log.error(f"Fallback ERROR: Dynamic lookup failed for LFDI {normalized_lfdi}: {e}")
                return None


def _get_href_generation_lock(client_lfdi):
    """Get or create a thread-safe lock for HREF generation for a specific client LFDI."""
    # Normalize LFDI to consistent hex string format for lock key
    if isinstance(client_lfdi, bytes):
        lock_key = client_lfdi.hex()
    else:
        # Remove any non-hex characters and convert to lowercase
        lock_key = str(client_lfdi).lower().replace("\\x", "").replace(" ", "").replace("-", "")

    _log.debug(f"LOCK GENERATION DEBUG: client_lfdi={client_lfdi}, type={type(client_lfdi)}, normalized_key={lock_key}")

    with _href_lock_manager:
        if lock_key not in _href_generation_locks:
            _href_generation_locks[lock_key] = threading.RLock()
            _log.debug(f"LOCK GENERATION DEBUG: Created new lock for key: {lock_key}")
        return _href_generation_locks[lock_key]


# Lazy initialization of specialized adapters
_specialized_adapters = {}
_specialized_adapters_lock = threading.Lock()


def _get_or_create_adapter(name, model_class):
    """Get or create a specialized adapter lazily."""
    if name not in _specialized_adapters:
        with _specialized_adapters_lock:
            if name not in _specialized_adapters:
                from .base import ensure_adapters_initialized

                ensure_adapters_initialized()  # Ensure base adapters are initialized
                _specialized_adapters[name] = ThreadSafeListAdapter(model_class)
    return _specialized_adapters[name]


# Create module-level adapter instances that are initialized lazily
# These will be actual adapter instances, not functions
DERAdapter = None
DERControlAdapter = None
DERProgramAdapter = None
DERCurveAdapter = None
FunctionSetAssignmentsAdapter = None
DeviceCapabilityAdapter = None
RegistrationAdapter = None


def _initialize_specialized_adapters():
    """Initialize all specialized adapters if not already done."""
    global DERAdapter, DERControlAdapter, DERProgramAdapter, DERCurveAdapter
    global FunctionSetAssignmentsAdapter, DeviceCapabilityAdapter, RegistrationAdapter

    if DeviceCapabilityAdapter is None:
        DERAdapter = _get_or_create_adapter("DER", m.DER)
        DERControlAdapter = _get_or_create_adapter("DERControl", m.DERControl)
        DERProgramAdapter = _get_or_create_adapter("DERProgram", m.DERProgram)
        DERCurveAdapter = _get_or_create_adapter("DERCurve", m.DERCurve)
        FunctionSetAssignmentsAdapter = _get_or_create_adapter("FunctionSetAssignments", m.FunctionSetAssignments)
        DeviceCapabilityAdapter = _get_or_create_adapter("DeviceCapability", m.DeviceCapability)
        RegistrationAdapter = _get_or_create_adapter("Registration", m.Registration)


# Initialize adapters on module load (but after database configuration)
def ensure_specialized_adapters_initialized():
    """Ensure specialized adapters are initialized. Safe to call multiple times."""
    if DeviceCapabilityAdapter is None:
        _initialize_specialized_adapters()


# Add compatibility method for list_size
def list_size(list_uri: str) -> int:
    """Compatibility method for existing code that uses list_size."""
    return ListAdapter.get_list_size(list_uri)


# Method will be added to ListAdapter instance during initialization


# Create a TimeAdapter for time operations
class TimeAdapter:
    """Thread-safe adapter for time operations."""

    def __init__(self):
        self._lock = threading.RLock()
        # Add the signals
        self.event_started = Signal()
        self.event_ended = Signal()
        self.time_changed = Signal()

    @property
    def current_tick(self):
        """Get current time tick in a thread-safe manner."""
        import time

        with self._lock:
            return int(time.time())


# Create singleton instance
TimeAdapter = TimeAdapter()

__all__ = [
    "ListAdapter",
    "EndDeviceAdapter",
    "DERAdapter",
    "DERControlAdapter",
    "DERProgramAdapter",
    "DERCurveAdapter",
    "FunctionSetAssignmentsAdapter",
    "DeviceCapabilityAdapter",
    "RegistrationAdapter",
    "TimeAdapter",
    "initialize_adapters",
    "get_adapter_stats",
    "AdapterResult",
]


# Helper function for certificate names
def normalize_certificate_name(href: str) -> str:
    """Normalize certificate name from href."""
    return href.rsplit(hrefs.SEP, 1)[-1]


# Helper function to extract LFDI from certificate
def get_lfdi_from_cert_file(cert_path: str) -> str:
    """Extract LFDI from certificate file."""
    try:
        with open(cert_path, "rb") as cert_file:
            cert_data = cert_file.read()
            x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert_data)
            fingerprint = x509.digest("sha256").decode("ascii")
            return lfdi_from_fingerprint(fingerprint)
    except Exception as e:
        _log.error(f"Error getting LFDI from certificate: {e}")
        raise


# Thread-safe certificate operations helper
import fcntl
from contextlib import contextmanager

_cert_locks = {}
_cert_locks_lock = threading.Lock()


@contextmanager
def certificate_lock(cert_name: str):
    """Thread-safe certificate file operations."""
    with _cert_locks_lock:
        if cert_name not in _cert_locks:
            _cert_locks[cert_name] = threading.Lock()
        lock = _cert_locks[cert_name]
    with lock:
        yield


def _admin_enddevices(self) -> Response:
    """Thread-safe version of enddevice management."""
    if request.method in ("POST", "PUT"):
        data = request.data.decode("utf-8")
        item = xml_to_dataclass(data)
        if not isinstance(item, m.EndDevice):
            _log.error("EndDevice was not passed via data.")
            return Response(status=400)
        if request.method == "POST":
            if item.href:
                _log.error(f"POST method with existing object {item.href}")
                return Response(status=400)
            # Thread-safe add with automatic conflict detection
            try:
                # Check if device already exists by LFDI
                existing = EndDeviceAdapter.fetch_by_property("lFDI", item.lFDI)
                if existing:
                    return Response("Device already exists", status=409)
                # Add new device
                item = EndDeviceAdapter.add(item)
                # Create certificate (this should also be made thread-safe)
                cert_filename = normalize_certificate_name(item.href)
                tls_repo: TLSRepository = g.TLS_REPOSITORY
                # Use file locking for certificate operations
                with certificate_lock(cert_filename):
                    cert, key = tls_repo.get_file_pair(cert_filename)
                    # Check if files exist and remove them
                    Path(cert).unlink(missing_ok=True)
                    Path(key).unlink(missing_ok=True)
                    # Create new certificate
                    tls_repo.create_cert(cert_filename)
                    # Get LFDI and SFDI from the certificate
                    item.lFDI = tls_repo.lfdi(cert_filename)
                    item.sFDI = tls_repo.sfdi(cert_filename)
                response_status = 201
            except Exception as e:
                _log.error(f"Failed to create end device: {e}")
                return Response("Internal server error", status=500)
        elif request.method == "PUT":
            if not item.href:
                _log.error("PUT method without an existing object.")
                return Response(status=400)
            # Thread-safe update
            try:
                index = int(item.href.rsplit(hrefs.SEP)[-1])
                result = EndDeviceAdapter.put(index, item)
                if not result.success:
                    return Response(result.error, status=400)
                response_status = 200
            except Exception as e:
                _log.error(f"Failed to update end device: {e}")
                return Response("Internal server error", status=500)
        return Response(dataclass_to_xml(item), status=response_status)
    # GET request - thread-safe list retrieval
    start = int(request.args.get("s", 0))
    after = int(request.args.get("a", 0))
    limit = int(request.args.get("l", 1))
    try:
        # This is now thread-safe
        allofem = EndDeviceAdapter.fetch_all(m.EndDeviceList(), start=start, after=after, limit=limit)
        return Response(dataclass_to_xml(allofem), status=200)
    except Exception as e:
        _log.error(f"Failed to fetch end devices: {e}")
        return Response("Internal server error", status=500)


def _admin_controls(self) -> Response:
    """Thread-safe DER control management."""
    if request.method in ("POST", "PUT"):
        data = request.data.decode("utf-8")
        control = xml_to_dataclass(data)
        if not isinstance(control, m.DERControl):
            _log.error("DERControl was not passed via data.")
            return Response(status=400)
        if request.method == "POST":
            if control.href:
                _log.error(f"POST method with existing object {control.href}")
                return Response(status=400)
            # Thread-safe add
            try:
                result = DERControlAdapter.append(hrefs.DEFAULT_CONTROL_ROOT, control)
                if result.success:
                    return Response(dataclass_to_xml(result.data), status=201, headers={"Location": result.location})
                else:
                    return Response(result.error, status=400)
            except Exception as e:
                _log.error(f"Failed to add DER control: {e}")
                return Response("Internal server error", status=500)
        elif request.method == "PUT":
            if not control.href:
                _log.error("PUT method without an existing object.")
                return Response(status=400)
            try:
                index = int(control.href.rsplit(hrefs.SEP)[-1])
                result = DERControlAdapter.put(hrefs.DEFAULT_CONTROL_ROOT, index, control)
                if result.success:
                    return Response(dataclass_to_xml(result.data), status=200)
                else:
                    return Response(result.error, status=400)
            except Exception as e:
                _log.error(f"Failed to update DER control: {e}")
                return Response("Internal server error", status=500)
    # GET request
    start = int(request.args.get("s", 0))
    after = int(request.args.get("a", 0))
    limit = int(request.args.get("l", 1))
    try:
        control_list = DERControlAdapter.get_resource_list(
            hrefs.DEFAULT_CONTROL_ROOT, start=start, after=after, limit=limit
        )
        return Response(dataclass_to_xml(control_list), status=200)
    except Exception as e:
        _log.error(f"Failed to fetch DER controls: {e}")
        return Response("Internal server error", status=500)


def create_mirror_usage_point(mup: m.MirrorUsagePoint, client_lfdi: str = None) -> AdapterResult:
    """Thread-safe mirror usage point creation with atomic operations to prevent race conditions."""
    try:
        # Get existing MUPs - reading doesn't need to be in a transaction
        try:
            existing_mups = ListAdapter.get_list(hrefs.DEFAULT_MUP_ROOT)
        except Exception as e:
            _log.debug(f"No existing MUPs found or error reading list: {e}")
            existing_mups = []

        # Check if MirrorUsagePoint already exists by mRID AND belongs to the same client
        # IMPORTANT: MUPs with the same mRID can exist for different clients in IEEE 2030.5
        _log.debug(
            f"MUP CREATION DEBUG: Checking for existing MUPs with mRID={getattr(mup, 'mRID', None)} for client {client_lfdi}"
        )
        if mup.mRID and client_lfdi:
            _log.debug(
                f"MUP CREATION DEBUG: MUP has mRID={mup.mRID}, checking {len(existing_mups)} existing MUPs for client {client_lfdi}"
            )
            for i, existing_mup in enumerate(existing_mups):
                existing_mrid = getattr(existing_mup, "mRID", None)
                existing_href = getattr(existing_mup, "href", None)
                _log.debug(f"MUP CREATION DEBUG: Existing MUP {i}: mRID={existing_mrid}, href={existing_href}")

                # Only consider it a duplicate if BOTH mRID matches AND it belongs to the same client
                if hasattr(existing_mup, "mRID") and existing_mup.mRID == mup.mRID:
                    # Check if this existing MUP belongs to the same client using metadata (thread-safe)
                    with _mup_metadata_lock:
                        metadata = _mup_metadata.get(existing_href, {})
                        existing_client_lfdi = metadata.get("createdByLFDI")
                    normalized_client_lfdi = _normalize_lfdi_for_cache(client_lfdi)

                    _log.debug(
                        f"MUP CREATION DEBUG: Checking ownership - existing client: {existing_client_lfdi}, current client: {normalized_client_lfdi}"
                    )

                    if existing_client_lfdi == normalized_client_lfdi:
                        _log.debug(
                            f"MUP CREATION DEBUG: Found existing MUP with matching mRID={mup.mRID} for SAME client {client_lfdi}, returning update result"
                        )
                        # Update existing for the same client
                        if not mup.href:
                            mup.href = existing_mup.href
                        result = ListAdapter.set_single(mup.href, mup)
                        if result.success:
                            return AdapterResult(success=True, data=mup, was_update=True, location=mup.href)
                        else:
                            return AdapterResult(success=False, error=result.error)
                    else:
                        _log.debug(
                            f"MUP CREATION DEBUG: Found existing MUP with same mRID={mup.mRID} but DIFFERENT client ({existing_client_lfdi} vs {normalized_client_lfdi}), continuing with new MUP creation"
                        )
        else:
            _log.debug("MUP CREATION DEBUG: MUP has no mRID or no client_lfdi, will create new MUP")

        # Generate device-specific href - deviceLFDI is required for IEEE 2030.5 compliance
        _log.debug(
            f"MUP deviceLFDI: {getattr(mup, 'deviceLFDI', 'None')}, existing href: {getattr(mup, 'href', 'None')}"
        )
        _log.debug(f"MUP deviceLFDI type: {type(getattr(mup, 'deviceLFDI', None))}")
        _log.debug(f"MUP deviceLFDI repr: {repr(getattr(mup, 'deviceLFDI', None))}")

        if not mup.deviceLFDI:
            _log.error("MirrorUsagePoint requires deviceLFDI for device association")
            # Per IEEE 2030.5 standard, return 400 error for missing required field
            return AdapterResult(
                success=False, error="deviceLFDI is required for MirrorUsagePoint creation", status_code=400
            )

        if not mup.href:
            # Ensure deviceLFDI is in bytes format for device lookup
            if isinstance(mup.deviceLFDI, bytes):
                lfdi_bytes = mup.deviceLFDI
            else:
                # Convert string/hex to bytes
                lfdi_str = str(mup.deviceLFDI)
                try:
                    # Try to decode hex string to bytes
                    lfdi_bytes = bytes.fromhex(lfdi_str)
                except ValueError:
                    # If not hex, encode as UTF-8
                    lfdi_bytes = lfdi_str.encode("utf-8")

            _log.debug(f"Looking up EndDevice with LFDI bytes: {lfdi_bytes} (hex: {lfdi_bytes.hex()})")

            # IMPORTANT: Use the authenticated client's LFDI for client_index lookup, not the MUP's deviceLFDI
            # This ensures each authenticated client gets their own MUP namespace
            lookup_lfdi = client_lfdi if client_lfdi else mup.deviceLFDI
            _log.debug(
                f"MUP CREATION DEBUG: Using authenticated client LFDI for client_index lookup: {lookup_lfdi} (original MUP deviceLFDI: {mup.deviceLFDI})"
            )

            # Find the device by authenticated client LFDI from pre-loaded cache (eliminates race conditions)
            device_info = _get_enddevice_from_cache(lookup_lfdi)
            device = device_info["device"] if device_info else None
            if device and device_info:
                # Use pre-calculated client_index from cache (eliminates race conditions)
                client_index = device_info["client_index"]
                _log.debug(
                    f"MUP CREATION DEBUG: Found client_index {client_index} for authenticated client LFDI {lookup_lfdi}, device href: {device.href if device else 'None'}"
                )
                if client_index:
                    # Use global lock ONLY for mirror_usage_point_index calculation to prevent conflicts
                    # while allowing concurrent MUP operations for different clients
                    _log.debug("MUP CREATION DEBUG: About to get GLOBAL lock for mirror_usage_point_index calculation")
                    global_index_lock = _get_href_generation_lock("__GLOBAL_MIRROR_USAGE_POINT_INDEX__")

                    # Then use per-client lock for the actual MUP creation (using authenticated client LFDI)
                    _log.debug(
                        f"MUP CREATION DEBUG: About to get per-client lock for authenticated client LFDI={lookup_lfdi}"
                    )
                    client_lock = _get_href_generation_lock(lookup_lfdi)

                    # Retry mechanism to handle potential race conditions
                    max_retries = 3
                    retry_count = 0

                    while retry_count < max_retries:
                        try:
                            # PHASE 1: Global lock to calculate mirror_usage_point_index safely
                            mirror_usage_point_index = None
                            mup_href = None

                            with global_index_lock:
                                _log.debug(
                                    "MUP CREATION DEBUG: Acquired GLOBAL lock for mirror_usage_point_index calculation"
                                )

                                # Re-read existing MUPs within the global lock to get latest state
                                try:
                                    existing_mups_fresh = ListAdapter.get_list(hrefs.DEFAULT_MUP_ROOT)
                                except Exception as e:
                                    _log.debug(f"No existing MUPs found in fresh read: {e}")
                                    existing_mups_fresh = []

                                # Count existing MUPs for this client to determine mirror_usage_point_index
                                client_mup_count = 0
                                # Normalize the new MUP's deviceLFDI for comparison
                                if isinstance(mup.deviceLFDI, bytes):
                                    new_mup_lfdi = mup.deviceLFDI.hex()
                                else:
                                    new_mup_lfdi = (
                                        str(mup.deviceLFDI).lower().replace("\\x", "").replace(" ", "").replace("-", "")
                                    )

                                for existing_mup in existing_mups_fresh:
                                    if hasattr(existing_mup, "deviceLFDI") and existing_mup.deviceLFDI:
                                        # Normalize the existing MUP's deviceLFDI for comparison
                                        if isinstance(existing_mup.deviceLFDI, bytes):
                                            existing_mup_lfdi = existing_mup.deviceLFDI.hex()
                                        else:
                                            existing_mup_lfdi = (
                                                str(existing_mup.deviceLFDI)
                                                .lower()
                                                .replace("\\x", "")
                                                .replace(" ", "")
                                                .replace("-", "")
                                            )

                                        if existing_mup_lfdi == new_mup_lfdi:
                                            client_mup_count += 1

                                mirror_usage_point_index = client_mup_count

                                # Generate href with pattern: /mup_{client_index}_{mirror_usage_point_index}
                                mup_href = f"/mup{hrefs.SEP}{client_index}{hrefs.SEP}{mirror_usage_point_index}"
                                _log.debug(
                                    f"Generated MUP href {mup_href} for client index {client_index}, mirror usage point {mirror_usage_point_index} (global lock, attempt {retry_count + 1})"
                                )

                            # PHASE 2: Per-client lock for the actual MUP creation, verification, and UPT creation
                            # Combine MUP and UPT creation in single atomic operation to prevent database lock cascades
                            with client_lock:
                                _log.debug(
                                    f"MUP CREATION DEBUG: Acquired per-client lock for MUP+UPT creation - authenticated client LFDI: {lookup_lfdi}"
                                )

                                # Set the href that was calculated under global lock
                                mup.href = mup_href

                                # Start atomic operation for both MUP and UPT creation
                                with atomic_operation():
                                    # Perform the database append within the per-client lock to ensure consistency
                                    # Use synchronous=True to ensure MUP is immediately available before responding to client
                                    _log.debug(f"About to append MUP with href: {mup.href} (synchronous write)")
                                    result = ListAdapter.append(hrefs.DEFAULT_MUP_ROOT, mup, synchronous=True)
                                    if not result.success:
                                        raise Exception(f"Database append failed: {result.error}")

                                    # Store metadata about which client created this MUP
                                    if client_lfdi:
                                        with _mup_metadata_lock:
                                            _mup_metadata[mup.href] = {
                                                "createdByLFDI": _normalize_lfdi_for_cache(client_lfdi),
                                                "createdAt": time.time(),
                                                "deviceLFDI": mup.deviceLFDI,  # Keep original deviceLFDI
                                            }
                                            _log.debug(f"Stored MUP metadata for {mup.href}: createdBy={client_lfdi}")

                                    _log.debug(
                                        f"Append result - success: {result.success}, location: {result.location}, data.href: {getattr(result.data, 'href', 'None')}"
                                    )

                                    # WRITE-THEN-READ CONSISTENCY CHECK
                                    # Verify the MUP can be successfully read by href (not by index)
                                    # This ensures write-read consistency and prevents 403 errors
                                    try:
                                        _log.debug(f"Performing verification read for MUP at href {mup.href}")

                                        # Find the MUP by href rather than by index to avoid index confusion
                                        verification_mups = ListAdapter.get_list(hrefs.DEFAULT_MUP_ROOT)
                                        verified_mup = None

                                        for test_mup in verification_mups:
                                            if hasattr(test_mup, "href") and test_mup.href == mup.href:
                                                verified_mup = test_mup
                                                break

                                        if verified_mup is None:
                                            raise Exception(
                                                f"Verification read failed: MUP not found with href {mup.href}"
                                            )

                                        # Verify the retrieved MUP actually belongs to this client
                                        if hasattr(verified_mup, "deviceLFDI") and verified_mup.deviceLFDI:
                                            if isinstance(verified_mup.deviceLFDI, bytes):
                                                verified_lfdi = verified_mup.deviceLFDI.hex()
                                            else:
                                                verified_lfdi = (
                                                    str(verified_mup.deviceLFDI)
                                                    .lower()
                                                    .replace("\\x", "")
                                                    .replace(" ", "")
                                                    .replace("-", "")
                                                )

                                            if verified_lfdi != new_mup_lfdi:
                                                raise Exception(
                                                    f"Verification read failed: Retrieved MUP belongs to different client (expected {new_mup_lfdi}, got {verified_lfdi})"
                                                )

                                        _log.debug(
                                            f"Verification read successful for MUP {mup.href} - write-read consistency confirmed"
                                        )

                                    except Exception as verification_error:
                                        _log.error(
                                            f"Write-read consistency verification failed for MUP {mup.href}: {verification_error}"
                                        )
                                        raise Exception(
                                            f"MUP write-read consistency check failed: {verification_error}"
                                        )

                                    # Create corresponding UsagePoint within the same atomic operation
                                    # This prevents database lock cascades from separate transactions
                                    try:
                                        # Get current UPT list size within the atomic operation for consistent index
                                        current_upt_size = len(ListAdapter.get_list(hrefs.DEFAULT_UPT_ROOT))

                                        usage_point = m.UsagePoint(
                                            mRID=mup.mRID,
                                            description=mup.description,
                                            href=f"{hrefs.DEFAULT_UPT_ROOT}_{current_upt_size}",
                                        )

                                        # Store the usage point within the same atomic operation (synchronous)
                                        up_result = ListAdapter.append(
                                            hrefs.DEFAULT_UPT_ROOT, usage_point, synchronous=True
                                        )
                                        if not up_result.success:
                                            _log.warning(
                                                f"Failed to create corresponding usage point for MirrorUsagePoint {result.location}: {up_result.error}"
                                            )
                                            # Continue anyway - the mirror usage point was created successfully
                                        else:
                                            _log.debug(
                                                f"Successfully created corresponding UsagePoint {usage_point.href} for MUP {mup.href}"
                                            )

                                    except Exception as e:
                                        _log.warning(
                                            f"Failed to create corresponding usage point for MirrorUsagePoint {result.location}: {e}"
                                        )
                                        # Continue anyway - the mirror usage point was created successfully

                                # Success - break out of retry loop
                                break

                        except Exception as e:
                            retry_count += 1
                            _log.warning(f"MUP creation attempt {retry_count} failed for client {mup.deviceLFDI}: {e}")
                            if retry_count >= max_retries:
                                return AdapterResult(
                                    success=False, error=f"Failed to create MUP after {max_retries} attempts: {e}"
                                )

                            # Brief wait before retry (exponential backoff)
                            wait_time = 0.01 * (2**retry_count)  # 20ms, 40ms, 80ms
                            time.sleep(wait_time)

                else:
                    _log.error(f"Client index not found for device: {device.href}")
                    # Per IEEE 2030.5 standard, return 400 error for invalid device configuration
                    return AdapterResult(
                        success=False, error=f"Client index not found for device: {device.href}", status_code=400
                    )
        else:
            _log.error(f"No device found for LFDI: {mup.deviceLFDI}")
            # Per IEEE 2030.5 standard, return 404 error when device cannot be found
            return AdapterResult(success=False, error=f"Device not found for LFDI: {mup.deviceLFDI}", status_code=404)

        # Verify result was set (should have been set in the per-client lock above)
        if "result" not in locals():
            _log.error(f"MUP creation failed - no result set. href: {getattr(mup, 'href', 'None')}")
            return AdapterResult(success=False, error="Failed to create MUP - internal error")

        if not result.success:
            return AdapterResult(success=False, error=result.error)

        # UsagePoint creation is now handled within the main atomic operation above
        # This eliminates the duplicate transaction that was causing database lock cascades

        return AdapterResult(
            success=True, data=result.data, was_update=False, location=mup.href if mup.href else result.location
        )

    except Exception as e:
        _log.error(f"Failed to create mirror usage point: {e}")
        return AdapterResult(success=False, error=str(e))


def create_or_update_meter_reading(
    mup_href: str, mmr_input: m.MirrorMeterReading | m.MirrorReadingSet, client_lfdi: str = None
) -> AdapterResult:
    """Thread-safe meter reading creation/update."""
    try:
        # Find the MirrorUsagePoint by href directly
        existing_mups = ListAdapter.get_list(hrefs.DEFAULT_MUP_ROOT)
        mup = None

        for existing_mup in existing_mups:
            if existing_mup.href == mup_href:
                mup = existing_mup
                break

        if mup is None:
            return AdapterResult(success=False, error=f"MirrorUsagePoint not found with href {mup_href}")

        # Find the MUP's position in the list for storage operations
        mup_list_index = None
        for i, existing_mup in enumerate(existing_mups):
            if existing_mup.href == mup_href:
                mup_list_index = i
                _log.debug(f"Found MUP at list index {mup_list_index} for href {mup_href}")
                break

        if mup_list_index is None:
            return AdapterResult(success=False, error=f"Could not determine storage index for MUP {mup_href}")

        # Create a parsed_href-like object for compatibility with existing code
        class MUPRef:
            def __init__(self, index):
                self.usage_point_index = index

        parsed_href = MUPRef(mup_list_index)

        # IEEE 2030.5 Rule 5: Only allow the client that created the mirror to update it
        if client_lfdi and hasattr(mup, "deviceLFDI") and mup.deviceLFDI:
            # Handle LFDI comparison - both could be bytes or strings
            try:
                if isinstance(mup.deviceLFDI, bytes):
                    # Try to decode as UTF-8, fallback to hex representation
                    try:
                        mup_lfdi = mup.deviceLFDI.decode("utf-8")
                    except UnicodeDecodeError:
                        # If it's not valid UTF-8, convert to hex string
                        mup_lfdi = mup.deviceLFDI.hex()
                else:
                    mup_lfdi = str(mup.deviceLFDI)

                # Ensure client LFDI is a string
                client_lfdi_str = str(client_lfdi)

                _log.debug(f"Authorization check: MUP LFDI='{mup_lfdi}', Client LFDI='{client_lfdi_str}'")

                if mup_lfdi != client_lfdi_str:
                    return AdapterResult(
                        success=False, error="Only the client that created this mirror may update it", status_code=403
                    )
            except Exception as e:
                _log.error(f"Error in LFDI comparison: {e}")
                return AdapterResult(success=False, error="Authorization check failed", status_code=403)

        # Set the href for the meter reading if not already set
        if not mmr_input.href:
            # Generate an href for the meter reading within the MUP using SEP separator
            if isinstance(mmr_input, m.MirrorMeterReading):
                mmr_input.href = f"{mup_href}{hrefs.SEP}mr{hrefs.SEP}{len(mup.MirrorMeterReading)}"
            elif isinstance(mmr_input, m.MirrorReadingSet):
                mmr_input.href = f"{mup_href}{hrefs.SEP}rs{hrefs.SEP}{len(getattr(mup, 'MirrorReadingSet', []))}"

        # Add the reading to the MirrorUsagePoint
        was_update = False
        if isinstance(mmr_input, m.MirrorMeterReading):
            # Check if it already exists (by mRID)
            existing_idx = None
            for i, existing_mmr in enumerate(mup.MirrorMeterReading):
                if existing_mmr.mRID == mmr_input.mRID:
                    existing_idx = i
                    was_update = True
                    break

            if was_update:
                # Update existing reading
                mup.MirrorMeterReading[existing_idx] = mmr_input
            else:
                # New reading - validate ReadingType requirement (IEEE 2030.5 Rule 8c)
                if not hasattr(mmr_input, "ReadingType") or mmr_input.ReadingType is None:
                    return AdapterResult(
                        success=False, error="ReadingType is required for new MirrorMeterReading", status_code=400
                    )
                # Add new reading
                mup.MirrorMeterReading.append(mmr_input)

        elif isinstance(mmr_input, m.MirrorReadingSet):
            # Handle MirrorReadingSet similarly
            if not hasattr(mup, "MirrorReadingSet"):
                mup.MirrorReadingSet = []

            # Check if it already exists (by mRID)
            existing_idx = None
            for i, existing_mrs in enumerate(mup.MirrorReadingSet):
                if existing_mrs.mRID == mmr_input.mRID:
                    existing_idx = i
                    was_update = True
                    break

            if was_update:
                # Update existing reading set
                mup.MirrorReadingSet[existing_idx] = mmr_input
            else:
                # Add new reading set
                mup.MirrorReadingSet.append(mmr_input)

        # Update the MirrorUsagePoint in storage
        result = ListAdapter.put(hrefs.DEFAULT_MUP_ROOT, parsed_href.usage_point_index, mup)
        if not result.success:
            return AdapterResult(success=False, error=result.error)

        # Also create corresponding reading in the related UsagePoint
        try:
            # Get the corresponding UsagePoint (same index)
            up = ListAdapter.get(hrefs.DEFAULT_UPT_ROOT, parsed_href.usage_point_index)
            if up is not None:
                if isinstance(mmr_input, m.MirrorMeterReading):
                    # Create corresponding MeterReading for the UsagePoint
                    meter_reading = m.MeterReading(
                        mRID=mmr_input.mRID,
                        href=f"{hrefs.DEFAULT_UPT_ROOT}{hrefs.SEP}{parsed_href.usage_point_index}{hrefs.SEP}mr{hrefs.SEP}{len(getattr(up, 'MeterReading', []))}",
                    )

                    if not hasattr(up, "MeterReading"):
                        up.MeterReading = []

                    # Check if it already exists (by mRID) and update/add
                    existing_idx = None
                    for i, existing_mr in enumerate(up.MeterReading):
                        if existing_mr.mRID == meter_reading.mRID:
                            existing_idx = i
                            break

                    if existing_idx is not None:
                        up.MeterReading[existing_idx] = meter_reading
                    else:
                        up.MeterReading.append(meter_reading)

                    # Update the UsagePoint in storage
                    up_result = ListAdapter.put(hrefs.DEFAULT_UPT_ROOT, parsed_href.usage_point_index, up)
                    if not up_result.success:
                        _log.warning(f"Failed to update corresponding usage point reading: {up_result.error}")
        except Exception as e:
            _log.warning(f"Failed to sync reading to corresponding usage point: {e}")

        return AdapterResult(success=True, data=mmr_input, was_update=was_update, location=mmr_input.href)

    except Exception as e:
        _log.error(f"Failed to create/update meter reading: {e}")
        return AdapterResult(success=False, error=str(e))


def create_or_update_usage_point_reading(up_href: str, reading_input: m.MeterReading | m.ReadingSet) -> AdapterResult:
    """Thread-safe usage point reading creation/update."""
    try:
        # Parse the UP href to get the usage point index
        parsed_href = hrefs.ParsedUsagePointHref(up_href)
        if not parsed_href.has_usage_point_index():
            return AdapterResult(success=False, error="Invalid UP href - no usage point index")

        # Get the existing UsagePoint
        up = ListAdapter.get(hrefs.DEFAULT_UPT_ROOT, parsed_href.usage_point_index)
        if up is None:
            return AdapterResult(success=False, error=f"UsagePoint not found at index {parsed_href.usage_point_index}")

        # Set the href for the meter reading if not already set
        if not reading_input.href:
            # Generate an href for the meter reading within the UP using SEP separator
            if isinstance(reading_input, m.MeterReading):
                if not hasattr(up, "MeterReading"):
                    up.MeterReading = []
                reading_input.href = f"{up_href}{hrefs.SEP}mr{hrefs.SEP}{len(up.MeterReading)}"
            elif isinstance(reading_input, m.ReadingSet):
                if not hasattr(up, "ReadingSet"):
                    up.ReadingSet = []
                reading_input.href = f"{up_href}{hrefs.SEP}rs{hrefs.SEP}{len(up.ReadingSet)}"

        # Add the reading to the UsagePoint
        was_update = False
        if isinstance(reading_input, m.MeterReading):
            if not hasattr(up, "MeterReading"):
                up.MeterReading = []

            # Check if it already exists (by mRID)
            existing_idx = None
            for i, existing_mr in enumerate(up.MeterReading):
                if existing_mr.mRID == reading_input.mRID:
                    existing_idx = i
                    was_update = True
                    break

            if was_update:
                # Update existing reading
                up.MeterReading[existing_idx] = reading_input
            else:
                # Add new reading
                up.MeterReading.append(reading_input)

        elif isinstance(reading_input, m.ReadingSet):
            if not hasattr(up, "ReadingSet"):
                up.ReadingSet = []

            # Check if it already exists (by mRID)
            existing_idx = None
            for i, existing_rs in enumerate(up.ReadingSet):
                if existing_rs.mRID == reading_input.mRID:
                    existing_idx = i
                    was_update = True
                    break

            if was_update:
                # Update existing reading set
                up.ReadingSet[existing_idx] = reading_input
            else:
                # Add new reading set
                up.ReadingSet.append(reading_input)

        # Update the UsagePoint in storage
        result = ListAdapter.put(hrefs.DEFAULT_UPT_ROOT, parsed_href.usage_point_index, up)
        if result.success:
            return AdapterResult(success=True, data=reading_input, was_update=was_update, location=reading_input.href)
        else:
            return AdapterResult(success=False, error=result.error)

    except Exception as e:
        _log.error(f"Failed to create/update usage point reading: {e}")
        return AdapterResult(success=False, error=str(e))


def create_device_capability(
    end_device_index: int, device_cfg: DeviceConfiguration, config: ServerConfiguration = None
) -> m.DeviceCapability:
    """Thread-safe device capability creation."""
    try:
        dcap_href = hrefs.DeviceCapabilityHref(end_device_index)
        device_capability = m.DeviceCapability()
        device_capability = dcap_href.fill_hrefs(device_capability)

        # Set the poll rate from config if available
        if config:
            device_capability.pollRate = config.poll_rate
        device_capability.MirrorUsagePointListLink = m.MirrorUsagePointListLink(href=hrefs.DEFAULT_MUP_ROOT, all=0)
        device_capability.TimeLink = m.TimeLink(href=hrefs.DEFAULT_TIME_ROOT)
        device_capability.UsagePointListLink = m.UsagePointListLink(href=hrefs.DEFAULT_UPT_ROOT, all=0)
        # Thread-safe adapter operations
        result = DeviceCapabilityAdapter.append(hrefs.DEFAULT_DCAP_ROOT, device_capability)
        if not result.success:
            raise Exception(f"Failed to add device capability: {result.error}")
        return result.data
    except Exception as e:
        _log.error(f"Failed to create device capability for device {end_device_index}: {e}")
        raise


def add_enddevice(device: m.EndDevice) -> m.EndDevice:
    """Thread-safe enddevice addition with all related resources."""
    try:
        # Add the device atomically
        device = EndDeviceAdapter.add(device)
        ed_href = hrefs.EndDeviceHref(edev_href=device.href)
        # Fill hrefs
        ed_href.fill_hrefs(device)
        # Create related resources atomically
        with atomic_operation():
            # Configuration
            config = m.Configuration(href=device.ConfigurationLink.href)
            result = ListAdapter.set_single(uri=device.ConfigurationLink.href, obj=config)
            # Device Information
            device_info = m.DeviceInformation(href=device.DeviceInformationLink.href)
            ListAdapter.set_single(uri=device.DeviceInformationLink.href, obj=device_info)
            # Device Status
            device_status = m.DeviceStatus(href=device.DeviceStatusLink.href)
            ListAdapter.set_single(uri=device.DeviceStatusLink.href, obj=device_status)
            # Power Status
            power_status = m.PowerStatus(href=device.PowerStatusLink.href)
            ListAdapter.set_single(uri=device.PowerStatusLink.href, obj=power_status)
        # Initialize lists
        device.MirrorUsagePointListLink = m.MirrorUsagePointListLink(href=hrefs.DEFAULT_MUP_ROOT, all=0)
        device.UsagePointListLink = m.UsagePointListLink(href=hrefs.DEFAULT_UPT_ROOT, all=0)
        # Initialize list URIs thread-safely
        ListAdapter.initialize_uri(hrefs.DEFAULT_MUP_ROOT, m.MirrorUsagePoint)
        ListAdapter.initialize_uri(hrefs.DEFAULT_UPT_ROOT, m.UsagePoint)
        ListAdapter.initialize_uri(ed_href.der_list, m.DER)
        ListAdapter.initialize_uri(ed_href.function_set_assignments, m.FunctionSetAssignments)
        return device
    except Exception as e:
        _log.error(f"Failed to add end device: {e}")
        raise


# Thread-safe event handling
_event_processing_lock = threading.RLock()


def update_active_der_event_started(event: m.Event):
    """Thread-safe event processing for DER control events."""
    with _event_processing_lock:
        try:
            assert type(event) == m.DERControl
            href_parser = hrefs.HrefEventParser(event.href)
            program = ListAdapter.get(hrefs.DEFAULT_DERP_ROOT, href_parser.program_index)
            # Get control list thread-safely
            control_list = ListAdapter.get_resource_list(program.DERControlListLink.href)
            control = next(filter(lambda x: x.mRID == event.mRID, control_list.DERControl))
            control.EventStatus = event.EventStatus
            assert control.EventStatus.currentStatus == 1
            # Atomic update of multiple resources
            with atomic_operation():
                # Add to active controls
                ListAdapter.append(program.ActiveDERControlListLink.href, control)
                # Update the control in the main list
                control_index = next(i for i, c in enumerate(control_list.DERControl) if c.mRID == event.mRID)
                ListAdapter.put(program.DERControlListLink.href, control_index, control)
            _log.info(f"Started DER control event {event.mRID}")
        except Exception as e:
            _log.error(f"Failed to process DER event start: {e}")
            raise


def update_active_der_event_ended(event: m.Event):
    """Thread-safe event processing for ending DER control events."""
    with _event_processing_lock:
        try:
            assert type(event) == m.DERControl
            href_parser = hrefs.HrefEventParser(event.href)
            program = ListAdapter.get(hrefs.DEFAULT_DERP_ROOT, href_parser.program_index)
            control_list = ListAdapter.get_resource_list(program.DERControlListLink.href)
            control = next(filter(lambda x: x.mRID == event.mRID, control_list.DERControl))
            control.EventStatus = event.EventStatus
            # Atomic removal from active list
            with atomic_operation():
                # Update control in main list
                control_index = next(i for i, c in enumerate(control_list.DERControl) if c.mRID == event.mRID)
                ListAdapter.put(program.DERControlListLink.href, control_index, control)
                # Remove from active list if not active
                if event.EventStatus.currentStatus != 1:
                    active_list = ListAdapter.get_list(program.ActiveDERControlListLink.href)
                    updated_active = [c for c in active_list if c.mRID != event.mRID]
                    # Replace entire active list
                    ListAdapter.set_list(program.ActiveDERControlListLink.href, updated_active)
            _log.info(f"Ended DER control event {event.mRID}")
        except Exception as e:
            _log.error(f"Failed to process DER event end: {e}")
            raise


# Add missing method that might be referenced
def clear_all_adapters():
    """Clear all adapters data."""
    with atomic_operation():
        try:
            _log.info("Clearing all adapter data")
            get_db().clear_all()
            initialize_adapters()  # Re-initialize adapters
        except Exception as e:
            _log.error(f"Failed to clear adapters: {e}")
            raise


def get_global_mrids():
    """Get the global MRIDs instance from base module."""
    from .base import get_global_mrids_instance

    return get_global_mrids_instance()


def initialize_2030_5(config: ServerConfiguration, tlsrepo: TLSRepository):
    """Thread-safe version of the 2030.5 server initialization."""
    _log.debug("Initializing 2030.5 with thread safety")
    # Clear storage if requested (thread-safe)
    if config.cleanse_storage:
        with atomic_operation():
            get_db().clear_all()
    # Initialize adapters
    initialize_adapters()
    # Initialize programs thread-safely
    with atomic_operation():
        ListAdapter.initialize_uri(hrefs.DEFAULT_DERP_ROOT, m.DERProgram)
        # Add default program if configured
        if config.default_program:
            index = ListAdapter.get_list_size(hrefs.DEFAULT_DERP_ROOT)
            derp = config.default_program
            if not derp.mRID:
                derp.mRID = get_global_mrids().new_mrid()
            result = ListAdapter.append(hrefs.DEFAULT_DERP_ROOT, derp)
            if not result.success:
                raise Exception(f"Failed to add default program: {result.error}")
            program_hrefs = hrefs.DERProgramHref(index)
            derp.href = program_hrefs._root
            derp.ActiveDERControlListLink = m.ActiveDERControlListLink(program_hrefs.active_control_href)
            derp.DefaultDERControlLink = m.DefaultDERControlLink(program_hrefs.default_control_href)
            derp.DERControlListLink = m.DERControlListLink(program_hrefs.der_control_list_href)
            # Add default control if configured
            if config.default_der_control:
                dderc = config.default_der_control
                dderc.mRID = get_global_mrids().new_mrid()
                dderc.href = derp.DefaultDERControlLink.href
                ListAdapter.set_single(uri=derp.DefaultDERControlLink.href, obj=dderc)
            # Initialize sub-lists
            ListAdapter.initialize_uri(derp.DERControlListLink.href, m.DERControl)
    # Add configured programs thread-safely
    for program_cfg in config.programs:
        try:
            with atomic_operation():
                program_hrefs = hrefs.DERProgramHref(ListAdapter.get_list_size(hrefs.DEFAULT_DERP_ROOT))
                default_der_control = program_cfg.pop("DefaultDERControl", None)
                program = m.DERProgram(**program_cfg)
                if not program.mRID:
                    program.mRID = get_global_mrids().new_mrid()
                program = program_hrefs.fill_hrefs(program)
                result = ListAdapter.append(hrefs.DEFAULT_DERP_ROOT, program)
                if not result.success:
                    raise Exception(f"Failed to add program: {result.error}")
                # Handle default control...
                if default_der_control:
                    dderc = m.DefaultDERControl(href=program.DefaultDERControlLink.href, **default_der_control)
                    if not dderc.mRID:
                        dderc.mRID = get_global_mrids().new_mrid()
                    ListAdapter.set_single(uri=program.DefaultDERControlLink.href, obj=dderc)
                # Initialize lists
                ListAdapter.initialize_uri(program.DERControlListLink.href, m.DERControl)
                ListAdapter.set_single(uri=program.ActiveDERControlListLink.href, obj=m.DERControlList(DERControl=[]))
        except Exception as e:
            _log.error(f"Failed to initialize program {program_cfg.get('description', 'unknown')}: {e}")
            raise
    # Add curves thread-safely
    ListAdapter.initialize_uri(hrefs.DEFAULT_CURVE_ROOT, m.DERCurve)
    for index, curve_cfg in enumerate(config.curves):
        try:
            curve = m.DERCurve(href=hrefs.SEP.join([hrefs.DEFAULT_CURVE_ROOT, str(index)]), **curve_cfg)
            if not curve.mRID:
                curve.mRID = get_global_mrids().new_mrid()
            result = ListAdapter.append(hrefs.DEFAULT_CURVE_ROOT, curve)
            if not result.success:
                raise Exception(f"Failed to add curve: {result.error}")
        except Exception as e:
            _log.error(f"Failed to add curve {index}: {e}")
            raise
    # Add devices thread-safely
    der_global_count = 0
    for index, cfg_device in enumerate(config.devices):
        try:
            device_capability = create_device_capability(index, cfg_device, config)
            ed_href = hrefs.EndDeviceHref(index)
            # Check if device already exists
            existing_device = EndDeviceAdapter.fetch_by_href(str(ed_href))
            if existing_device is not None:
                _log.warning(f"End device {cfg_device.id} already exists. Updating...")
                # Thread-safe update
                existing_device.lFDI = tlsrepo.lfdi(cfg_device.id)
                existing_device.sFDI = tlsrepo.sfdi(cfg_device.id)
                existing_device.postRate = cfg_device.post_rate
                result = EndDeviceAdapter.put(index, existing_device)
                if not result.success:
                    raise Exception(f"Failed to update device: {result.error}")
            else:
                _log.debug(f"Adding end device {cfg_device.id} to server")
                end_device = m.EndDevice(
                    lFDI=tlsrepo.lfdi(cfg_device.id),
                    sFDI=tlsrepo.sfdi(cfg_device.id),
                    postRate=cfg_device.post_rate,
                    enabled=True,
                    changedTime=TimeAdapter.current_tick,
                )
                end_device = add_enddevice(end_device)
                get_global_mrids().add_item_with_mrid(cfg_device.id, end_device)

                # Also add the EndDevice indexed by certificate CN for GridAPPS-D compatibility
                # The certificate CN is typically derived from the device ID
                try:
                    # Use the tlsrepo parameter instead of Flask.g to avoid context issues
                    # Get the certificate subject (CN) for this device
                    cn = tlsrepo.get_common_name(cfg_device.id)
                    if cn and hasattr(cn, "CN"):
                        cert_cn = cn.CN  # Extract the CN field
                        # Also index by certificate CN
                        get_global_mrids().add_item_with_mrid(cert_cn, end_device)
                        _log.debug(f"Added EndDevice mapping: CN '{cert_cn}' -> device_id '{cfg_device.id}'")
                except Exception as e:
                    _log.warning(f"Could not add certificate CN mapping for device {cfg_device.id}: {e}")
                    # Continue without CN mapping - direct device ID lookup will still work
                # Add registration
                reg = m.Registration(
                    href=end_device.RegistrationLink.href,
                    pIN=cfg_device.pin,
                    pollRate=cfg_device.poll_rate,
                    dateTimeRegistered=TimeAdapter.current_tick,
                )
                ListAdapter.set_single(uri=reg.href, obj=reg)
                # Handle DERs and FSAs...
                if cfg_device.ders:
                    for der in cfg_device.ders:
                        der_href = hrefs.DERHref(hrefs.SEP.join([hrefs.DEFAULT_DER_ROOT, str(der_global_count)]))
                        der_global_count += 1
                        der_obj = m.DER(
                            href=der_href.root,
                            DERStatusLink=m.DERStatusLink(der_href.der_status),
                            DERSettingsLink=m.DERSettingsLink(der_href.der_settings),
                            DERCapabilityLink=m.DERCapabilityLink(der_href.der_capability),
                            DERAvailabilityLink=m.DERAvailabilityLink(der_href.der_availability),
                        )
                        # Add DER thread-safely
                        result = ListAdapter.append(ed_href.der_list, der_obj)
                        if not result.success:
                            raise Exception(f"Failed to add DER: {result.error}")
        except Exception as e:
            _log.error(f"Failed to initialize device {cfg_device.id}: {e}")
            raise

    # Initialize EndDevice cache for fast lookups (eliminates race conditions)
    # Must be done AFTER all devices are created
    _initialize_enddevice_cache()

    _log.info("Thread-safe 2030.5 initialization completed")


def get_mup_metadata(mup_href: str) -> dict | None:
    """Get metadata for a MirrorUsagePoint."""
    with _mup_metadata_lock:
        return _mup_metadata.get(mup_href)


def get_mups_for_client(client_lfdi: str) -> list[m.MirrorUsagePoint]:
    """Get all MirrorUsagePoints created by or belonging to a specific client."""
    normalized_client_lfdi = _normalize_lfdi_for_cache(client_lfdi)
    result = []

    try:
        all_mups = ListAdapter.get_list(hrefs.DEFAULT_MUP_ROOT)

        with _mup_metadata_lock:
            for mup in all_mups:
                # Check if this MUP was created by the client
                metadata = _mup_metadata.get(mup.href)
                if metadata and metadata.get("createdByLFDI") == normalized_client_lfdi:
                    result.append(mup)
                    continue

                # Also check deviceLFDI for backward compatibility
                if hasattr(mup, "deviceLFDI") and mup.deviceLFDI:
                    mup_lfdi = _normalize_lfdi_for_cache(mup.deviceLFDI)
                    if mup_lfdi == normalized_client_lfdi:
                        result.append(mup)
    except KeyError:
        pass

    return result
