# ieee_2030_5/server/server_constructs.py
from __future__ import annotations

import logging
from copy import deepcopy

import ieee_2030_5.adapters as adpt
import ieee_2030_5.hrefs as hrefs
import ieee_2030_5.models as m
from ieee_2030_5.certs import TLSRepository
from ieee_2030_5.config import DeviceConfiguration, ServerConfiguration
from ieee_2030_5.data.indexer import add_href
from ieee_2030_5.persistance.points import atomic_operation
from ieee_2030_5.server.device_fsa import create_device_fsa_with_program

_log = logging.getLogger(__name__)


# Define ConfigurationError here since it's not in ieee_2030_5.config
class ConfigurationError(Exception):
    """Exception raised for configuration errors."""

    pass


def create_device_capability(
    end_device_index: int, device_cfg: DeviceConfiguration, config: ServerConfiguration = None
) -> m.DeviceCapability:
    """Create a device capability object for the passed device index
    This function does not verify that there is a device at the passed index.
    """
    dcap_href = hrefs.DeviceCapabilityHref(end_device_index)
    device_capability = m.DeviceCapability()
    device_capability = dcap_href.fill_hrefs(device_capability)

    # Set the poll rate for device capability
    if config:
        device_capability.pollRate = adpt.get_poll_rate("device_capability")
    device_capability.MirrorUsagePointListLink = m.MirrorUsagePointListLink(href=hrefs.DEFAULT_MUP_ROOT, all=0)
    device_capability.TimeLink = m.TimeLink(href=hrefs.DEFAULT_TIME_ROOT)
    device_capability.UsagePointListLink = m.UsagePointListLink(href=hrefs.DEFAULT_UPT_ROOT, all=0)

    # Use thread-safe append instead of add
    device_capability_adapter = adpt._get_or_create_adapter("DeviceCapability", m.DeviceCapability)
    result = device_capability_adapter.append(hrefs.DEFAULT_DCAP_ROOT, device_capability)
    if not result.success:
        raise Exception(f"Failed to add device capability: {result.error}")
    return result.data


def add_enddevice(device: m.EndDevice, device_id: str = None) -> m.EndDevice:
    """Populates links to EndDevice resources and adds it to the EndDeviceAdapter.
    If the link is to a single writable (by the client) resource then create the link
    and the resource with default data.  Otherwise, the link will be to a list.  It is
    expected that the list will be populated at a later point in time in the code execution.
    The enddevice is added to the enddevice adapter, and the following links are created and added to the enddevice:
    - `DERListLink`: A link to the DER list for the enddevice
    - `FunctionSetAssignmentsListLink`: A link to the function set assignments list for the enddevice
    - `LogEventListLink`: A link to the log event list for the enddevice
    - `RegistrationLink`: A link to the registration for the enddevice
    - `ConfigurationLink`: A link to the configuration for the enddevice
    - `DeviceInformationLink`: A link to the device information for the enddevice
    - `DeviceStatusLink`: A link to the device status for the enddevice
    - `PowerStatusLink`: A link to the power status for the enddevice
    :param device: The enddevice to add
    :type device: m.EndDevice
    :param device_id: The device ID (often mRID) associated with this device
    :type device_id: str
    :return: The enddevice object that was added to the adapter
    :rtype: m.EndDevice
    """
    # Use thread-safe add method
    device = adpt.EndDeviceAdapter.add(device, device_id=device_id)

    # Create a link object that holds references for linking other objects to the end device.
    ed_href = hrefs.EndDeviceHref(edev_href=device.href)
    ed_href.fill_hrefs(device)

    # Update the stored EndDevice with the filled hrefs
    device_index = int(device.href.split("_")[1]) if "_" in device.href else None
    if device_index is not None:
        device_key = f"enddevice:{device_index}"
        import pickle

        with atomic_operation():
            adpt.EndDeviceAdapter._db.set_point(device_key, pickle.dumps(device))
        _log.debug(f"Updated stored EndDevice with filled links: {device.href}")

    # Store objects in the href cache for retrieval (wrapped in atomic operation)
    with atomic_operation():
        # Configuration
        config = m.Configuration(href=device.ConfigurationLink.href)
        adpt.ListAdapter.set_single(uri=device.ConfigurationLink.href, obj=config)
        add_href(ed_href.configuration, config)

        # Device Information
        device_info = m.DeviceInformation(href=device.DeviceInformationLink.href)
        adpt.ListAdapter.set_single(uri=device.DeviceInformationLink.href, obj=device_info)
        add_href(ed_href.device_information, device_info)

        # Device Status
        device_status = m.DeviceStatus(href=device.DeviceStatusLink.href)
        adpt.ListAdapter.set_single(uri=device.DeviceStatusLink.href, obj=device_status)
        add_href(ed_href.device_status, device_status)

        # Power Status
        power_status = m.PowerStatus(href=device.PowerStatusLink.href)
        adpt.ListAdapter.set_single(uri=device.PowerStatusLink.href, obj=power_status)
        add_href(ed_href.power_status, power_status)

    # Add links to the device
    device.MirrorUsagePointListLink = m.MirrorUsagePointListLink(href=hrefs.DEFAULT_MUP_ROOT, all=0)
    device.UsagePointListLink = m.UsagePointListLink(href=hrefs.DEFAULT_UPT_ROOT, all=0)

    # Initialize list URIs
    adpt.ListAdapter.initialize_uri(hrefs.DEFAULT_MUP_ROOT, m.MirrorUsagePoint)
    adpt.ListAdapter.initialize_uri(hrefs.DEFAULT_UPT_ROOT, m.UsagePoint)
    adpt.ListAdapter.initialize_uri(ed_href.der_list, m.DER)
    adpt.ListAdapter.initialize_uri(ed_href.function_set_assignments, m.FunctionSetAssignments)

    # Store EndDevice in href indexer for individual access
    add_href(device.href, device)
    _log.debug("Stored EndDevice at href %s for individual access", device.href)

    return device


def update_active_der_event_started(event: m.Event):
    """Event triggered when a DERControl event starts
    Find the control and copy it to the ActiveDERControlList
    :param event: The control event
    :type event: m.Event
    """
    adpt.update_active_der_event_started(event)


def update_active_der_event_ended(event: m.Event):
    """Event triggered when a DERControl event ends
    Search over the ActiveDERControlListLink for the event that has been triggered
    and remove it from the list.
    :param event: The control event
    :type event: m.Event
    """
    adpt.update_active_der_event_ended(event)


# Event handlers will be connected during initialization


def create_der_program_and_control(
    default_der_program: m.DERProgram,
    default_der_control: m.DefaultDERControl,
    derp_index: int,
    name: str = None,
) -> tuple[m.DERProgram, m.DefaultDERControl]:
    """Create DER program and control with proper mRIDs.

    Args:
        default_der_program: Template DER program to copy
        default_der_control: Template DER control to copy
        derp_index: Index for the program href
        name: Optional descriptive name for the program

    Returns:
        Tuple of (DERProgram, DefaultDERControl) with proper hrefs and mRIDs
    """
    # Create a deep copy to avoid modifying the originals
    derp = deepcopy(default_der_program)
    dderc = deepcopy(default_der_control)

    # Set description if name is provided
    if name and not derp.description:
        derp.description = name

    # Ensure mRIDs are assigned
    if not derp.mRID:
        derp.mRID = adpt.get_global_mrids().new_mrid()
        _log.debug(
            "Generated new mRID for DERProgram: %s",
            derp.mRID.hex() if isinstance(derp.mRID, bytes) else derp.mRID,
        )

    if not dderc.mRID:
        dderc.mRID = adpt.get_global_mrids().new_mrid()
        _log.debug(
            "Generated new mRID for DefaultDERControl: %s",
            dderc.mRID.hex() if isinstance(dderc.mRID, bytes) else dderc.mRID,
        )

    # Set up program hrefs
    program_hrefs = hrefs.DERProgramHref(derp_index)
    derp.href = program_hrefs._root
    derp.ActiveDERControlListLink = m.ActiveDERControlListLink(program_hrefs.active_control_href)
    derp.DefaultDERControlLink = m.DefaultDERControlLink(program_hrefs.default_control_href)
    derp.DERControlListLink = m.DERControlListLink(program_hrefs.der_control_list_href)
    derp.DERCurveListLink = m.DERCurveListLink(program_hrefs.der_curve_list_href)

    # Set the DefaultDERControl href FIRST before registering
    dderc.href = derp.DefaultDERControlLink.href

    # Register with GlobalmRIDs after hrefs are set
    adpt.get_global_mrids().add_item_with_mrid(derp.href, derp)
    # Note: Don't register dderc here - set_single() will do it automatically below

    # Initialize lists in the storage
    adpt.ListAdapter.initialize_uri(program_hrefs.der_curve_list_href, m.DERCurve)

    # Store the objects
    result = adpt.ListAdapter.append(hrefs.DEFAULT_DERP_ROOT, derp)
    if not result.success:
        raise Exception(f"Failed to store DER program: {result.error}")

    # Note: We do NOT append DefaultDERControl to /dderc global list.
    # DefaultDERControl is accessed through its parent DERProgram link, not as a standalone list.
    # Only store it at its specific href to avoid duplicate mRID registration.

    # CRITICAL: Store the DefaultDERControl at its specific href for individual access via get_href()
    adpt.ListAdapter.set_single(uri=dderc.href, obj=dderc)

    # Also store in the href indexer for fast access
    add_href(dderc.href, dderc)

    _log.debug("Stored DefaultDERControl at href %s for individual access", dderc.href)

    return derp, dderc


def initialize_2030_5(config: ServerConfiguration, tlsrepo: TLSRepository):
    """Initialize the 2030.5 server with thread safety.
    This method initializes the adapters from the configuration objects into
    the persistence adapters.
    """
    # Connect event handlers to TimeAdapter signals
    adpt.TimeAdapter.event_started.connect(update_active_der_event_started)
    adpt.TimeAdapter.event_ended.connect(update_active_der_event_ended)

    _log.debug("Initializing 2030.5 with thread safety")
    _log.debug("Adding server level urls to cache")

    # Configure all poll rates from config
    adpt.configure_poll_rates(config)

    # Clear storage if requested
    if config.cleanse_storage:
        with atomic_operation():
            adpt.clear_all_adapters()

    programs_by_description = {}

    # Initialize DER program list
    adpt.ListAdapter.initialize_uri(hrefs.DEFAULT_DERP_ROOT, m.DERProgram)

    # Create default FSA with default program if configured
    # Note: Device-specific FSAs are now created per-device in add_enddevice()
    # No longer creating a shared global FSA

    # Add default program to shared /derp list if configured
    # Note: This is a utility-wide shared program list; devices now have their own device-specific programs in FSAs
    if config.default_program:
        import copy

        with atomic_operation():
            index = adpt.ListAdapter.get_list_size(hrefs.DEFAULT_DERP_ROOT)
            # IMPORTANT: Make a copy to avoid reusing the same mRID
            derp = copy.deepcopy(config.default_program)

            # Always generate a new unique mRID for this copy
            derp.mRID = adpt.get_global_mrids().new_mrid()

            result = adpt.ListAdapter.append(hrefs.DEFAULT_DERP_ROOT, derp)
            if not result.success:
                raise Exception(f"Failed to add default program: {result.error}")
            derp = result.data

            program_hrefs = hrefs.DERProgramHref(index)
            derp.href = program_hrefs._root
            derp.ActiveDERControlListLink = m.ActiveDERControlListLink(program_hrefs.active_control_href)
            derp.DefaultDERControlLink = m.DefaultDERControlLink(program_hrefs.default_control_href)
            derp.DERControlListLink = m.DERControlListLink(program_hrefs.der_control_list_href)

            # Add default DER control if configured
            if config.default_der_control:
                # IMPORTANT: Make a copy to avoid reusing the same mRID
                dderc = copy.deepcopy(config.default_der_control)
                dderc.mRID = adpt.get_global_mrids().new_mrid()
                dderc.href = derp.DefaultDERControlLink.href
                adpt.ListAdapter.set_single(uri=derp.DefaultDERControlLink.href, obj=dderc)

            # Controls if there are any should be added to this list
            adpt.ListAdapter.initialize_uri(derp.DERControlListLink.href, m.DERControl)

    # Add configured programs
    for index, program_cfg in enumerate(config.programs):
        with atomic_operation():
            program_hrefs = hrefs.DERProgramHref(adpt.ListAdapter.get_list_size(hrefs.DEFAULT_DERP_ROOT))

            # Pop off default_der_control if specified
            default_der_control = program_cfg.pop("DefaultDERControl", None)

            program = m.DERProgram(**program_cfg)
            if not program.mRID:
                program.mRID = adpt.get_global_mrids().new_mrid()

            program = program_hrefs.fill_hrefs(program)

            result = adpt.ListAdapter.append(hrefs.DEFAULT_DERP_ROOT, program)
            if not result.success:
                raise Exception(f"Failed to add program: {result.error}")

            # Either set up default control or use the one passed in
            if not default_der_control:
                default_der_control = m.DefaultDERControl(
                    href=program_hrefs.default_control_href,
                    mRID=adpt.get_global_mrids().new_mrid(),
                    DERControlBase=m.DERControlBase(),
                )
            elif default_der_control:
                der_control_base = None
                if "DERControlBase" in default_der_control:
                    der_control_base = default_der_control.pop("DERControlBase")

                default_der_control = m.DefaultDERControl(
                    href=program.DefaultDERControlLink.href, **default_der_control
                )

                if not default_der_control.mRID:
                    default_der_control.mRID = adpt.get_global_mrids().new_mrid()

                if not der_control_base:
                    default_der_control.DERControlBase = m.DERControlBase()
                else:
                    default_der_control.DERControlBase = m.DERControlBase(**der_control_base)

            adpt.ListAdapter.initialize_uri(program.DERControlListLink.href, m.DERControl)

            # Store objects for retrieval - links first, then program
            add_href(program.DefaultDERControlLink.href, default_der_control)
            add_href(program.ActiveDERControlListLink.href, m.DERControlList(DERControl=[]))
            add_href(program.DERCurveListLink.href, m.DERCurveList(DERCurve=[]))
            add_href(program.DERControlListLink.href, m.DERControlList(DERControl=[]))

            # Store the program itself AFTER all its links are populated
            add_href(program.href, program)

            programs_by_description[program.description] = program

    # Add DER curves
    adpt.ListAdapter.initialize_uri(hrefs.DEFAULT_CURVE_ROOT, m.DERCurve)

    for index, curve_cfg in enumerate(config.curves):
        curve = m.DERCurve(href=hrefs.SEP.join([hrefs.DEFAULT_CURVE_ROOT, str(index)]), **curve_cfg)

        if not curve.mRID:
            curve.mRID = adpt.get_global_mrids().new_mrid()
            _log.debug(
                "Generated new mRID for curve: %s",
                curve.mRID.hex() if isinstance(curve.mRID, bytes) else curve.mRID,
            )

        result = adpt.ListAdapter.append(hrefs.DEFAULT_CURVE_ROOT, curve)
        if not result.success:
            raise Exception(f"Failed to add curve {index}: {result.error}")

        # Register with GlobalmRIDs for cross-reference lookups
        adpt.get_global_mrids().add_item_with_mrid(curve.href, curve)

    # Add devices
    import time

    device_start_time = time.time()
    _log.info(f"Starting device initialization for {len(config.devices)} devices at {time.strftime('%H:%M:%S')}")
    _log.warning("DEBUG LEVEL CHECK: Starting device processing loop")

    # Temporarily reduce logging verbosity during device initialization for performance
    import logging

    sql_logger = logging.getLogger("ieee_2030_5.persistance.sqlite_store")
    original_level = sql_logger.level
    bulk_init_threshold = getattr(config, "bulk_device_init_threshold", None)
    bulk_init_log_level = getattr(config, "bulk_device_init_log_level", None)
    if bulk_init_threshold is not None and bulk_init_log_level is not None:
        if len(config.devices) > bulk_init_threshold:
            sql_logger.setLevel(bulk_init_log_level)
            _log.info(
                f"Reduced database logging verbosity to {logging.getLevelName(bulk_init_log_level)} "
                f"for bulk device initialization performance (threshold: {bulk_init_threshold})"
            )

    try:
        _log.warning(f"TRACE: About to start device loop with {len(config.devices)} devices")
        for enum_index, cfg_device in enumerate(config.devices):
            _log.warning(f"TRACE: Loop iteration {enum_index}, device: {cfg_device.id}")
            if enum_index % 20 == 0:  # Log every 20 devices instead of 50
                _log.info(f"Processing device {enum_index + 1}/{len(config.devices)}: {cfg_device.id}")

            _log.debug(f"TRACE: Processing individual device {cfg_device.id}, index {enum_index}")
            # Generate stable device index using existing function
            if cfg_device.id:
                device_index = hrefs.get_device_hashed_index(cfg_device.id)
                _log.warning(f"TRACE: Generated device_index {device_index} for device {cfg_device.id}")
            else:
                raise ValueError(f"device_id is required for device {enum_index}. Cannot create stable device index.")

            _log.warning(f"TRACE: About to create device capability for device {cfg_device.id}")
            create_device_capability(device_index, cfg_device, config)
            ed_href = hrefs.EndDeviceHref(device_index)
            _log.warning(f"TRACE: Created ed_href {ed_href} for device {cfg_device.id}")

            # Check if device already exists
            _log.debug(f"TRACE: Checking if device {cfg_device.id} exists at href {ed_href}")
            existing_device = adpt.EndDeviceAdapter.fetch_by_href(str(ed_href))
            _log.debug(f"TRACE: Device {cfg_device.id} existing_device result: {existing_device is not None}")

            if existing_device is not None:
                _log.warning(f"End device {cfg_device.id} already exists. Updating lfdi, sfdi, and postRate.")
                existing_device.lFDI = tlsrepo.lfdi(cfg_device.id)
                existing_device.sFDI = tlsrepo.sfdi(cfg_device.id)
                existing_device.postRate = cfg_device.post_rate

                # Link existing device to default FSA if available
                if default_fsa:
                    ed_href = hrefs.EndDeviceHref(device_index)
                    # Initialize FSA list if needed
                    # Create device-specific FSA
                    fsa = create_device_fsa_with_program(existing_device.href, config)
                    if fsa:
                        list_size = adpt.ListAdapter.get_list_size(ed_href.function_set_assignments)
                        existing_device.FunctionSetAssignmentsListLink = m.FunctionSetAssignmentsListLink(
                            href=ed_href.function_set_assignments,
                            all=list_size,
                        )
                        _log.info(
                            "Created device-specific FSA for device %s at %s (count=%d)",
                            cfg_device.id,
                            fsa.href,
                            list_size,
                        )

                        # Persist the updated device with FSA link using direct database access
                        device_key = f"enddevice:{device_index}"
                        import pickle

                        with atomic_operation():
                            adpt.EndDeviceAdapter._db.set_point(device_key, pickle.dumps(existing_device))
                            add_href(existing_device.href, existing_device)
                        _log.debug("Persisted existing device %s with FSA link", existing_device.href)

                # Ensure device is registered in GlobalMRIDs even for existing devices
                _log.debug("Registering existing device %s in GlobalMRIDs", cfg_device.id)
                # Note: EndDevices are stored at enddevice:{index}, not at their href
                device_key = f"enddevice:{device_index}"

                # Register the EndDevice's mRID to point to its actual storage location
                if hasattr(existing_device, "mRID") and existing_device.mRID:
                    adpt.get_global_mrids().register_mrid(existing_device.mRID, device_key, "EndDevice")
                    _log.debug(
                        "Registered existing EndDevice mRID %s -> %s",
                        existing_device.mRID,
                        device_key,
                    )

                # Also register by device ID (equipment mRID from GridAPPS-D)
                adpt.get_global_mrids().register_mrid(cfg_device.id, device_key, "EndDevice")
                _log.debug("Registered existing device ID %s -> %s", cfg_device.id, device_key)

                # Also register by DER equipment IDs from GridAPPS-D for message mapping
                if cfg_device.ders:
                    for der_name in cfg_device.ders:
                        if der_name != cfg_device.id:  # Avoid duplicate registration
                            # Register the equipment ID -> device storage location mapping
                            adpt.get_global_mrids().register_mrid(der_name, device_key, "EndDevice")
                            _log.debug(
                                "Registered existing device %s by DER equipment ID: %s -> %s",
                                cfg_device.id,
                                der_name,
                                device_key,
                            )

                _log.debug("GlobalMRIDs now has %d entries", len(adpt.get_global_mrids()))

                # Also add the EndDevice indexed by certificate CN for GridAPPS-D compatibility
                try:
                    # Use the tlsrepo parameter instead of Flask.g to avoid context issues
                    # Get the certificate subject (CN) for this device
                    cn = tlsrepo.get_common_name(cfg_device.id)
                    if cn and hasattr(cn, "CN"):
                        cert_cn = cn.CN  # Extract the CN field
                        # Also index by certificate CN -> device storage location
                        adpt.get_global_mrids().register_mrid(cert_cn, device_key, "EndDevice")
                        _log.debug("Added EndDevice mapping: CN '%s' -> %s", cert_cn, device_key)
                except Exception as e:
                    _log.warning("Could not add certificate CN mapping for device %s: %s", cfg_device.id, e)
                    # Continue without CN mapping - direct device ID lookup will still work
            else:
                _log.debug(f"Adding end device {cfg_device.id} to server")

                end_device = m.EndDevice(
                    lFDI=tlsrepo.lfdi(cfg_device.id),
                    sFDI=tlsrepo.sfdi(cfg_device.id),
                    postRate=cfg_device.post_rate,
                    enabled=True,
                    changedTime=adpt.TimeAdapter.current_tick,
                )

                end_device = add_enddevice(end_device, cfg_device.id)

                # Extract device_index from href and create ed_href for later use
                device_index = int(end_device.href.split("_")[1]) if "_" in end_device.href else None
                if device_index is None:
                    raise Exception(f"Failed to extract device_index from href {end_device.href}")

                ed_href = hrefs.EndDeviceHref(device_index)
                _log.debug(f"Created ed_href for device {cfg_device.id} at index {device_index}")

                _log.debug("Registering new device %s in GlobalMRIDs", cfg_device.id)
                # Note: EndDevices are stored at enddevice:{index}, not at their href
                # The href index is separate and points to the Index object for lookups
                device_key = f"enddevice:{device_index}"

                # Register the EndDevice's mRID to point to its actual storage location
                if hasattr(end_device, "mRID") and end_device.mRID:
                    adpt.get_global_mrids().register_mrid(end_device.mRID, device_key, "EndDevice")
                    _log.debug("Registered EndDevice mRID %s -> %s", end_device.mRID, device_key)

                # Also register by device ID (equipment mRID from GridAPPS-D)
                adpt.get_global_mrids().register_mrid(cfg_device.id, device_key, "EndDevice")
                _log.debug("Registered device ID %s -> %s", cfg_device.id, device_key)

                # Also register by DER equipment IDs from GridAPPS-D for message mapping
                if cfg_device.ders:
                    for der_name in cfg_device.ders:
                        if der_name != cfg_device.id:  # Avoid duplicate registration
                            # Register the equipment ID -> device storage location mapping
                            adpt.get_global_mrids().register_mrid(der_name, device_key, "EndDevice")
                            _log.debug(
                                "Registered device %s by DER equipment ID: %s -> %s",
                                cfg_device.id,
                                der_name,
                                device_key,
                            )

                _log.debug(f"GlobalMRIDs now has {len(adpt.get_global_mrids())} entries")

                # Also add the EndDevice indexed by certificate CN for GridAPPS-D compatibility
                try:
                    # Use the tlsrepo parameter instead of Flask.g to avoid context issues
                    # Get the certificate subject (CN) for this device
                    cn = tlsrepo.get_common_name(cfg_device.id)
                    if cn and hasattr(cn, "CN"):
                        cert_cn = cn.CN  # Extract the CN field
                        # Also index by certificate CN -> device storage location
                        adpt.get_global_mrids().register_mrid(cert_cn, device_key, "EndDevice")
                        _log.debug("Added EndDevice mapping: CN '%s' -> %s", cert_cn, device_key)
                except Exception as e:
                    _log.warning("Could not add certificate CN mapping for device %s: %s", cfg_device.id, e)
                    # Continue without CN mapping - direct device ID lookup will still work

                # Add registration
                reg = m.Registration(
                    href=end_device.RegistrationLink.href,
                    pIN=cfg_device.pin,
                    pollRate=cfg_device.poll_rate,
                    dateTimeRegistered=adpt.TimeAdapter.current_tick,
                )

                adpt.ListAdapter.set_single(uri=reg.href, obj=reg)
                add_href(reg.href, reg)

                # Initialize DER and FSA lists
                adpt.ListAdapter.initialize_uri(ed_href.der_list, m.DER)
                adpt.ListAdapter.initialize_uri(ed_href.function_set_assignments, m.FunctionSetAssignments)

                # Handle FSAs
                fsa_linked = False

                # Create device-specific FSA for this device
                fsa = create_device_fsa_with_program(end_device.href, config)
                device_specific_program_href = None
                if fsa:
                    fsa_linked = True
                    # The device-specific program is at {fsa_href}/derp/0
                    device_specific_program_href = hrefs.SEP.join((fsa.href, "derp", "0"))
                    _log.info(
                        "Device %s created with device-specific FSA at %s with program at %s (%d FSA(s))",
                        cfg_device.id,
                        fsa.href,
                        device_specific_program_href,
                        adpt.ListAdapter.get_list_size(ed_href.function_set_assignments),
                    )

                # Handle additional device-specific FSAs from config if specified
                if cfg_device.fsas:
                    for fsa_name in cfg_device.fsas:
                        fsa_index = adpt.ListAdapter.get_list_size(ed_href.function_set_assignments)
                        fsa = m.FunctionSetAssignments(
                            href=hrefs.SEP.join((ed_href.function_set_assignments, str(fsa_index))),
                            mRID=adpt.get_global_mrids().new_mrid(),
                            description=fsa_name,
                        )

                        result = adpt.ListAdapter.append(ed_href.function_set_assignments, fsa)
                        if not result.success:
                            raise Exception(f"Failed to add FSA {fsa_name}: {result.error}")
                        fsa_linked = True
                        _log.info(f"Added device-specific FSA '{fsa_name}' for device {cfg_device.id}")

                # Update link to FSA list if any FSAs were added
                if fsa_linked:
                    list_size = adpt.ListAdapter.get_list_size(ed_href.function_set_assignments)
                    end_device.FunctionSetAssignmentsListLink = m.FunctionSetAssignmentsListLink(
                        href=ed_href.function_set_assignments,
                        all=list_size,
                    )
                    _log.debug(
                        "Updated EndDevice FSA link: href=%s, all=%d",
                        ed_href.function_set_assignments,
                        list_size,
                    )

                    # IMPORTANT: Persist the updated EndDevice with the FSA link
                    # Use direct database access like add_enddevice() does
                    device_key = f"enddevice:{device_index}"
                    import pickle

                    with atomic_operation():
                        adpt.EndDeviceAdapter._db.set_point(device_key, pickle.dumps(end_device))
                        # Also update the href cache
                        add_href(end_device.href, end_device)
                    _log.debug("Persisted EndDevice %s with FSA link count=%d", end_device.href, list_size)

                # Handle DERs
                _log.debug(
                    "Device %s has ders: %s, type: %s",
                    cfg_device.id,
                    cfg_device.ders,
                    type(cfg_device.ders),
                )
                if cfg_device.ders:
                    # Create DER objects for each configured DER
                    for der_index, der in enumerate(cfg_device.ders):
                        with atomic_operation():
                            # Create DER object with device-scoped href
                            der_href_path = hrefs.SEP.join([str(device_index), "der", str(der_index)])
                            der_href = hrefs.DERHref(hrefs.SEP.join([hrefs.DEFAULT_DER_ROOT, der_href_path]))

                            der_obj = m.DER(
                                href=der_href.root,
                                DERStatusLink=m.DERStatusLink(der_href.der_status),
                                DERSettingsLink=m.DERSettingsLink(der_href.der_settings),
                                DERCapabilityLink=m.DERCapabilityLink(der_href.der_capability),
                                DERAvailabilityLink=m.DERAvailabilityLink(der_href.der_availability),
                            )

                            # Find the device-specific program with minimum primacy from the device's FSAs
                            # Since we created a device-specific FSA earlier, use that program
                            fsa_list = adpt.ListAdapter.get_list(ed_href.function_set_assignments)
                            if not fsa_list:
                                _log.warning(
                                    "No FSA found for device %s - DER will not have a program",
                                    cfg_device.id,
                                )
                            else:
                                _log.debug(
                                    "Device %s has %d FSA(s) available",
                                    cfg_device.id,
                                    len(fsa_list),
                                )

                                # Find program with minimum primacy from device's FSAs
                                try:
                                    current_min_primacy = 10000
                                    current_der_program = None

                                    for fsa in fsa_list:
                                        if not hasattr(fsa, "DERProgramListLink") or not fsa.DERProgramListLink:
                                            _log.debug(
                                                "FSA %s has no DERProgramListLink",
                                                fsa.href if hasattr(fsa, "href") else "unknown",
                                            )
                                            continue

                                        fsa_programs = adpt.ListAdapter.get_list(fsa.DERProgramListLink.href)
                                        for der_program in fsa_programs:
                                            if not der_program:
                                                continue

                                            if current_der_program is None:
                                                current_der_program = der_program

                                            if (
                                                hasattr(der_program, "primacy")
                                                and der_program.primacy < current_min_primacy
                                            ):
                                                current_min_primacy = der_program.primacy
                                                current_der_program = der_program

                                    if current_der_program:
                                        der_obj.CurrentDERProgramLink = m.CurrentDERProgramLink(
                                            current_der_program.href
                                        )
                                        _log.info(
                                            "Set DER %s CurrentDERProgramLink to device-specific program %s",
                                            der_obj.href,
                                            current_der_program.href,
                                        )
                                    else:
                                        _log.warning(
                                            "No program with minimum primacy found for DER %s",
                                            der_obj.href,
                                        )

                                except Exception as e:
                                    _log.warning("Error finding program with minimum primacy: %s", e)

                            # Add DER to device
                            result = adpt.ListAdapter.append(ed_href.der_list, der_obj)
                            if not result.success:
                                raise Exception("Failed to add DER to device: %s" % result.error)

                            # Store DER in href indexer for individual access
                            add_href(der_obj.href, der_obj)
                            _log.debug("Stored DER at href %s for individual access", der_obj.href)

                # Handle default DER on all devices if configured
                elif config.include_default_der_on_all_devices:
                    _log.debug(f"Device {cfg_device.id} using default DER path (no explicit ders configured)")
                    with atomic_operation():
                        if not config.default_program:
                            raise ConfigurationError(
                                "Must include default_program if include_default_der_on_all_devices is set!"
                            )

                        # Create default DER with device-scoped href (index 0 since it's the only DER)
                        der_href_path = hrefs.SEP.join([str(device_index), "der", "0"])
                        der_href = hrefs.DERHref(hrefs.SEP.join([hrefs.DEFAULT_DER_ROOT, der_href_path]))

                        der_obj = m.DER(
                            href=der_href.root,
                            DERStatusLink=m.DERStatusLink(der_href.der_status),
                            DERSettingsLink=m.DERSettingsLink(der_href.der_settings),
                            DERCapabilityLink=m.DERCapabilityLink(der_href.der_capability),
                            DERAvailabilityLink=m.DERAvailabilityLink(der_href.der_availability),
                        )

                        # Point to the device-specific program, not the shared program
                        if device_specific_program_href:
                            der_obj.CurrentDERProgramLink = m.CurrentDERProgramLink(device_specific_program_href)
                        else:
                            # Fallback to shared program if no device-specific program exists
                            der_obj.CurrentDERProgramLink = m.CurrentDERProgramLink(config.default_program.href)
                            _log.warning(
                                "No device-specific program found for device %s, using shared program",
                                cfg_device.id,
                            )

                        result = adpt.ListAdapter.append(ed_href.der_list, der_obj)
                        if not result.success:
                            raise Exception(f"Failed to add default DER to device: {result.error}")
    finally:
        # Restore original logging level
        sql_logger.setLevel(original_level)
        _log.info("DEBUG: Finally block executing...")

        # Simple test first
        _log.info("DEBUG: Testing basic adapter access...")
        try:
            _log.info(f"DEBUG: adpt type: {type(adpt)}")
            _log.info(f"DEBUG: global_mrids type: {type(adpt.get_global_mrids())}")
        except Exception as e:
            _log.error(f"DEBUG: Basic adapter test failed: {e}")

        device_end_time = time.time()
        device_duration = device_end_time - device_start_time

        # Output all known mRIDs for debugging
        _log.info("=" * 80)
        _log.info("KNOWN mRIDs IN SYSTEM AFTER INITIALIZATION:")
        _log.info("=" * 80)
        try:
            known_mrids = adpt.get_global_mrids().list_all_known_mrids()
            _log.info("DEBUG: Successfully got mRID list")
        except Exception as e:
            _log.error(f"DEBUG: Failed to get mRID list: {e}")
            known_mrids = {}
        if known_mrids:
            for mrid, location in sorted(known_mrids.items()):
                _log.info(f"  {mrid} -> {location}")
            _log.info(f"Total registered mRIDs: {len(known_mrids)}")

            # Quick test of specific mRIDs right here
            _log.info("DEBUG: Quick test of problem mRIDs...")
            for test_mrid in [
                "_CA0A0024-DA79-4395-9B05-6A7B9DE0AED9",
                "_EB6BC0A1-FA4B-46CE-B26E-DD022AB62595",
            ]:
                if test_mrid in known_mrids:
                    _log.info(f"DEBUG: {test_mrid} IS in registry -> {known_mrids[test_mrid]}")
                else:
                    _log.error(f"DEBUG: {test_mrid} NOT in registry!")

        else:
            _log.warning("NO mRIDs found in registry - this indicates initialization problems!")
        _log.info("=" * 80)

        # Simple test to ensure this code executes
        _log.info("DEBUG: About to start mRID lookup testing...")

        # DEBUG: Test mRID lookup directly without creating new adapter
        _log.info("DEBUG: Testing mRID lookup for known equipment...")
        try:
            test_mrids = [
                "_CA0A0024-DA79-4395-9B05-6A7B9DE0AED9",
                "_EB6BC0A1-FA4B-46CE-B26E-DD022AB62595",
            ]

            for test_mrid in test_mrids:
                _log.info(f"DEBUG: Testing lookup for {test_mrid}")

                # Test GlobalMRIDs.get_location()
                location = adpt.get_global_mrids().get_location(test_mrid)
                _log.info(f"DEBUG: get_location('{test_mrid}') = {location}")

                # Test direct database lookup
                mrid_key = f"mrid:{test_mrid}"
                direct_data = adpt.get_list_adapter()._db.get_point(mrid_key)
                if direct_data:
                    try:
                        decoded = direct_data.decode("utf-8")
                        _log.info(f"DEBUG: Direct DB lookup '{mrid_key}' = '{decoded}'")
                    except UnicodeDecodeError:
                        _log.error(f"DEBUG: Direct DB lookup '{mrid_key}' = BINARY_DATA (len={len(direct_data)})")
                else:
                    _log.info(f"DEBUG: Direct DB lookup '{mrid_key}' = NOT_FOUND")

                # Test GlobalMRIDs.get_item()
                if location:
                    item = adpt.get_global_mrids().get_item(test_mrid)
                    _log.info(
                        f"DEBUG: get_item('{test_mrid}') = {type(item)} {getattr(item, 'href', 'NO_HREF') if item else 'None'}"
                    )

                _log.info(f"DEBUG: --- End test for {test_mrid} ---")

        except Exception as e:
            _log.error(f"DEBUG: mRID lookup test failed: {e}")
            import traceback

            _log.error(f"DEBUG: Traceback: {traceback.format_exc()}")

        # _log.info(f"Device initialization completed in {device_duration:.2f} seconds at {time.strftime('%H:%M:%S')}")

    # Display all resources for debugging
    # if hasattr(adpt.ListAdapter, "print_all") and callable(adpt.ListAdapter.print_all):
    #     adpt.ListAdapter.print_all()
    # else:
    #     _log.debug("ListAdapter.print_all method not available")

    # _log.info("Thread-safe 2030.5 initialization completed")
