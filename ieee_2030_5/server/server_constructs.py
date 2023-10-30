from __future__ import annotations

import logging

from blinker import Signal

# from ieee_2030_5.adapters import BaseAdapter
from ieee_2030_5.certs import TLSRepository, lfdi_from_fingerprint
from ieee_2030_5.config import ServerConfiguration
from ieee_2030_5.data.indexer import add_href, get_href
from ieee_2030_5.utils.tls_wrapper import OpensslWrapper

_log = logging.getLogger(__name__)

import ieee_2030_5.adapters as adpt
import ieee_2030_5.hrefs as hrefs
import ieee_2030_5.models as m


def create_device_capability(end_device_index: int) -> m.DeviceCapability:
    """Create a device capability objecct for the passed device index

    This function does not verify that there is a device at the passed index.
    """
    dcap_href = hrefs.DeviceCapabilityHref(end_device_index)
    device_capability = m.DeviceCapability()
    device_capability = dcap_href.fill_hrefs(device_capability)

    # device_capability = m.DeviceCapability(href=str(hrefs.DERCapabilitiesHref(end_device_index)))
    # device_capability.EndDeviceListLink = m.EndDeviceListLink(href=hrefs.DEFAULT_EDEV_ROOT, all=1)
    # device_capability.DERProgramListLink = m.DERProgramListLink(href=hrefs.DEFAULT_DERP_ROOT,
    #                                                             all=0)
    device_capability.MirrorUsagePointListLink = m.MirrorUsagePointListLink(
        href=hrefs.DEFAULT_MUP_ROOT, all=0)
    device_capability.TimeLink = m.TimeLink(href=hrefs.DEFAULT_TIME_ROOT)
    device_capability.UsagePointListLink = m.UsagePointListLink(href=hrefs.DEFAULT_UPT_ROOT, all=0)

    adpt.DeviceCapabilityAdapter.add(device_capability)
    return device_capability


def add_enddevice(device: m.EndDevice) -> m.EndDevice:
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
    :return: The enddevice object that was added to the adapter
    :rtype: m.EndDevice
    """

    # After adding to the adapter the device will have an href associated with the Adapter Type.
    device = adpt.EndDeviceAdapter.add(device)

    # Create a link object that holds references for linking other objects to the end device.
    ed_href = hrefs.EndDeviceHref(edev_href=device.href)

    ed_href.fill_hrefs(device)

    # Store objects in the href cache for retrieval.
    add_href(ed_href.configuration, m.Configuration(href=device.ConfigurationLink.href))
    add_href(ed_href.device_information,
             m.DeviceInformation(href=device.DeviceInformationLink.href))
    add_href(ed_href.device_status, m.DeviceStatus(href=device.DeviceStatusLink.href))
    add_href(ed_href.power_status, m.PowerStatus(href=device.PowerStatusLink.href))

    device.MirrorUsagePointListLink = m.MirrorUsagePointListLink(href=hrefs.DEFAULT_MUP_ROOT,
                                                                 all=0)
    device.UsagePointListLink = m.UsagePointListLink(href=hrefs.DEFAULT_UPT_ROOT, all=0)
    adpt.ListAdapter.initialize_uri(hrefs.DEFAULT_MUP_ROOT, m.MirrorUsagePoint)
    adpt.ListAdapter.initialize_uri(hrefs.DEFAULT_UPT_ROOT, m.UsagePoint)

    return device


def update_active_der_event_started(event: m.Event):
    """Event triggered when a DERControl event starts
    
    Find the control and copy it to the ActiveDERControlList

    :param event: The control event
    :type event: m.Event
    """

    assert type(event) == m.DERControl

    href_parser = hrefs.HrefEventParser(event.href)

    program = adpt.ListAdapter.get(hrefs.DEFAULT_DERP_ROOT, href_parser.program_index)

    control_list: m.DERControlList = adpt.ListAdapter.get_resource_list(
        program.DERControlListLink.href)
    control = next(filter(lambda x: x.mRID == event.mRID, control_list.DERControl))
    control.EventStatus = event.EventStatus
    assert control.EventStatus.currentStatus == 1
    adpt.ListAdapter.append(program.ActiveDERControlListLink.href, control)

    add_href(control.href, control)
    add_href(event.href, event)
    add_href(control_list.href, control_list)

    activel: m.DERControlList = get_href(program.ActiveDERControlListLink.href)

    try:
        # TODO: if found deal with supersceded eventing.
        next(filter(lambda x: x.mRID == event.mRID, activel.DERControl))
    except StopIteration:
        activel.DERControl.append(event)
        add_href(program.ActiveDERControlListLink.href, activel)


def update_active_der_event_ended(event: m.Event):
    """Event triggered when a DERControl event ends
    
    Search over the ActiveDERControlListLink for the event that has been triggered
    and remove it from the list.

    :param event: The control event
    :type event: m.Event
    """
    assert type(event) == m.DERControl

    href_parser = hrefs.HrefEventParser(event.href)

    program = adpt.ListAdapter.get(hrefs.DEFAULT_DERP_ROOT, href_parser.program_index)

    control_list: m.DERControlList = adpt.ListAdapter.get_resource_list(
        program.DERControlListLink.href)
    control = next(filter(lambda x: x.mRID == event.mRID, control_list.DERControl))
    control.EventStatus = event.EventStatus
    add_href(control.href, control)
    add_href(event.href, event)
    add_href(control_list.href, control_list)

    activel: m.DERControlList = get_href(program.ActiveDERControlListLink.href)

    remove = []
    for index, ctl in enumerate(activel.DERControl):
        if ctl.mRID == event.mRID:
            if event.EventStatus.currentStatus != 1:
                remove.insert(0, index)

    for x in remove:
        activel.DERControl.pop(x)

    add_href(program.ActiveDERControlListLink.href, activel)


adpt.TimeAdapter.event_started.connect(update_active_der_event_started)
adpt.TimeAdapter.event_ended.connect(update_active_der_event_ended)


def initialize_2030_5(config: ServerConfiguration, tlsrepo: TLSRepository):
    """Initialize the 2030.5 server.  
    
    This method initializes the adapters from the configuration objects into
    the persistence adapters.
    
    The adapters are:
    
     - EndDeviceAdapter
     - DERAdapter
     - DERCurveAdapter
     - DERProgramAdapter
     - FunctionSetAssignmentsAdapter
     
    The EndDevices in the EndDeviceAdapter will link to Lists of other types.  Those
    Lists will be stored in the ListAdapter object under the List's href (see below /edev_0_der).
    As an example the following, note the DER href is not /edev_0_der_0, but /der_12 instead.
    
    <EndDevice href="/edev_0">
      <DERList href="/edev_0_der" all="1">
    </EndDevice>
    <DERList href="/edev_0_der" all="1" result="1">
      <DER href="/der_12">
        ...
      </DER>
    </DERList
        
    
    """
    _log.debug("Initializing 2030.5")
    _log.debug("Adding server level urls to cache")

    end_device_fsa = {}
    end_device_ders = {}

    if config.cleanse_storage:
        adpt.clear_all_adapters()

    programs_by_description = {}

    for index, program_cfg in enumerate(config.programs):
        program_hrefs = hrefs.DERProgramHref(index)
        # Pop off default_der_control if specified.
        default_der_control = program_cfg.pop("DefaultDERControl", None)
        program = m.DERProgram(**program_cfg)
        program = program_hrefs.fill_hrefs(program)
        adpt.ListAdapter.append(hrefs.DEFAULT_DERP_ROOT, program)

        # Either set up default control or use the one passed in.
        if not default_der_control:
            default_der_control = m.DefaultDERControl(href=program_hrefs.default_control_href,
                                                      DERControlBase=m.DERControlBase())
        elif default_der_control:
            der_control_base = None
            if "DERControlBase" in default_der_control:
                der_control_base = default_der_control.pop("DERControlBase")
            default_der_control = m.DefaultDERControl(href=program.DefaultDERControlLink.href,
                                                      **default_der_control)
            if not der_control_base:
                default_der_control.DERControlBase = m.DERControlBase()
            else:
                default_der_control.DERControlBase = m.DERControlBase(**der_control_base)
        adpt.ListAdapter.initialize_uri(program.DERControlListLink.href, m.DERControl)
        add_href(program.DefaultDERControlLink.href, default_der_control)
        add_href(program.ActiveDERControlListLink.href, m.DERControlList(DERControl=[]))

        programs_by_description[program.description] = program

    fsa_with_description = {}

    for index, fsa in enumerate(config.fsas):
        programs = fsa.pop("programs", [])
        fsa_obj = m.FunctionSetAssignments(href=hrefs.fsa_href(index), **fsa)
        der_program_link = hrefs.SEP.join([fsa_obj.href, hrefs.DER_PROGRAM])
        fsa_obj.DERProgramListLink = m.DERProgramListLink(href=der_program_link, all=len(programs))
        adpt.ListAdapter.initialize_uri(der_program_link, m.DERProgram)
        for program in programs:
            if program not in programs_by_description:
                raise ValueError(
                    f"Program {program} not found in programs list for fsa {fsa['description']}")
            adpt.ListAdapter.append(der_program_link, programs_by_description[program])
        fsa_with_description[fsa_obj.description] = fsa_obj
        # put the programs back in the config fsa.
        fsa['programs'] = programs

    # Add DERCurves to the ListAdapter under the key hrefs.DEFAULT_CURVE_ROOT.
    for index, curve_cfg in enumerate(config.curves):
        curve = m.DERCurve(href=hrefs.SEP.join([hrefs.DEFAULT_CURVE_ROOT,
                                                str(index)]),
                           **curve_cfg)
        adpt.ListAdapter.append(hrefs.DEFAULT_CURVE_ROOT, curve)

    der_global_count = 0
    for index, cfg_device in enumerate(config.devices):

        create_device_capability(index)
        ed_href = hrefs.EndDeviceHref(index)
        end_device = adpt.EndDeviceAdapter.fetch_by_href(str(ed_href))
        if end_device is not None:
            _log.warning(
                f"End device {cfg_device.id} already exists.  Updating lfdi, sfdi, and postRate.")
            end_device.lFDI = tlsrepo.lfdi(cfg_device.id)
            end_device.sFDI = tlsrepo.sfdi(cfg_device.id)
            end_device.postRate = cfg_device.post_rate
            adpt.EndDeviceAdapter.put(index, end_device)
        else:
            _log.debug(f"Adding end device {cfg_device.id} to server")
            end_device = m.EndDevice(lFDI=tlsrepo.lfdi(cfg_device.id),
                                     sFDI=tlsrepo.sfdi(cfg_device.id),
                                     postRate=cfg_device.post_rate,
                                     enabled=True,
                                     changedTime=adpt.TimeAdapter.current_tick)
            add_enddevice(end_device)
            reg = m.Registration(href=end_device.RegistrationLink.href,
                                 pIN=cfg_device.pin,
                                 pollRate=cfg_device.poll_rate,
                                 dateTimeRegistered=adpt.TimeAdapter.current_tick)
            adpt.RegistrationAdapter.add(reg)
            add_href(reg.href, reg)

            if cfg_device.fsas:
                end_device.FunctionSetAssignmentsListLink = m.FunctionSetAssignmentsListLink(
                    href=ed_href.function_set_assignments, all=len(cfg_device.fsas))
                for fsa in cfg_device.fsas:
                    adpt.ListAdapter.append(ed_href.function_set_assignments,
                                            fsa_with_description[fsa])

            # If no ders specified then we create one for the end device.
            if cfg_device.ders:
                # Create references from the main der list to the ed specific list.
                for der in cfg_device.ders:
                    der_href = hrefs.DERHref(
                        hrefs.SEP.join([hrefs.DEFAULT_DER_ROOT,
                                        str(der_global_count)]))
                    der_global_count += 1
                    der_obj = m.DER(href=der_href.root,
                                    DERStatusLink=m.DERStatusLink(der_href.der_status),
                                    DERSettingsLink=m.DERSettingsLink(der_href.der_settings),
                                    DERCapabilityLink=m.DERCapabilityLink(der_href.der_capability),
                                    DERAvailabilityLink=m.DERAvailabilityLink(
                                        der_href.der_availability))
                    adpt.ListAdapter.append(ed_href.der_list, der_obj)
                    current_min_primacy = 10000
                    current_der_program = None
                    for fsa in adpt.ListAdapter.get_list(ed_href.function_set_assignments):
                        for der_program in adpt.ListAdapter.get_list(fsa.DERProgramListLink.href):
                            if current_der_program is None:
                                current_der_program = der_program
                            if der_program.primacy < current_min_primacy:
                                current_min_primacy = der_program.primacy
                    der_obj.CurrentDERProgramLink = m.CurrentDERProgramLink(
                        current_der_program.href)

            else:

                # der_href will manage the url links to other lists/resources for the DER.
                der_href = hrefs.DERHref(ed_href.der_list)

                # Create a reference to the default der list. Add an entry for the end device as
                # a DER object.  Note these are all available for the client to read/write via
                # GET/PUT to/from the server.
                der_list = m.DERList(DER=[
                    m.DER(href=der_href.root,
                          DERStatusLink=m.DERStatusLink(der_href.der_status),
                          DERSettingsLink=m.DERSettingsLink(der_href.der_settings),
                          DERCapabilityLink=m.DERCapabilityLink(der_href.der_capability),
                          DERAvailabilityLink=m.DERAvailabilityLink(der_href.der_availability))
                ])
                adpt.ListAdapter.append(ed_href.der_list, der_list)
                current_min_primacy = 10000
                current_der_program = None
                for fsa in adpt.ListAdapter.get_list(ed_href.function_set_assignments):
                    for der_program in adpt.ListAdapter.get_list(fsa.DERProgramListLink.href):
                        if current_der_program is None:
                            current_der_program = der_program
                        if der_program.primacy < current_min_primacy:
                            current_min_primacy = der_program.primacy
                der_list.DER[0].CurrentDERProgramLink = m.CurrentDERProgramLink(
                    current_der_program.href)

    adpt.ListAdapter.print_all()
