# ieee_2030_5/server/server_constructs.py
from __future__ import annotations
import logging
from blinker import Signal
from ieee_2030_5.certs import TLSRepository, lfdi_from_fingerprint
from ieee_2030_5.config import ServerConfiguration, DeviceConfiguration
from ieee_2030_5.data.indexer import add_href, get_href
from ieee_2030_5.persistance.points import atomic_operation

_log = logging.getLogger(__name__)
import ieee_2030_5.adapters as adpt
import ieee_2030_5.hrefs as hrefs
import ieee_2030_5.models as m


# Define ConfigurationError here since it's not in ieee_2030_5.config
class ConfigurationError(Exception):
    """Exception raised for configuration errors."""
    pass


def create_device_capability(end_device_index: int,
                             device_cfg: DeviceConfiguration) -> m.DeviceCapability:
    """Create a device capability object for the passed device index
    This function does not verify that there is a device at the passed index.
    """
    dcap_href = hrefs.DeviceCapabilityHref(end_device_index)
    device_capability = m.DeviceCapability()
    device_capability = dcap_href.fill_hrefs(device_capability)
    device_capability.MirrorUsagePointListLink = m.MirrorUsagePointListLink(
        href=hrefs.DEFAULT_MUP_ROOT, all=0)
    device_capability.TimeLink = m.TimeLink(href=hrefs.DEFAULT_TIME_ROOT)
    device_capability.UsagePointListLink = m.UsagePointListLink(href=hrefs.DEFAULT_UPT_ROOT, all=0)

    # Use thread-safe append instead of add
    device_capability_adapter = adpt._get_or_create_adapter('DeviceCapability', m.DeviceCapability)
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
    device.MirrorUsagePointListLink = m.MirrorUsagePointListLink(href=hrefs.DEFAULT_MUP_ROOT,
                                                                 all=0)
    device.UsagePointListLink = m.UsagePointListLink(href=hrefs.DEFAULT_UPT_ROOT, all=0)

    # Initialize list URIs
    adpt.ListAdapter.initialize_uri(hrefs.DEFAULT_MUP_ROOT, m.MirrorUsagePoint)
    adpt.ListAdapter.initialize_uri(hrefs.DEFAULT_UPT_ROOT, m.UsagePoint)
    adpt.ListAdapter.initialize_uri(ed_href.der_list, m.DER)
    adpt.ListAdapter.initialize_uri(ed_href.function_set_assignments, m.FunctionSetAssignments)

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


def create_der_program_and_control(default_der_program: m.DERProgram,
                                   default_der_control: m.DefaultDERControl,
                                   name: str) -> [m.DERProgram, m.DefaultDERControl]:
    """
    Create a new DERProgram based upon the default derp control
    """
    from copy import deepcopy

    # Get current list size for index
    derp_index = adpt.ListAdapter.get_list_size(hrefs.DEFAULT_DERP_ROOT)

    # Prepare objects
    derp = deepcopy(default_der_program)
    dderc = deepcopy(default_der_control)
    derp.mRID = adpt.get_global_mrids().new_mrid()
    dderc.mRID = adpt.get_global_mrids().new_mrid()

    # Use thread-safe append
    result = adpt.ListAdapter.append(hrefs.DEFAULT_DERP_ROOT, derp)
    if not result.success:
        raise Exception(f"Failed to add DER program: {result.error}")
    derp = result.data

    # Set up hrefs
    program_hrefs = hrefs.DERProgramHref(derp_index)
    derp.href = program_hrefs._root
    derp.ActiveDERControlListLink = m.ActiveDERControlListLink(program_hrefs.active_control_href)
    derp.DefaultDERControlLink = m.DefaultDERControlLink(program_hrefs.default_control_href)
    derp.DERControlListLink = m.DERControlListLink(program_hrefs.der_control_list_href)
    derp.DERCurveListLink = m.DERCurveListLink(program_hrefs.der_curve_list_href)
    dderc.href = derp.DefaultDERControlLink.href

    # Initialize curve list
    adpt.ListAdapter.initialize_uri(program_hrefs.der_curve_list_href, m.DERCurve)

    # Add default control
    result = adpt.ListAdapter.append(hrefs.DEFAULT_DDERC_ROOT, dderc)
    if not result.success:
        raise Exception(f"Failed to add default DER control: {result.error}")
    dderc = result.data

    # Update program with links
    result = adpt.ListAdapter.append(hrefs.DEFAULT_DERP_ROOT, derp)
    if not result.success:
        raise Exception(f"Failed to update DER program: {result.error}")
    derp = result.data

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

    end_device_ders = {}

    # Clear storage if requested
    if config.cleanse_storage:
        with atomic_operation():
            adpt.clear_all_adapters()

    programs_by_description = {}

    # Initialize DER program list
    adpt.ListAdapter.initialize_uri(hrefs.DEFAULT_DERP_ROOT, m.DERProgram)

    # Add default program if configured
    if config.default_program:
        with atomic_operation():
            index = adpt.ListAdapter.get_list_size(hrefs.DEFAULT_DERP_ROOT)
            derp = config.default_program

            if not derp.mRID:
                derp.mRID = adpt.get_global_mrids().new_mrid()

            result = adpt.ListAdapter.append(hrefs.DEFAULT_DERP_ROOT, derp)
            if not result.success:
                raise Exception(f"Failed to add default program: {result.error}")
            derp = result.data

            program_hrefs = hrefs.DERProgramHref(index)
            derp.href = program_hrefs._root
            derp.ActiveDERControlListLink = m.ActiveDERControlListLink(
                program_hrefs.active_control_href)
            derp.DefaultDERControlLink = m.DefaultDERControlLink(
                program_hrefs.default_control_href)
            derp.DERControlListLink = m.DERControlListLink(program_hrefs.der_control_list_href)

            # Add default DER control if configured
            if config.default_der_control:
                dderc = config.default_der_control
                dderc.mRID = adpt.get_global_mrids().new_mrid()
                dderc.href = derp.DefaultDERControlLink.href
                adpt.ListAdapter.set_single(uri=derp.DefaultDERControlLink.href, obj=dderc)

            # Controls if there are any should be added to this list
            adpt.ListAdapter.initialize_uri(derp.DERControlListLink.href, m.DERControl)

    # Add configured programs
    for index, program_cfg in enumerate(config.programs):
        with atomic_operation():
            program_hrefs = hrefs.DERProgramHref(
                adpt.ListAdapter.get_list_size(hrefs.DEFAULT_DERP_ROOT))

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
                default_der_control = m.DefaultDERControl(href=program_hrefs.default_control_href,
                                                          mRID=adpt.get_global_mrids().new_mrid(),
                                                          DERControlBase=m.DERControlBase())
            elif default_der_control:
                der_control_base = None
                if "DERControlBase" in default_der_control:
                    der_control_base = default_der_control.pop("DERControlBase")

                default_der_control = m.DefaultDERControl(href=program.DefaultDERControlLink.href,
                                                          **default_der_control)

                if not default_der_control.mRID:
                    default_der_control.mRID = adpt.get_global_mrids().new_mrid()

                if not der_control_base:
                    default_der_control.DERControlBase = m.DERControlBase()
                else:
                    default_der_control.DERControlBase = m.DERControlBase(**der_control_base)

            adpt.ListAdapter.initialize_uri(program.DERControlListLink.href, m.DERControl)

            # Store objects for retrieval
            add_href(program.DefaultDERControlLink.href, default_der_control)
            add_href(program.ActiveDERControlListLink.href, m.DERControlList(DERControl=[]))
            add_href(program.DERCurveListLink.href, m.DERCurveList(DERCurve=[]))
            add_href(program.DERControlListLink.href, m.DERControlList(DERControl=[]))

            programs_by_description[program.description] = program

    # Add DER curves
    adpt.ListAdapter.initialize_uri(hrefs.DEFAULT_CURVE_ROOT, m.DERCurve)

    for index, curve_cfg in enumerate(config.curves):
        curve = m.DERCurve(href=hrefs.SEP.join([hrefs.DEFAULT_CURVE_ROOT,
                                                str(index)]),
                           **curve_cfg)

        if not curve.mRID:
            curve.mRID = adpt.get_global_mrids().new_mrid()

        result = adpt.ListAdapter.append(hrefs.DEFAULT_CURVE_ROOT, curve)
        if not result.success:
            raise Exception(f"Failed to add curve {index}: {result.error}")

    # Add devices

    for enum_index, cfg_device in enumerate(config.devices):
        try:
            # Generate stable device index from device_id (same logic as in EndDeviceAdapter.add)
            if cfg_device.id:
                import hashlib
                hash_obj = hashlib.sha256(cfg_device.id.encode('utf-8'))
                device_index = int(hash_obj.hexdigest()[:8], 16) % 100000  # Limit to 5 digits
            else:
                raise ValueError(f"device_id is required for device {enum_index}. Cannot create stable device index.")
            
            device_capability = create_device_capability(device_index, cfg_device)
            ed_href = hrefs.EndDeviceHref(device_index)

            # Check if device already exists
            existing_device = adpt.EndDeviceAdapter.fetch_by_href(str(ed_href))

            if existing_device is not None:
                _log.warning(
                    f"End device {cfg_device.id} already exists. Updating lfdi, sfdi, and postRate."
                )
                existing_device.lFDI = tlsrepo.lfdi(cfg_device.id)
                existing_device.sFDI = tlsrepo.sfdi(cfg_device.id)
                existing_device.postRate = cfg_device.post_rate

                result = adpt.EndDeviceAdapter.put(device_index, existing_device)
                if not result.success:
                    raise Exception(f"Failed to update device {cfg_device.id}: {result.error}")
            else:
                _log.debug(f"Adding end device {cfg_device.id} to server")

                end_device = m.EndDevice(lFDI=tlsrepo.lfdi(cfg_device.id),
                                         sFDI=tlsrepo.sfdi(cfg_device.id),
                                         postRate=cfg_device.post_rate,
                                         enabled=True,
                                         changedTime=adpt.TimeAdapter.current_tick)

                end_device = add_enddevice(end_device, cfg_device.id)
                adpt.get_global_mrids().add_item_with_mrid(cfg_device.id, end_device)

                # Add registration
                reg = m.Registration(href=end_device.RegistrationLink.href,
                                     pIN=cfg_device.pin,
                                     pollRate=cfg_device.poll_rate,
                                     dateTimeRegistered=adpt.TimeAdapter.current_tick)

                adpt.ListAdapter.set_single(uri=reg.href, obj=reg)
                add_href(reg.href, reg)

                # Initialize DER and FSA lists
                adpt.ListAdapter.initialize_uri(ed_href.der_list, m.DER)
                adpt.ListAdapter.initialize_uri(ed_href.function_set_assignments,
                                                m.FunctionSetAssignments)

                # Handle FSAs
                if cfg_device.fsas:
                    for fsa_name in cfg_device.fsas:
                        fsa_index = adpt.ListAdapter.get_list_size(
                            ed_href.function_set_assignments)
                        fsa = m.FunctionSetAssignments(href=hrefs.SEP.join(
                            (ed_href.function_set_assignments, str(fsa_index))),
                                                       mRID=adpt.get_global_mrids().new_mrid(),
                                                       description=fsa_name)

                        result = adpt.ListAdapter.append(ed_href.function_set_assignments, fsa)
                        if not result.success:
                            raise Exception(f"Failed to add FSA {fsa_name}: {result.error}")

                    # Update link to FSA list
                    end_device.FunctionSetAssignmentsListLink = m.FunctionSetAssignmentsListLink(
                        href=ed_href.function_set_assignments,
                        all=adpt.ListAdapter.get_list_size(ed_href.function_set_assignments),
                    )

                # Handle DERs
                _log.debug(f"Device {cfg_device.id} has ders: {cfg_device.ders}, type: {type(cfg_device.ders)}")
                if cfg_device.ders:
                    # Create references from the main der list to the ed specific list.
                    for der_index, der in enumerate(cfg_device.ders):
                        with atomic_operation():
                            # Create DER object with device-scoped href
                            der_href_path = hrefs.SEP.join([str(device_index), "der", str(der_index)])
                            der_href = hrefs.DERHref(
                                hrefs.SEP.join([hrefs.DEFAULT_DER_ROOT, der_href_path]))

                            der_obj = m.DER(
                                href=der_href.root,
                                DERStatusLink=m.DERStatusLink(der_href.der_status),
                                DERSettingsLink=m.DERSettingsLink(der_href.der_settings),
                                DERCapabilityLink=m.DERCapabilityLink(der_href.der_capability),
                                DERAvailabilityLink=m.DERAvailabilityLink(
                                    der_href.der_availability))

                            # Create program and control
                            derp, dderc = create_der_program_and_control(
                                default_der_program=config.default_program,
                                default_der_control=config.default_der_control,
                                name=f"{der} Program")

                            der_obj.CurrentDERProgramLink = m.DERProgramLink(derp.href)

                            # Add DER to device
                            result = adpt.ListAdapter.append(ed_href.der_list, der_obj)
                            if not result.success:
                                raise Exception(f"Failed to add DER to device: {result.error}")

                            # Save default DER control
                            adpt.ListAdapter.set_single(obj=dderc, uri=dderc.href)

                            # Initialize DER control list
                            derp_derc_list_href = hrefs.SEP.join((derp.href, "derc"))
                            adpt.ListAdapter.initialize_uri(list_uri=derp_derc_list_href,
                                                            obj=m.DERControl)

                            # Handle FSAs for this DER
                            fsa_list = adpt.ListAdapter.get_list(ed_href.function_set_assignments)
                            if fsa_list:
                                # Create a new der program for this specific fsa
                                fsa = fsa_list[0]
                                derp_fsa_href = hrefs.SEP.join((fsa.href, "derp"))
                                adpt.ListAdapter.initialize_uri(list_uri=derp_fsa_href,
                                                                obj=m.DERProgram)

                                result = adpt.ListAdapter.append(list_uri=derp_fsa_href, obj=derp)
                                if not result.success:
                                    raise Exception(
                                        f"Failed to add program to FSA: {result.error}")

                                fsa.DERProgramListLink = m.DERProgramListLink(
                                    href=derp_fsa_href,
                                    all=adpt.ListAdapter.get_list_size(derp_fsa_href))

                            # Find program with minimum primacy
                            # In the try block where we find the program with minimum primacy
                            try:
                                current_min_primacy = 10000
                                current_der_program = None

                                for fsa in adpt.ListAdapter.get_list(ed_href.function_set_assignments):
                                    if not hasattr(fsa, 'DERProgramListLink') or not fsa.DERProgramListLink:
                                        _log.debug(f"FSA {fsa.href if hasattr(fsa, 'href') else 'unknown'} has no DERProgramListLink")
                                        continue

                                    fsa_programs = adpt.ListAdapter.get_list(fsa.DERProgramListLink.href)
                                    for der_program in fsa_programs:
                                        if not der_program:
                                            continue

                                        if current_der_program is None:
                                            current_der_program = der_program

                                        if hasattr(der_program, 'primacy') and der_program.primacy < current_min_primacy:
                                            current_min_primacy = der_program.primacy
                                            current_der_program = der_program

                                if current_der_program:
                                    der_obj.CurrentDERProgramLink = m.CurrentDERProgramLink(current_der_program.href)
                                else:
                                    _log.info(f"No program with minimum primacy found for DER {der_obj.href}")

                            except Exception as e:
                                _log.warning(f"Error finding program with minimum primacy: {e}")

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
                        der_href = hrefs.DERHref(
                            hrefs.SEP.join([hrefs.DEFAULT_DER_ROOT, der_href_path]))

                        der_obj = m.DER(
                            href=der_href.root,
                            DERStatusLink=m.DERStatusLink(der_href.der_status),
                            DERSettingsLink=m.DERSettingsLink(der_href.der_settings),
                            DERCapabilityLink=m.DERCapabilityLink(der_href.der_capability),
                            DERAvailabilityLink=m.DERAvailabilityLink(der_href.der_availability))

                        der_obj.CurrentDERProgramLink = m.CurrentDERProgramLink(
                            config.default_program.href)

                        result = adpt.ListAdapter.append(ed_href.der_list, der_obj)
                        if not result.success:
                            raise Exception(f"Failed to add default DER to device: {result.error}")

        except Exception as e:
            _log.error(f"Failed to process device {cfg_device.id}: {e}")
            raise

    # Display all resources for debugging
    if hasattr(adpt.ListAdapter, "print_all") and callable(adpt.ListAdapter.print_all):
        adpt.ListAdapter.print_all()
    else:
        _log.debug("ListAdapter.print_all method not available")

    _log.info("Thread-safe 2030.5 initialization completed")
