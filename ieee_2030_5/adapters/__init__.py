# ieee_2030_5/adapters/__init__.py
"""
Thread-safe adapters for IEEE 2030.5 server.
"""
import threading
import logging
from pathlib import Path
from typing import Any
import OpenSSL
from flask import Response, request, g
from ieee_2030_5.utils import dataclass_to_xml, xml_to_dataclass
import ieee_2030_5.models as m
from ieee_2030_5 import hrefs
from ieee_2030_5.config import DeviceConfiguration, ServerConfiguration
from ieee_2030_5.persistance.points import atomic_operation, get_db
from ieee_2030_5.certs import TLSRepository, lfdi_from_fingerprint, sfdi_from_lfdi
from blinker import Signal
from .base import (ThreadSafeListAdapter, ThreadSafeEndDeviceAdapter, initialize_adapters,
                   get_adapter_stats, AdapterResult)
# Import the global instances
from .base import ListAdapter, EndDeviceAdapter

_log = logging.getLogger(__name__)

# Create additional specialized adapters
DERControlAdapter = ThreadSafeListAdapter(m.DERControl)
DERProgramAdapter = ThreadSafeListAdapter(m.DERProgram)
DERCurveAdapter = ThreadSafeListAdapter(m.DERCurve)
FunctionSetAssignmentsAdapter = ThreadSafeListAdapter(m.FunctionSetAssignments)
DeviceCapabilityAdapter = ThreadSafeListAdapter(m.DeviceCapability)
RegistrationAdapter = ThreadSafeListAdapter(m.Registration)


# Add compatibility method for list_size
def list_size(list_uri: str) -> int:
    """Compatibility method for existing code that uses list_size."""
    return ListAdapter.get_list_size(list_uri)


# Add method directly to the ListAdapter instance
ListAdapter.list_size = lambda uri: ListAdapter.get_list_size(uri)


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
    'ListAdapter', 'EndDeviceAdapter', 'DERControlAdapter', 'DERProgramAdapter', 'DERCurveAdapter',
    'FunctionSetAssignmentsAdapter', 'DeviceCapabilityAdapter', 'RegistrationAdapter',
    'TimeAdapter', 'initialize_adapters', 'get_adapter_stats', 'AdapterResult'
]


# Helper function for certificate names
def normalize_certificate_name(href: str) -> str:
    """Normalize certificate name from href."""
    return href.rsplit(hrefs.SEP, 1)[-1]


# Helper function to extract LFDI from certificate
def get_lfdi_from_cert_file(cert_path: str) -> str:
    """Extract LFDI from certificate file."""
    try:
        with open(cert_path, 'rb') as cert_file:
            cert_data = cert_file.read()
            x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert_data)
            fingerprint = x509.digest("sha256").decode('ascii')
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
    if request.method in ('POST', 'PUT'):
        data = request.data.decode('utf-8')
        item = xml_to_dataclass(data)
        if not isinstance(item, m.EndDevice):
            _log.error("EndDevice was not passed via data.")
            return Response(status=400)
        if request.method == 'POST':
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
        elif request.method == 'PUT':
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
    start = int(request.args.get('s', 0))
    after = int(request.args.get('a', 0))
    limit = int(request.args.get('l', 1))
    try:
        # This is now thread-safe
        allofem = EndDeviceAdapter.fetch_all(m.EndDeviceList(),
                                             start=start,
                                             after=after,
                                             limit=limit)
        return Response(dataclass_to_xml(allofem), status=200)
    except Exception as e:
        _log.error(f"Failed to fetch end devices: {e}")
        return Response("Internal server error", status=500)


def _admin_controls(self) -> Response:
    """Thread-safe DER control management."""
    if request.method in ('POST', 'PUT'):
        data = request.data.decode('utf-8')
        control = xml_to_dataclass(data)
        if not isinstance(control, m.DERControl):
            _log.error("DERControl was not passed via data.")
            return Response(status=400)
        if request.method == 'POST':
            if control.href:
                _log.error(f"POST method with existing object {control.href}")
                return Response(status=400)
            # Thread-safe add
            try:
                result = DERControlAdapter.append(hrefs.DEFAULT_CONTROL_ROOT, control)
                if result.success:
                    return Response(dataclass_to_xml(result.data),
                                    status=201,
                                    headers={'Location': result.location})
                else:
                    return Response(result.error, status=400)
            except Exception as e:
                _log.error(f"Failed to add DER control: {e}")
                return Response("Internal server error", status=500)
        elif request.method == 'PUT':
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
    start = int(request.args.get('s', 0))
    after = int(request.args.get('a', 0))
    limit = int(request.args.get('l', 1))
    try:
        control_list = DERControlAdapter.get_resource_list(hrefs.DEFAULT_CONTROL_ROOT,
                                                           start=start,
                                                           after=after,
                                                           limit=limit)
        return Response(dataclass_to_xml(control_list), status=200)
    except Exception as e:
        _log.error(f"Failed to fetch DER controls: {e}")
        return Response("Internal server error", status=500)


def create_device_capability(end_device_index: int,
                             device_cfg: DeviceConfiguration) -> m.DeviceCapability:
    """Thread-safe device capability creation."""
    try:
        dcap_href = hrefs.DeviceCapabilityHref(end_device_index)
        device_capability = m.DeviceCapability()
        device_capability = dcap_href.fill_hrefs(device_capability)
        device_capability.MirrorUsagePointListLink = m.MirrorUsagePointListLink(
            href=hrefs.DEFAULT_MUP_ROOT, all=0)
        device_capability.TimeLink = m.TimeLink(href=hrefs.DEFAULT_TIME_ROOT)
        device_capability.UsagePointListLink = m.UsagePointListLink(href=hrefs.DEFAULT_UPT_ROOT,
                                                                    all=0)
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
        device.MirrorUsagePointListLink = m.MirrorUsagePointListLink(href=hrefs.DEFAULT_MUP_ROOT,
                                                                     all=0)
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
                control_index = next(i for i, c in enumerate(control_list.DERControl)
                                     if c.mRID == event.mRID)
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
                control_index = next(i for i, c in enumerate(control_list.DERControl)
                                     if c.mRID == event.mRID)
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


# Global mRID management with thread safety
class ThreadSafeGlobalMRIDs:
    """Thread-safe global mRID management."""

    def __init__(self):
        self._lock = threading.RLock()
        self._db = get_db()
        self._mrid_counter_key = "global:mrid_counter"
        self._mrid_index_key = "global:mrid_index"

    def new_mrid(self) -> bytes:
        """Generate a new unique mRID."""
        with self._lock:
            try:
                import pickle
                # Get current counter
                counter_data = self._db.get_point(self._mrid_counter_key)
                current_counter = 0 if counter_data is None else pickle.loads(counter_data)
                # Generate new mRID
                new_mrid = f"mrid_{current_counter}".encode()
                # Update counter
                self._db.set_point(self._mrid_counter_key, pickle.dumps(current_counter + 1))
                return new_mrid
            except Exception as e:
                _log.error(f"Failed to generate new mRID: {e}")
                raise

    def add_item_with_mrid(self, key: str, item: Any):
        """Add an item with its mRID to the global index."""
        with self._lock:
            try:
                import pickle
                # Get current index
                index_data = self._db.get_point(self._mrid_index_key)
                mrid_index = {} if index_data is None else pickle.loads(index_data)
                # Add item
                if hasattr(item, 'mRID'):
                    mrid_index[item.mRID] = key
                # Store updated index
                self._db.set_point(self._mrid_index_key, pickle.dumps(mrid_index))
            except Exception as e:
                _log.error(f"Failed to add item with mRID: {e}")
                raise


# Add missing method that might be referenced
def clear_all_adapters():
    """Clear all adapters data."""
    with atomic_operation():
        try:
            _log.info("Clearing all adapter data")
            get_db().clear_all()
            initialize_adapters()    # Re-initialize adapters
        except Exception as e:
            _log.error(f"Failed to clear adapters: {e}")
            raise


# Global instance
GlobalmRIDs = ThreadSafeGlobalMRIDs()


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
                derp.mRID = GlobalmRIDs.new_mrid()
            result = ListAdapter.append(hrefs.DEFAULT_DERP_ROOT, derp)
            if not result.success:
                raise Exception(f"Failed to add default program: {result.error}")
            program_hrefs = hrefs.DERProgramHref(index)
            derp.href = program_hrefs._root
            derp.ActiveDERControlListLink = m.ActiveDERControlListLink(
                program_hrefs.active_control_href)
            derp.DefaultDERControlLink = m.DefaultDERControlLink(
                program_hrefs.default_control_href)
            derp.DERControlListLink = m.DERControlListLink(program_hrefs.der_control_list_href)
            # Add default control if configured
            if config.default_der_control:
                dderc = config.default_der_control
                dderc.mRID = GlobalmRIDs.new_mrid()
                dderc.href = derp.DefaultDERControlLink.href
                ListAdapter.set_single(uri=derp.DefaultDERControlLink.href, obj=dderc)
            # Initialize sub-lists
            ListAdapter.initialize_uri(derp.DERControlListLink.href, m.DERControl)
    # Add configured programs thread-safely
    for program_cfg in config.programs:
        try:
            with atomic_operation():
                program_hrefs = hrefs.DERProgramHref(
                    ListAdapter.get_list_size(hrefs.DEFAULT_DERP_ROOT))
                default_der_control = program_cfg.pop("DefaultDERControl", None)
                program = m.DERProgram(**program_cfg)
                if not program.mRID:
                    program.mRID = GlobalmRIDs.new_mrid()
                program = program_hrefs.fill_hrefs(program)
                result = ListAdapter.append(hrefs.DEFAULT_DERP_ROOT, program)
                if not result.success:
                    raise Exception(f"Failed to add program: {result.error}")
                # Handle default control...
                if default_der_control:
                    dderc = m.DefaultDERControl(href=program.DefaultDERControlLink.href,
                                                **default_der_control)
                    if not dderc.mRID:
                        dderc.mRID = GlobalmRIDs.new_mrid()
                    ListAdapter.set_single(uri=program.DefaultDERControlLink.href, obj=dderc)
                # Initialize lists
                ListAdapter.initialize_uri(program.DERControlListLink.href, m.DERControl)
                ListAdapter.set_single(uri=program.ActiveDERControlListLink.href,
                                       obj=m.DERControlList(DERControl=[]))
        except Exception as e:
            _log.error(
                f"Failed to initialize program {program_cfg.get('description', 'unknown')}: {e}")
            raise
    # Add curves thread-safely
    ListAdapter.initialize_uri(hrefs.DEFAULT_CURVE_ROOT, m.DERCurve)
    for index, curve_cfg in enumerate(config.curves):
        try:
            curve = m.DERCurve(href=hrefs.SEP.join([hrefs.DEFAULT_CURVE_ROOT,
                                                    str(index)]),
                               **curve_cfg)
            if not curve.mRID:
                curve.mRID = GlobalmRIDs.new_mrid()
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
            device_capability = create_device_capability(index, cfg_device)
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
                end_device = m.EndDevice(lFDI=tlsrepo.lfdi(cfg_device.id),
                                         sFDI=tlsrepo.sfdi(cfg_device.id),
                                         postRate=cfg_device.post_rate,
                                         enabled=True,
                                         changedTime=TimeAdapter.current_tick)
                end_device = add_enddevice(end_device)
                GlobalmRIDs.add_item_with_mrid(cfg_device.id, end_device)
                # Add registration
                reg = m.Registration(href=end_device.RegistrationLink.href,
                                     pIN=cfg_device.pin,
                                     pollRate=cfg_device.poll_rate,
                                     dateTimeRegistered=TimeAdapter.current_tick)
                ListAdapter.set_single(uri=reg.href, obj=reg)
                # Handle DERs and FSAs...
                if cfg_device.ders:
                    for der in cfg_device.ders:
                        der_href = hrefs.DERHref(
                            hrefs.SEP.join([hrefs.DEFAULT_DER_ROOT,
                                            str(der_global_count)]))
                        der_global_count += 1
                        der_obj = m.DER(
                            href=der_href.root,
                            DERStatusLink=m.DERStatusLink(der_href.der_status),
                            DERSettingsLink=m.DERSettingsLink(der_href.der_settings),
                            DERCapabilityLink=m.DERCapabilityLink(der_href.der_capability),
                            DERAvailabilityLink=m.DERAvailabilityLink(der_href.der_availability))
                        # Add DER thread-safely
                        result = ListAdapter.append(ed_href.der_list, der_obj)
                        if not result.success:
                            raise Exception(f"Failed to add DER: {result.error}")
        except Exception as e:
            _log.error(f"Failed to initialize device {cfg_device.id}: {e}")
            raise
    _log.info("Thread-safe 2030.5 initialization completed")
