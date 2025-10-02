"""
Thread-safe URL management system for IEEE 2030.5 server.
Provides consistent URL generation and parsing for all server resources.
"""

from __future__ import annotations

import functools
import threading
from dataclasses import dataclass
from enum import Enum
from typing import Any, NamedTuple

import ieee_2030_5.models as m

# Thread-safe caching
_cache_lock = threading.RLock()

# Sentinel value for no index
NO_INDEX = -1

# Path separator
SEP = "_"


# Path component constants - centralized in one place
class PathComponent:
    """Centralized path components for IEEE 2030.5 URLs."""

    EDEV = "edev"
    DCAP = "dcap"
    UPT = "upt"
    UTP = "upt"  # Add this alias for backward compatibility
    MUP = "mup"
    DRP = "drp"
    SDEV = "sdev"
    MSG = "msg"
    DER = "der"
    CURVE = "dc"
    RSPS = "rsps"
    LOG = "log"
    DERC = "derc"
    DDERC = "dderc"
    DERCA = "derca"
    DERCURVE = "dc"
    FSA = "fsa"
    TIME = "tm"
    DER_PROGRAM = "derp"
    DER_AVAILABILITY = "dera"
    DER_STATUS = "ders"
    DER_CAPABILITY = "dercap"
    DER_CONTROL_ACTIVE = "derca"
    DER_SETTINGS = "derg"
    END_DEVICE_REGISTRATION = "rg"
    END_DEVICE_STATUS = "dstat"
    END_DEVICE_FSA = FSA
    END_DEVICE_POWER_STATUS = "ps"
    END_DEVICE_LOG_EVENT_LIST = "lel"
    END_DEVICE_INFORMATION = "di"
    CONFIGURATION = "cfg"


# Root URLs - constructed from components for consistency
class RootURLs:
    """Root URLs for IEEE 2030.5 resources."""

    DEFAULT_TIME_ROOT = f"/{PathComponent.TIME}"
    DEFAULT_DCAP_ROOT = f"/{PathComponent.DCAP}"
    DEFAULT_EDEV_ROOT = f"/{PathComponent.EDEV}"
    DEFAULT_UPT_ROOT = f"/{PathComponent.UPT}"
    DEFAULT_MUP_ROOT = f"/{PathComponent.MUP}"
    DEFAULT_DRP_ROOT = f"/{PathComponent.DRP}"
    DEFAULT_SELF_ROOT = f"/{PathComponent.SDEV}"
    DEFAULT_MESSAGE_ROOT = f"/{PathComponent.MSG}"
    DEFAULT_DER_ROOT = f"/{PathComponent.DER}"
    DEFAULT_CURVE_ROOT = f"/{PathComponent.CURVE}"
    DEFAULT_RSPS_ROOT = f"/{PathComponent.RSPS}"
    DEFAULT_LOG_EVENT_ROOT = f"/{PathComponent.LOG}"
    DEFAULT_FSA_ROOT = f"/{PathComponent.FSA}"
    DEFAULT_DERP_ROOT = f"/{PathComponent.DER_PROGRAM}"
    DEFAULT_DDERC_ROOT = f"/{PathComponent.DDERC}"
    DEFAULT_CONTROL_ROOT = f"/{PathComponent.DERC}"


# Resource types
class ResourceType(Enum):
    """Enumeration of IEEE 2030.5 resource types."""

    END_DEVICE = "EndDevice"
    DER = "DER"
    DER_PROGRAM = "DERProgram"
    DER_CONTROL = "DERControl"
    DER_CURVE = "DERCurve"
    FUNCTION_SET_ASSIGNMENTS = "FunctionSetAssignments"
    USAGE_POINT = "UsagePoint"
    MIRROR_USAGE_POINT = "MirrorUsagePoint"
    DEVICE_CAPABILITY = "DeviceCapability"
    TIME = "Time"
    SELF_DEVICE = "SelfDevice"
    CONFIGURATION = "Configuration"
    DEVICE_INFORMATION = "DeviceInformation"
    DEVICE_STATUS = "DeviceStatus"
    POWER_STATUS = "PowerStatus"
    REGISTRATION = "Registration"
    LOG_EVENT = "LogEvent"
    DEFAULT_DER_CONTROL = "DefaultDERControl"
    ACTIVE_DER_CONTROL = "ActiveDERControl"


# Sub-resource types
class DERSubType(Enum):
    """Sub-resource types for DER resources."""

    CAPABILITY = PathComponent.DER_CAPABILITY
    SETTINGS = PathComponent.DER_SETTINGS
    STATUS = PathComponent.DER_STATUS
    AVAILABILITY = PathComponent.DER_AVAILABILITY
    CURRENT_PROGRAM = PathComponent.DER_PROGRAM
    NONE = None


class FSASubType(Enum):
    """Sub-resource types for FSA resources."""

    DER_PROGRAM = "derp"
    NONE = None


class EDevSubType(Enum):
    """Sub-resource types for EndDevice resources."""

    NONE = None
    REGISTRATION = PathComponent.END_DEVICE_REGISTRATION
    DEVICE_STATUS = PathComponent.END_DEVICE_STATUS
    POWER_STATUS = PathComponent.END_DEVICE_POWER_STATUS
    FUNCTION_SET_ASSIGNMENTS = PathComponent.END_DEVICE_FSA
    LOG_EVENT_LIST = PathComponent.END_DEVICE_LOG_EVENT_LIST
    DEVICE_INFORMATION = PathComponent.END_DEVICE_INFORMATION
    DER = PathComponent.DER
    CONFIGURATION = PathComponent.CONFIGURATION


class DERProgramSubType(Enum):
    """Sub-resource types for DERProgram resources."""

    NONE = 0
    ACTIVE_DER_CONTROL_LIST = 1
    DEFAULT_DER_CONTROL = 2
    DER_CONTROL_LIST = 3
    DER_CURVE_LIST = 4
    DER_CONTROL_REPLY_TO = 5
    DER_CONTROL = 6


# Thread-safe cached function decorator
def thread_safe_cached(func):
    """Thread-safe version of functools.lru_cache."""
    cached_func = functools.lru_cache(maxsize=128)(func)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with _cache_lock:
            return cached_func(*args, **kwargs)

    # Add cache_clear method
    wrapper.cache_clear = cached_func.cache_clear
    wrapper.cache_info = cached_func.cache_info

    return wrapper


# Base parser class
class HrefParser:
    """Base class for parsing IEEE 2030.5 hrefs."""

    def __init__(self, href: str):
        """Initialize with an href string."""
        self.href = href
        self._split = href.split(SEP)

    def has_index(self) -> bool:
        """Check if there is an index on the primary type."""
        return len(self._split) > 1

    def count(self) -> int:
        """Return the number of parts in the href."""
        return len(self._split)

    def join(self, how_many: int) -> str:
        """Join the first `how_many` parts of the href."""
        return SEP.join([str(x) for x in self._split[:how_many]])

    def startswith(self, value: str) -> bool:
        """Check if the href starts with a specific value."""
        return self.href.startswith(value)

    def at(self, index: int) -> str | int | None:
        """Get the component at the specified index."""
        try:
            if index >= len(self._split):
                return None

            try:
                intvalue = int(self._split[index])
                return intvalue
            except ValueError:
                return self._split[index]
        except IndexError:
            return None


class HrefEventParser(HrefParser):
    """Parser for event hrefs."""

    @property
    def program_index(self) -> int:
        """Get the program index."""
        return int(self.at(1))

    @property
    def event_index(self) -> int:
        """Get the event index."""
        return int(self._split[-1])

    @property
    def events_href(self) -> str:
        """Get the events href."""
        return SEP.join(self._split[:-1])


# URL Registry
class URLRegistry:
    """Registry for IEEE 2030.5 URLs with thread safety."""

    _instance = None
    _lock = threading.RLock()

    @classmethod
    def get_instance(cls) -> URLRegistry:
        """Get the singleton instance of the URL registry."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def __init__(self):
        """Initialize the registry."""
        self._urls: dict[str, str] = {}
        self._lock = threading.RLock()

    def register(self, key: str, url: str) -> None:
        """Register a URL."""
        with self._lock:
            self._urls[key] = url

    def get(self, key: str) -> str | None:
        """Get a URL by key."""
        with self._lock:
            return self._urls.get(key)

    def clear(self) -> None:
        """Clear all registered URLs."""
        with self._lock:
            self._urls.clear()


# URL Builder class
class URLBuilder:
    """Builder for IEEE 2030.5 URLs with thread safety."""

    _instance = None
    _lock = threading.RLock()

    @classmethod
    def get_instance(cls) -> URLBuilder:
        """Get the singleton instance of the URL builder."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def __init__(self):
        """Initialize the URL builder."""
        self.registry = URLRegistry.get_instance()

    def join_parts(self, *parts: Any) -> str:
        """Join URL parts with the separator."""
        valid_parts = [str(p) for p in parts if p is not None and p != NO_INDEX]
        result = valid_parts[0]
        if len(valid_parts) > 1:
            result += SEP.join([""] + valid_parts[1:])
        return result

    @thread_safe_cached
    def get_server_config_href(self) -> str:
        """Get the server configuration URL."""
        url = "/server/cfg"
        self.registry.register("server_config", url)
        return url

    @thread_safe_cached
    def get_enddevice_list_href(self) -> str:
        """Get the end device list URL."""
        return RootURLs.DEFAULT_EDEV_ROOT

    @thread_safe_cached
    def curve_href(self, index: int = NO_INDEX) -> str:
        """Get a curve URL."""
        if index == NO_INDEX:
            return RootURLs.DEFAULT_CURVE_ROOT
        return SEP.join([RootURLs.DEFAULT_CURVE_ROOT, str(index)])

    @thread_safe_cached
    def fsa_href(self, index: int = NO_INDEX, edev_index: int = NO_INDEX) -> str:
        """Get a FSA URL."""
        if index == NO_INDEX and edev_index == NO_INDEX:
            return RootURLs.DEFAULT_FSA_ROOT
        elif index != NO_INDEX and edev_index == NO_INDEX:
            return SEP.join([RootURLs.DEFAULT_FSA_ROOT, str(index)])
        elif index == NO_INDEX and edev_index != NO_INDEX:
            return SEP.join([RootURLs.DEFAULT_EDEV_ROOT, str(edev_index), PathComponent.FSA])
        else:
            return SEP.join([RootURLs.DEFAULT_EDEV_ROOT, str(edev_index), PathComponent.FSA, str(index)])

    @thread_safe_cached
    def derp_href(self, edev_index: int, fsa_index: int) -> str:
        """Get a DER program URL for an end device FSA."""
        return SEP.join(
            [RootURLs.DEFAULT_EDEV_ROOT, str(edev_index), PathComponent.FSA, str(fsa_index), PathComponent.DER_PROGRAM]
        )

    @thread_safe_cached
    def der_href(self, index: int = NO_INDEX, fsa_index: int = NO_INDEX, edev_index: int = NO_INDEX) -> str:
        """Get a DER URL."""
        if index == NO_INDEX and fsa_index == NO_INDEX and edev_index == NO_INDEX:
            return RootURLs.DEFAULT_DER_ROOT
        elif index != NO_INDEX and fsa_index == NO_INDEX and edev_index == NO_INDEX:
            return SEP.join([RootURLs.DEFAULT_DER_ROOT, str(index)])
        elif index == NO_INDEX and fsa_index != NO_INDEX and edev_index == NO_INDEX:
            return SEP.join([RootURLs.DEFAULT_FSA_ROOT, str(fsa_index), PathComponent.DER_PROGRAM])
        elif edev_index != NO_INDEX and fsa_index == NO_INDEX and index == NO_INDEX:
            return SEP.join([RootURLs.DEFAULT_EDEV_ROOT, str(edev_index), PathComponent.FSA])
        elif edev_index != NO_INDEX and fsa_index != NO_INDEX and index == NO_INDEX:
            return SEP.join([RootURLs.DEFAULT_EDEV_ROOT, str(edev_index), PathComponent.FSA, str(fsa_index)])
        else:
            raise ValueError(f"index={index}, fsa_index={fsa_index}, edev_index={edev_index}")

    @thread_safe_cached
    def edev_der_href(self, edev_index: int, der_index: int = NO_INDEX) -> str:
        """Get a DER URL for an end device."""
        if der_index == NO_INDEX:
            return SEP.join([RootURLs.DEFAULT_EDEV_ROOT, str(edev_index), PathComponent.DER])
        return SEP.join([RootURLs.DEFAULT_EDEV_ROOT, str(edev_index), PathComponent.DER, str(der_index)])

    @thread_safe_cached
    def der_sub_href(self, edev_index: int, index: int = NO_INDEX, subtype: DERSubType = None) -> str:
        """Get a DER sub-resource URL."""
        if subtype is None and index == NO_INDEX:
            return SEP.join([RootURLs.DEFAULT_EDEV_ROOT, str(edev_index), PathComponent.DER])
        elif subtype is None:
            return SEP.join([RootURLs.DEFAULT_EDEV_ROOT, str(edev_index), PathComponent.DER, str(index)])
        else:
            return SEP.join([RootURLs.DEFAULT_EDEV_ROOT, str(edev_index), PathComponent.DER, str(index), subtype.value])

    @thread_safe_cached
    def mirror_usage_point_href(self, mirror_usage_point_index: int = NO_INDEX, device_id: str = None) -> str:
        """Get a mirror usage point URL.

        Args:
            mirror_usage_point_index: The index of the mirror usage point (deprecated, use device_id)
            device_id: The device ID to generate a hashed index from
        """
        if mirror_usage_point_index == NO_INDEX and device_id is None:
            return RootURLs.DEFAULT_MUP_ROOT
        else:
            # If device_id is provided, generate hashed index from it
            if device_id is not None:
                index = get_device_hashed_index(device_id)
            else:
                index = mirror_usage_point_index
            return SEP.join([RootURLs.DEFAULT_MUP_ROOT, str(index)])

    @thread_safe_cached
    def usage_point_href(
        self,
        usage_point_index: int | str = NO_INDEX,
        meter_reading_list: bool = False,
        meter_reading_list_index: int = NO_INDEX,
        meter_reading_index: int = NO_INDEX,
        meter_reading_type: bool = False,
        reading_set: bool = False,
        reading_set_index: int = NO_INDEX,
        reading_index: int = NO_INDEX,
    ) -> str:
        """Get a usage point URL with various options."""
        if isinstance(usage_point_index, str):
            base_upt = usage_point_index
        else:
            base_upt = RootURLs.DEFAULT_UPT_ROOT

        if usage_point_index == NO_INDEX:
            return base_upt
        else:
            if isinstance(usage_point_index, str):
                arr = [base_upt]
            else:
                arr = [RootURLs.DEFAULT_UPT_ROOT, str(usage_point_index)]

            if meter_reading_list:
                if meter_reading_list_index == NO_INDEX:
                    arr.extend(["mr"])
                else:
                    arr.extend(["mr", str(meter_reading_list_index)])

            return SEP.join(arr)

    @thread_safe_cached
    def get_der_program_list(self, fsa_href: str) -> str:
        """Get a DER program list URL for an FSA."""
        return SEP.join([fsa_href, "der"])

    @thread_safe_cached
    def get_dr_program_list(self, fsa_href: str) -> str:
        """Get a DR program list URL for an FSA."""
        return SEP.join([fsa_href, "dr"])

    @thread_safe_cached
    def get_fsa_list_href(self, end_device_href: str) -> str:
        """Get an FSA list URL for an end device."""
        return SEP.join([end_device_href, PathComponent.FSA])

    @thread_safe_cached
    def get_response_set_href(self) -> str:
        """Get the response set URL."""
        return RootURLs.DEFAULT_RSPS_ROOT

    @thread_safe_cached
    def get_der_list_href(self, index: int = NO_INDEX) -> str:
        """Get a DER list URL."""
        if index == NO_INDEX:
            return RootURLs.DEFAULT_DER_ROOT
        else:
            return SEP.join([RootURLs.DEFAULT_DER_ROOT, str(index)])

    @thread_safe_cached
    def get_enddevice_href(self, edev_indx: int = NO_INDEX, subref: str = None) -> str:
        """Get an end device URL."""
        if edev_indx == NO_INDEX:
            return RootURLs.DEFAULT_EDEV_ROOT
        elif subref:
            return SEP.join([RootURLs.DEFAULT_EDEV_ROOT, f"{edev_indx}", f"{subref}"])
        else:
            return SEP.join([RootURLs.DEFAULT_EDEV_ROOT, f"{edev_indx}"])

    @thread_safe_cached
    def registration_href(self, edev_index: int) -> str:
        """Get a registration URL for an end device."""
        return SEP.join([RootURLs.DEFAULT_EDEV_ROOT, str(edev_index), PathComponent.END_DEVICE_REGISTRATION])

    @thread_safe_cached
    def get_configuration_href(self, edev_index: int) -> str:
        """Get a configuration URL for an end device."""
        return self.get_enddevice_href(edev_index, PathComponent.CONFIGURATION)

    @thread_safe_cached
    def get_power_status_href(self, edev_index: int) -> str:
        """Get a power status URL for an end device."""
        return self.get_enddevice_href(edev_index, PathComponent.END_DEVICE_POWER_STATUS)

    @thread_safe_cached
    def get_device_status(self, edev_index: int) -> str:
        """Get a device status URL for an end device."""
        return self.get_enddevice_href(edev_index, PathComponent.END_DEVICE_STATUS)

    @thread_safe_cached
    def get_device_information(self, edev_index: int) -> str:
        """Get a device information URL for an end device."""
        return self.get_enddevice_href(edev_index, PathComponent.END_DEVICE_INFORMATION)

    @thread_safe_cached
    def get_time_href(self) -> str:
        """Get the time URL."""
        return RootURLs.DEFAULT_TIME_ROOT

    @thread_safe_cached
    def get_log_list_href(self, edev_index: int) -> str:
        """Get a log list URL for an end device."""
        return self.get_enddevice_href(edev_index, PathComponent.END_DEVICE_LOG_EVENT_LIST)

    @thread_safe_cached
    def get_dcap_href(self) -> str:
        """Get the device capability URL."""
        return RootURLs.DEFAULT_DCAP_ROOT

    @thread_safe_cached
    def get_dderc_href(self) -> str:
        """Get the default DER control URL."""
        return SEP.join([RootURLs.DEFAULT_DER_ROOT, PathComponent.DDERC])

    @thread_safe_cached
    def get_derc_default_href(self, derp_index: int) -> str:
        """Get the default DER control URL for a program."""
        return SEP.join([RootURLs.DEFAULT_DER_ROOT, PathComponent.DDERC, f"{derp_index}"])

    @thread_safe_cached
    def get_derc_href(self, index: int = NO_INDEX) -> str:
        """Get a DER control URL."""
        if index == NO_INDEX:
            return SEP.join([RootURLs.DEFAULT_DER_ROOT, PathComponent.DERC])
        return SEP.join([RootURLs.DEFAULT_DER_ROOT, PathComponent.DERC, f"{index}"])

    @thread_safe_cached
    def get_program_href(self, index: int = NO_INDEX, subref: str = None) -> str:
        """Get a program URL."""
        if index == NO_INDEX:
            return RootURLs.DEFAULT_DERP_ROOT
        else:
            if subref is not None:
                return f"{RootURLs.DEFAULT_DERP_ROOT}{SEP}{index}{SEP}{subref}"
            else:
                return f"{RootURLs.DEFAULT_DERP_ROOT}{SEP}{index}"

    def build_link(self, base_url: str, *suffix: str | None) -> str:
        """Build a URL from a base and optional suffixes."""
        result = base_url
        if result.endswith("/"):
            result = result[:-1]
        if suffix:
            for p in suffix:
                if p is not None:
                    if isinstance(p, str):
                        if p.startswith("/"):
                            result += f"{p}"
                        else:
                            result += f"/{p}"
                    else:
                        result += f"/{p}"
        return result

    def extend_url(self, base_url: str, index: int | None = None, suffix: str | None = None) -> str:
        """Extend a URL with optional index and suffix."""
        result = base_url
        if index is not None:
            result += f"/{index}"
        if suffix:
            result += f"/{suffix}"
        return result


# Resource URL classes
@dataclass
class EndDeviceHref:
    """URLs for an end device resource."""

    index: int = None
    _root: str = None

    def __init__(self, index: int = None, edev_href: str = None):
        """Initialize with either an index or an href."""
        if index is None and edev_href is None:
            raise ValueError("Must have either index or edev_href specified")
        if index is not None and edev_href is not None:
            raise ValueError("Cannot have both index and edev_href specified")

        self.index = index
        if edev_href is not None:
            try:
                # Handle both slash and underscore separators
                if "/" in edev_href and "_" not in edev_href:
                    # Handle slash format (e.g., "/edev/0")
                    parts = edev_href.split("/")
                    # Find the part after "edev"
                    for i, part in enumerate(parts):
                        if part == "edev" and i + 1 < len(parts) and parts[i + 1].isdigit():
                            self.index = int(parts[i + 1])
                            break
                else:
                    # Handle underscore format (e.g., "/edev_0")
                    parts = edev_href.split(SEP)
                    if len(parts) >= 2:
                        self.index = int(parts[1])

                if self.index is None:
                    raise ValueError(f"Could not extract index from href: {edev_href}")

            except (ValueError, IndexError) as e:
                _log.error(f"Error parsing EndDevice href '{edev_href}': {e}")
                # Fallback to a deterministic index
                import hashlib

                hash_obj = hashlib.md5(edev_href.encode("utf-8"))
                self.index = int(hash_obj.hexdigest(), 16) % 10000

        self._root = SEP.join([RootURLs.DEFAULT_EDEV_ROOT, str(self.index)])

    @staticmethod
    def parse(href: str) -> EndDeviceHref:
        """Parse an href into an EndDeviceHref."""
        index = int(href.split(SEP)[1])
        return EndDeviceHref(index)

    def __str__(self) -> str:
        """Convert to a string."""
        return SEP.join([RootURLs.DEFAULT_EDEV_ROOT, str(self.index)])

    @property
    def configuration(self) -> str:
        """Get the configuration URL."""
        return SEP.join([RootURLs.DEFAULT_EDEV_ROOT, str(self.index), PathComponent.CONFIGURATION])

    @property
    def der_list(self) -> str:
        """Get the DER list URL."""
        return SEP.join([RootURLs.DEFAULT_EDEV_ROOT, str(self.index), PathComponent.DER])

    @property
    def device_information(self) -> str:
        """Get the device information URL."""
        return SEP.join([RootURLs.DEFAULT_EDEV_ROOT, str(self.index), PathComponent.END_DEVICE_INFORMATION])

    @property
    def device_status(self) -> str:
        """Get the device status URL."""
        return SEP.join([RootURLs.DEFAULT_EDEV_ROOT, str(self.index), PathComponent.END_DEVICE_STATUS])

    @property
    def power_status(self) -> str:
        """Get the power status URL."""
        return SEP.join([RootURLs.DEFAULT_EDEV_ROOT, str(self.index), PathComponent.END_DEVICE_POWER_STATUS])

    @property
    def registration(self) -> str:
        """Get the registration URL."""
        return SEP.join([RootURLs.DEFAULT_EDEV_ROOT, str(self.index), PathComponent.END_DEVICE_REGISTRATION])

    @property
    def function_set_assignments(self) -> str:
        """Get the FSA URL."""
        return SEP.join([RootURLs.DEFAULT_EDEV_ROOT, str(self.index), PathComponent.END_DEVICE_FSA])

    @property
    def log_event_list(self) -> str:
        """Get the log event list URL."""
        return SEP.join([RootURLs.DEFAULT_EDEV_ROOT, str(self.index), PathComponent.END_DEVICE_LOG_EVENT_LIST])

    def fill_hrefs(self, enddevice: m.EndDevice) -> m.EndDevice:
        """Fill the hrefs for an end device."""
        enddevice.href = self._root
        enddevice.ConfigurationLink = m.ConfigurationLink(self.configuration)
        enddevice.DeviceInformationLink = m.DeviceInformationLink(self.device_information)
        enddevice.DeviceStatusLink = m.DeviceStatusLink(self.device_status)
        enddevice.PowerStatusLink = m.PowerStatusLink(self.power_status)
        enddevice.RegistrationLink = m.RegistrationLink(self.registration)

        # Preserve existing FSA link count if it was already set
        # Otherwise, check the actual list size
        existing_fsa_count = 0
        if hasattr(enddevice, "FunctionSetAssignmentsListLink") and enddevice.FunctionSetAssignmentsListLink:
            existing_fsa_count = enddevice.FunctionSetAssignmentsListLink.all

        # If we have an existing count, preserve it, otherwise try to get the actual count
        if existing_fsa_count > 0:
            enddevice.FunctionSetAssignmentsListLink = m.FunctionSetAssignmentsListLink(
                self.function_set_assignments, all=existing_fsa_count
            )
        else:
            # Try to get the actual count from the list adapter
            try:
                import ieee_2030_5.adapters as adpt

                actual_count = adpt.ListAdapter.get_list_size(self.function_set_assignments)
                enddevice.FunctionSetAssignmentsListLink = m.FunctionSetAssignmentsListLink(
                    self.function_set_assignments, all=actual_count
                )
            except:
                # Fall back to 0 if we can't get the count
                enddevice.FunctionSetAssignmentsListLink = m.FunctionSetAssignmentsListLink(
                    self.function_set_assignments, all=0
                )

        # Similar for other list links - preserve existing counts
        existing_log_count = 0
        if hasattr(enddevice, "LogEventListLink") and enddevice.LogEventListLink:
            existing_log_count = enddevice.LogEventListLink.all
        enddevice.LogEventListLink = m.LogEventListLink(self.log_event_list, all=existing_log_count)

        existing_der_count = 0
        if hasattr(enddevice, "DERListLink") and enddevice.DERListLink:
            existing_der_count = enddevice.DERListLink.all
        enddevice.DERListLink = m.DERListLink(self.der_list, all=existing_der_count)

        return enddevice


@dataclass
class DERHref:
    """URLs for a DER resource."""

    root: str

    def __init__(self, root: str) -> None:
        """Initialize with a root URL."""
        self.root = root

    @property
    def der_availability(self) -> str:
        """Get the DER availability URL."""
        return SEP.join([self.root, PathComponent.DER_AVAILABILITY])

    @property
    def der_status(self) -> str:
        """Get the DER status URL."""
        return SEP.join([self.root, PathComponent.DER_STATUS])

    @property
    def der_capability(self) -> str:
        """Get the DER capability URL."""
        return SEP.join([self.root, PathComponent.DER_CAPABILITY])

    @property
    def der_settings(self) -> str:
        """Get the DER settings URL."""
        return SEP.join([self.root, PathComponent.DER_SETTINGS])

    @property
    def der_current_program(self) -> str:
        """Get the DER current program URL."""
        return SEP.join([self.root, PathComponent.DER_PROGRAM])

    def fill_hrefs(self, der: m.DER) -> m.DER:
        """Fill the hrefs for a DER."""
        der.href = self.root
        der.DERAvailabilityLink = m.DERAvailabilityLink(self.der_availability)
        der.DERStatusLink = m.DERStatusLink(self.der_status)
        der.DERCapabilityLink = m.DERCapabilityLink(self.der_capability)
        der.DERSettingsLink = m.DERSettingsLink(self.der_settings)
        der.DERProgramLink = m.DERProgramLink(self.der_current_program)
        return der


@dataclass
class DeviceCapabilityHref:
    """URLs for a device capability resource."""

    _end_device_index: str
    root: str

    def __init__(self, end_device_index: str) -> None:
        """Initialize with an end device index."""
        self._end_device_index = end_device_index
        self.root = RootURLs.DEFAULT_DCAP_ROOT

    @property
    def enddevice_href(self) -> str:
        """Get the end device URL."""
        return RootURLs.DEFAULT_EDEV_ROOT

    @property
    def mirror_usage_point_href(self) -> str:
        """Get the mirror usage point URL."""
        return RootURLs.DEFAULT_MUP_ROOT

    @property
    def self_device_href(self) -> str:
        """Get the self device URL."""
        return RootURLs.DEFAULT_SELF_ROOT

    @property
    def time_href(self) -> str:
        """Get the time URL."""
        return RootURLs.DEFAULT_TIME_ROOT

    @property
    def usage_point_href(self) -> str:
        """Get the usage point URL."""
        return RootURLs.DEFAULT_UPT_ROOT

    def fill_hrefs(self, dcap: m.DeviceCapability) -> m.DeviceCapability:
        """Fill the hrefs for a device capability."""
        dcap.href = self.root
        dcap.EndDeviceListLink = m.EndDeviceListLink(self.enddevice_href, all=1)
        dcap.MirrorUsagePointListLink = m.MirrorUsagePointListLink(self.mirror_usage_point_href, all=0)
        dcap.SelfDeviceLink = m.SelfDeviceLink(self.self_device_href)
        dcap.TimeLink = m.TimeLink(self.time_href)
        dcap.UsagePointListLink = m.UsagePointListLink(self.usage_point_href, all=0)
        dcap.DERProgramListLink = m.DERProgramListLink(href=RootURLs.DEFAULT_DERP_ROOT, all=0)
        # Add the global FSA list link - points to the shared FSA list available to all devices
        # The count will be updated dynamically based on actual FSAs available
        # For now, set to 1 assuming at least the default FSA exists
        dcap.FunctionSetAssignmentsListLink = m.FunctionSetAssignmentsListLink(href="/fsa", all=1)
        return dcap


@dataclass
class DERProgramHref:
    """URLs for a DER program resource."""

    _root: str

    def __init__(self, program_index: int) -> None:
        """Initialize with a program index."""
        self._root = SEP.join([RootURLs.DEFAULT_DERP_ROOT, str(program_index)])

    @property
    def active_control_href(self) -> str:
        """Get the active control href."""
        return SEP.join([self._root, PathComponent.DER_CONTROL_ACTIVE])

    @property
    def default_control_href(self) -> str:
        """Get the default control href."""
        return SEP.join([self._root, PathComponent.DDERC])

    @property
    def der_control_list_href(self) -> str:
        """Get the DER control list href."""
        return SEP.join([self._root, PathComponent.DERC])

    @property
    def der_curve_list_href(self) -> str:
        """Get the DER curve list href."""
        return SEP.join([self._root, PathComponent.CURVE])

    def fill_hrefs(self, program: m.DERProgram) -> m.DERProgram:
        """Fill the hrefs for a DER program."""
        program.href = self._root
        program.ActiveDERControlListLink = m.ActiveDERControlListLink(self.active_control_href, all=0)
        program.DefaultDERControlLink = m.DefaultDERControlLink(self.default_control_href)
        program.DERControlListLink = m.DERControlListLink(href=self.der_control_list_href, all=0)
        program.DERCurveListLink = m.DERCurveListLink(href=self.der_curve_list_href, all=0)
        return program


@dataclass
class ParsedUsagePointHref:
    """Parser for usage point hrefs."""

    _href: str
    _split: list[str]

    def __init__(self, href: str):
        """Initialize with an href string."""
        self._href = href
        self._split = href.split(SEP)

    def last_list(self) -> str:
        """Get the container href of an item."""
        if self._split[-1].isnumeric():
            return SEP.join(self._split[:-1])
        return self._href

    def has_usage_point_index(self) -> bool:
        """Check if there is a usage point index."""
        return self.usage_point_index is not None

    def has_extra(self) -> bool:
        """Check if there are extra components."""
        return (
            self.has_meter_reading_list()
            or self.has_reading_list()
            or self.has_reading_set_list()
            or self.has_reading_set_reading_list()
        )

    def has_meter_reading_list(self) -> bool:
        """Check if there is a meter reading list."""
        try:
            return self._split[2] == "mr"
        except IndexError:
            return False

    def has_reading_type(self) -> bool:
        """Check if there is a reading type."""
        try:
            return self._split[4] == "rt"
        except IndexError:
            return False

    def has_reading_set_list(self) -> bool:
        """Check if there is a reading set list."""
        try:
            return self._split[4] == "rs"
        except IndexError:
            return False

    def has_reading_set_reading_list(self) -> bool:
        """Check if there is a reading set reading list."""
        try:
            return self._split[6] == "r"
        except IndexError:
            return False

    def has_reading_list(self) -> bool:
        """Check if there is a reading list."""
        try:
            return self._split[4] == "r" or self._split[6] == "r"
        except IndexError:
            return False

    @property
    def client_index(self) -> int | None:
        """Get the client index from format: /mup_{client}_{pointindex}."""
        try:
            # New format: /mup_{client_index}_{usage_point_index}
            # _split[0] = '/mup', _split[1] = client_index, _split[2] = usage_point_index
            return int(self._split[1])
        except (IndexError, ValueError):
            return None

    @property
    def usage_point_index(self) -> int | None:
        """Get the usage point index from format: /mup_{client}_{pointindex}."""
        try:
            # New format: /mup_{client_index}_{usage_point_index}
            # _split[0] = '/mup', _split[1] = client_index, _split[2] = usage_point_index
            return int(self._split[2])
        except (IndexError, ValueError):
            return None

    @property
    def meter_reading_index(self) -> int | None:
        """Get the meter reading index."""
        try:
            return int(self._split[3])
        except (IndexError, ValueError):
            return None

    @property
    def reading_set_index(self) -> int | None:
        """Get the reading set index."""
        try:
            if self._split[4] == "rs":
                return int(self._split[5])
        except (IndexError, ValueError):
            pass
        return None

    @property
    def reading_set_reading_index(self) -> int | None:
        """Get the reading set reading index."""
        try:
            if self._split[6] == "r":
                return int(self._split[7])
        except (IndexError, ValueError):
            pass
        return None

    @property
    def reading_index(self) -> int | None:
        """Get the reading index."""
        try:
            if self._split[4] == "r":
                return int(self._split[5])
            elif self._split[6] == "r":
                return int(self._split[7])
        except (IndexError, ValueError):
            pass
        return None


@dataclass
class UsagePointHref:
    """URLs for usage point resources."""

    _href: str = None
    _root: str = "/upt"

    def is_root(self) -> bool:
        """Check if this is a root URL."""
        return self._href == self._root

    def value(self) -> str:
        """Get the root value."""
        return self._root

    def usage_point(self, usage_point_index: int) -> str:
        """Get a usage point URL."""
        return SEP.join([self._root, str(usage_point_index)])

    def meterreading_list(self, usage_point_index: int) -> str:
        """Get a meter reading list URL."""
        return SEP.join([self._root, str(usage_point_index), "mr"])

    def meterreading(self, usage_point_index: int, meter_reading_index: int) -> str:
        """Get a meter reading URL."""
        return SEP.join([self.meterreading_list(usage_point_index), str(meter_reading_index)])

    def readingset_list(self, usage_point_index: int, meter_reading_index: int) -> str:
        """Get a reading set list URL."""
        return SEP.join([self.meterreading(usage_point_index, meter_reading_index), "rs"])

    def readingtype(self, usage_point_index: int, meter_reading_index: int) -> str:
        """Get a reading type URL."""
        return SEP.join([self.meterreading(usage_point_index, meter_reading_index), "rt"])

    def readingset(self, usage_point_index: int, meter_reading_index: int, reading_set_index: int) -> str:
        """Get a reading set URL."""
        return SEP.join([self.readingset_list(usage_point_index, meter_reading_index), str(reading_set_index)])

    def readingsetreading_list(self, usage_point_index: int, meter_reading_index: int, reading_set_index: int) -> str:
        """Get a reading set reading list URL."""
        return SEP.join([self.readingset(usage_point_index, meter_reading_index, reading_set_index), "r"])

    def readingsetreading(
        self, usage_point_index: int, meter_reading_index: int, reading_set_index: int, reading_index: int
    ) -> str:
        """Get a reading set reading URL."""
        return SEP.join(
            [self.readingsetreading_list(usage_point_index, meter_reading_index, reading_set_index), str(reading_index)]
        )

    def reading_list(self, usage_point_index: int, meter_reading_index: int) -> str:
        """Get a reading list URL."""
        return SEP.join([self.meterreading(usage_point_index, meter_reading_index), "r"])

    def reading(self, usage_point_index: int, meter_reading_index: int, reading_index: int) -> str:
        """Get a reading URL."""
        return SEP.join([self.reading_list(usage_point_index, meter_reading_index), str(reading_index)])


@dataclass
class MirrorUsagePointHref:
    """Mirror usage point href data."""

    mirror_usage_point_index: int = NO_INDEX
    meter_reading_list_index: int = NO_INDEX
    meter_reading_index: int = NO_INDEX
    reading_set_index: int = NO_INDEX
    reading_index: int = NO_INDEX

    @staticmethod
    def parse(href: str) -> MirrorUsagePointHref:
        """Parse an href into a MirrorUsagePointHref."""
        items = href.split(SEP)
        if len(items) == 1:
            return MirrorUsagePointHref()
        if len(items) == 2:
            return MirrorUsagePointHref(int(items[1]))
        return MirrorUsagePointHref()


@dataclass
class EdevHref:
    """End device href data."""

    edev_index: int
    edev_subtype: EDevSubType = EDevSubType.NONE
    edev_subtype_index: int = NO_INDEX
    edev_der_subtype: DERSubType = DERSubType.NONE

    def __str__(self) -> str:
        """Convert to a string."""
        value = "/edev"
        if self.edev_index != NO_INDEX:
            value = f"{value}{SEP}{self.edev_index}"
        if self.edev_subtype != EDevSubType.NONE:
            value = f"{value}{SEP}{self.edev_subtype.value}"
        if self.edev_subtype_index != NO_INDEX:
            value = f"{value}{SEP}{self.edev_subtype_index}"
        if self.edev_der_subtype != DERSubType.NONE:
            value = f"{value}{SEP}{self.edev_der_subtype.value}"
        return value

    @staticmethod
    def parse(path: str) -> EdevHref:
        """Parse a path into an EdevHref."""
        split_pth = path.split(SEP)
        if split_pth[0] != PathComponent.EDEV and split_pth[0][1:] != PathComponent.EDEV:
            raise ValueError(f"Must start with {PathComponent.EDEV}")

        if len(split_pth) == 1:
            return EdevHref(NO_INDEX)
        elif len(split_pth) == 2:
            return EdevHref(int(split_pth[1]))
        elif len(split_pth) == 3:
            return EdevHref(int(split_pth[1]), edev_subtype=EDevSubType(split_pth[2]))
        elif len(split_pth) == 4:
            return EdevHref(
                int(split_pth[1]), edev_subtype=EDevSubType(split_pth[2]), edev_subtype_index=int(split_pth[3])
            )
        elif len(split_pth) == 5:
            return EdevHref(
                int(split_pth[1]),
                edev_subtype=EDevSubType(split_pth[2]),
                edev_subtype_index=int(split_pth[3]),
                edev_der_subtype=DERSubType(split_pth[4]),
            )
        else:
            raise ValueError("Out of bounds parsing.")

    def __eq__(self, other: object) -> bool:
        """Compare for equality."""
        if not isinstance(other, EdevHref):
            return False
        return (
            other.edev_index == self.edev_index
            and other.edev_subtype == self.edev_subtype
            and other.edev_subtype_index == self.edev_subtype_index
            and other.edev_der_subtype == self.edev_der_subtype
        )


class FSAHref(NamedTuple):
    """Function set assignments href data."""

    fsa_index: int = NO_INDEX
    fsa_sub: FSASubType = FSASubType.NONE


def fsa_parse(path: str) -> FSAHref:
    """Parse a path into an FSAHref."""
    split_pth = path.split(SEP)
    if len(split_pth) == 1:
        return FSAHref(NO_INDEX)
    elif len(split_pth) == 2:
        return FSAHref(int(split_pth[1]))
    elif len(split_pth) == 3:
        return FSAHref(int(split_pth[1]), FSASubType(split_pth[2]))
    raise ValueError("Invalid parsing path.")


class DERProgramHrefOld(NamedTuple):
    """Old-style DER program href data."""

    root: str
    index: int
    derp_subtype: DERProgramSubType = DERProgramSubType.NONE
    derp_subtype_index: int = NO_INDEX

    @staticmethod
    def parse(href: str) -> DERProgramHrefOld:
        """Parse an href into a DERProgramHrefOld."""
        parsed = href.split(SEP)
        if len(parsed) == 1:
            return DERProgramHrefOld(parsed[0], NO_INDEX)
        elif len(parsed) == 2:
            return DERProgramHrefOld(parsed[0], int(parsed[1]))
        else:
            mapped = {
                PathComponent.DERC: DERProgramSubType.DER_CONTROL_LIST,
                PathComponent.DERCA: DERProgramSubType.ACTIVE_DER_CONTROL_LIST,
                PathComponent.DDERC: DERProgramSubType.DEFAULT_DER_CONTROL,
            }
            if len(parsed) == 4:
                return DERProgramHrefOld(parsed[0], int(parsed[1]), mapped[parsed[2]], int(parsed[3]))
            return DERProgramHrefOld(parsed[0], int(parsed[1]), mapped[parsed[2]])


# Instantiate the URL builder
url_builder = URLBuilder.get_instance()


# Compatibility functions that use the URL builder
def der_program_parse(href: str) -> DERProgramHrefOld:
    """Parse a DER program href."""
    return DERProgramHrefOld.parse(href)


def der_program_href(
    index: int = NO_INDEX, sub: DERProgramSubType = DERProgramSubType.NONE, subindex: int = NO_INDEX
) -> str:
    """Build a DER program href."""
    if index == NO_INDEX:
        return RootURLs.DEFAULT_DERP_ROOT

    if sub == DERProgramSubType.NONE:
        return SEP.join([RootURLs.DEFAULT_DERP_ROOT, str(index)])

    if sub == DERProgramSubType.ACTIVE_DER_CONTROL_LIST:
        if subindex == NO_INDEX:
            return SEP.join([RootURLs.DEFAULT_DERP_ROOT, str(index), PathComponent.DER_CONTROL_ACTIVE])
        else:
            return SEP.join([RootURLs.DEFAULT_DERP_ROOT, str(index), PathComponent.DER_CONTROL_ACTIVE, str(subindex)])

    if sub == DERProgramSubType.DEFAULT_DER_CONTROL:
        if subindex == NO_INDEX:
            return SEP.join([RootURLs.DEFAULT_DERP_ROOT, str(index), PathComponent.DDERC])
        else:
            return SEP.join([RootURLs.DEFAULT_DERP_ROOT, str(index), PathComponent.DDERC, str(subindex)])

    if sub == DERProgramSubType.DER_CURVE_LIST:
        if subindex == NO_INDEX:
            return SEP.join([RootURLs.DEFAULT_DERP_ROOT, str(index), PathComponent.CURVE])
        else:
            return SEP.join([RootURLs.DEFAULT_DERP_ROOT, str(index), PathComponent.CURVE, str(subindex)])

    if sub == DERProgramSubType.DER_CONTROL_LIST:
        if subindex == NO_INDEX:
            return SEP.join([RootURLs.DEFAULT_DERP_ROOT, str(index), PathComponent.DERC])
        else:
            return SEP.join([RootURLs.DEFAULT_DERP_ROOT, str(index), PathComponent.DERC, str(subindex)])

    if sub == DERProgramSubType.DER_CONTROL_REPLY_TO:
        return RootURLs.DEFAULT_RSPS_ROOT

    # Default return if none of the above conditions are met
    return SEP.join([RootURLs.DEFAULT_DERP_ROOT, str(index)])


# Thread-safe versions of the helper functions
@thread_safe_cached
def get_server_config_href() -> str:
    """Get the server configuration URL."""
    return url_builder.get_server_config_href()


@thread_safe_cached
def get_enddevice_list_href() -> str:
    """Get the end device list URL."""
    return url_builder.get_enddevice_list_href()


@thread_safe_cached
def curve_href(index: int = NO_INDEX) -> str:
    """Get a curve URL."""
    return url_builder.curve_href(index)


@thread_safe_cached
def fsa_href(index: int = NO_INDEX, edev_index: int = NO_INDEX) -> str:
    """Get an FSA URL."""
    return url_builder.fsa_href(index, edev_index)


@thread_safe_cached
def derp_href(edev_index: int, fsa_index: int) -> str:
    """Get a DER program URL for an end device FSA."""
    return url_builder.derp_href(edev_index, fsa_index)


@thread_safe_cached
def der_href(index: int = NO_INDEX, fsa_index: int = NO_INDEX, edev_index: int = NO_INDEX) -> str:
    """Get a DER URL."""
    return url_builder.der_href(index, fsa_index, edev_index)


@thread_safe_cached
def edev_der_href(edev_index: int, der_index: int = NO_INDEX) -> str:
    """Get a DER URL for an end device."""
    return url_builder.edev_der_href(edev_index, der_index)


@thread_safe_cached
def der_sub_href(edev_index: int, index: int = NO_INDEX, subtype: DERSubType = None) -> str:
    """Get a DER sub-resource URL."""
    return url_builder.der_sub_href(edev_index, index, subtype)


@thread_safe_cached
def get_device_hashed_index(device_id: str) -> int:
    """Get the consistent hashed index for a device ID.

    This function provides the standard hashing mechanism used throughout
    the IEEE 2030.5 server for converting device IDs to consistent indices.

    Args:
        device_id: The device identifier string

    Returns:
        int: Hashed index (0-99999)
    """
    import hashlib

    hash_obj = hashlib.sha256(device_id.encode("utf-8"))
    return int(hash_obj.hexdigest()[:8], 16) % 100000  # Limit to 5 digits


def mirror_usage_point_href(mirror_usage_point_index: int = NO_INDEX, device_id: str = None) -> str:
    """Get a mirror usage point URL."""
    return url_builder.mirror_usage_point_href(mirror_usage_point_index, device_id)


@thread_safe_cached
def usage_point_href(
    usage_point_index: int | str = NO_INDEX,
    meter_reading_list: bool = False,
    meter_reading_list_index: int = NO_INDEX,
    meter_reading_index: int = NO_INDEX,
    meter_reading_type: bool = False,
    reading_set: bool = False,
    reading_set_index: int = NO_INDEX,
    reading_index: int = NO_INDEX,
) -> str:
    """Get a usage point URL with various options."""
    return url_builder.usage_point_href(
        usage_point_index,
        meter_reading_list,
        meter_reading_list_index,
        meter_reading_index,
        meter_reading_type,
        reading_set,
        reading_set_index,
        reading_index,
    )


@thread_safe_cached
def get_der_program_list(fsa_href: str) -> str:
    """Get a DER program list URL for an FSA."""
    return url_builder.get_der_program_list(fsa_href)


@thread_safe_cached
def get_dr_program_list(fsa_href: str) -> str:
    """Get a DR program list URL for an FSA."""
    return url_builder.get_dr_program_list(fsa_href)


@thread_safe_cached
def get_fsa_list_href(end_device_href: str) -> str:
    """Get an FSA list URL for an end device."""
    return url_builder.get_fsa_list_href(end_device_href)


@thread_safe_cached
def get_response_set_href() -> str:
    """Get the response set URL."""
    return url_builder.get_response_set_href()


@thread_safe_cached
def get_der_list_href(index: int = NO_INDEX) -> str:
    """Get a DER list URL."""
    return url_builder.get_der_list_href(index)


@thread_safe_cached
def get_enddevice_href(edev_indx: int = NO_INDEX, subref: str = None) -> str:
    """Get an end device URL."""
    return url_builder.get_enddevice_href(edev_indx, subref)


@thread_safe_cached
def registration_href(edev_index: int) -> str:
    """Get a registration URL for an end device."""
    return url_builder.registration_href(edev_index)


@thread_safe_cached
def get_configuration_href(edev_index: int) -> str:
    """Get a configuration URL for an end device."""
    return url_builder.get_configuration_href(edev_index)


@thread_safe_cached
def get_power_status_href(edev_index: int) -> str:
    """Get a power status URL for an end device."""
    return url_builder.get_power_status_href(edev_index)


@thread_safe_cached
def get_device_status(edev_index: int) -> str:
    """Get a device status URL for an end device."""
    return url_builder.get_device_status(edev_index)


@thread_safe_cached
def get_device_information(edev_index: int) -> str:
    """Get a device information URL for an end device."""
    return url_builder.get_device_information(edev_index)


@thread_safe_cached
def get_time_href() -> str:
    """Get the time URL."""
    return url_builder.get_time_href()


@thread_safe_cached
def get_log_list_href(edev_index: int) -> str:
    """Get a log list URL for an end device."""
    return url_builder.get_log_list_href(edev_index)


@thread_safe_cached
def get_dcap_href() -> str:
    """Get the device capability URL."""
    return url_builder.get_dcap_href()


@thread_safe_cached
def get_dderc_href() -> str:
    """Get the default DER control URL."""
    return url_builder.get_dderc_href()


@thread_safe_cached
def get_derc_default_href(derp_index: int) -> str:
    """Get the default DER control URL for a program."""
    return url_builder.get_derc_default_href(derp_index)


@thread_safe_cached
def get_derc_href(index: int = NO_INDEX) -> str:
    """Get a DER control URL."""
    return url_builder.get_derc_href(index)


@thread_safe_cached
def get_program_href(index: int = NO_INDEX, subref: str = None) -> str:
    """Get a program URL."""
    return url_builder.get_program_href(index, subref)


def build_link(base_url: str, *suffix: str | None) -> str:
    """Build a URL from a base and optional suffixes."""
    return url_builder.build_link(base_url, *suffix)


def extend_url(base_url: str, index: int | None = None, suffix: str | None = None) -> str:
    """Extend a URL with optional index and suffix."""
    return url_builder.extend_url(base_url, index, suffix)


# Define additional constants for backward compatibility
sdev: str = RootURLs.DEFAULT_SELF_ROOT
admin: str = "/admin"
uuid_gen: str = "/uuid"

# Default export of important symbols
__all__ = [
    "NO_INDEX",
    "SEP",
    "PathComponent",
    "RootURLs",
    "ResourceType",
    "DERSubType",
    "FSASubType",
    "EDevSubType",
    "DERProgramSubType",
    "URLBuilder",
    "URLRegistry",
    "HrefParser",
    "HrefEventParser",
    "EndDeviceHref",
    "DERHref",
    "DeviceCapabilityHref",
    "DERProgramHref",
    "ParsedUsagePointHref",
    "UsagePointHref",
    "MirrorUsagePointHref",
    "EdevHref",
    "FSAHref",
    "get_server_config_href",
    "get_enddevice_list_href",
    "curve_href",
    "fsa_href",
    "derp_href",
    "der_href",
    "edev_der_href",
    "der_sub_href",
    "mirror_usage_point_href",
    "usage_point_href",
    "get_der_program_list",
    "get_dr_program_list",
    "get_fsa_list_href",
    "get_response_set_href",
    "get_der_list_href",
    "get_enddevice_href",
    "registration_href",
    "get_configuration_href",
    "get_power_status_href",
    "get_device_status",
    "get_device_information",
    "get_time_href",
    "get_log_list_href",
    "get_dcap_href",
    "get_dderc_href",
    "get_derc_default_href",
    "get_derc_href",
    "get_program_href",
    "build_link",
    "extend_url",
    "DEFAULT_TIME_ROOT",
    "DEFAULT_DCAP_ROOT",
    "DEFAULT_EDEV_ROOT",
    "DEFAULT_UPT_ROOT",
    "DEFAULT_MUP_ROOT",
    "DEFAULT_DRP_ROOT",
    "DEFAULT_SELF_ROOT",
    "DEFAULT_MESSAGE_ROOT",
    "DEFAULT_DER_ROOT",
    "DEFAULT_CURVE_ROOT",
    "DEFAULT_RSPS_ROOT",
    "DEFAULT_LOG_EVENT_ROOT",
    "DEFAULT_FSA_ROOT",
    "DEFAULT_DERP_ROOT",
    "DEFAULT_DDERC_ROOT",
    "DEFAULT_CONTROL_ROOT",
]

# Add backward compatibility constants to __all__
for attr_name in dir(PathComponent):
    if not attr_name.startswith("_"):
        globals()[attr_name] = getattr(PathComponent, attr_name)
        __all__.append(attr_name)

for attr_name in dir(RootURLs):
    if not attr_name.startswith("_"):
        globals()[attr_name] = getattr(RootURLs, attr_name)
        __all__.append(attr_name)
