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
    device_capability = m.DeviceCapability(href=str(hrefs.DeviceCapabilityHref(end_device_index)))
    device_capability.EndDeviceListLink = m.EndDeviceListLink(href=hrefs.DEFAULT_EDEV_ROOT, all=1)
    device_capability.DERProgramListLink = m.DERProgramListLink(href=hrefs.DEFAULT_DERP_ROOT,
                                                                all=0)
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

    # These links are to list entries not a single element.  These hrefs should
    # be used with the new apt.ListAdapter.
    device.DERListLink = m.DERListLink(href=ed_href.der_list)
    device.FunctionSetAssignmentsListLink = m.FunctionSetAssignmentsListLink(
        href=ed_href.function_set_assignments)
    device.LogEventListLink = m.LogEventListLink(href=ed_href.log_event_list)
    device.RegistrationLink = m.RegistrationLink(href=ed_href.registration)

    # Store objects in the href cache for retrieval.
    device.ConfigurationLink = m.ConfigurationLink(href=ed_href.configuration)
    add_href(ed_href.configuration, m.Configuration(href=ed_href.configuration))

    device.DeviceInformationLink = m.DeviceInformationLink(href=ed_href.device_information)
    add_href(ed_href.device_information, m.DeviceInformation(href=ed_href.device_information))

    device.DeviceStatusLink = m.DeviceStatusLink(href=ed_href.device_status)
    add_href(ed_href.device_status, m.DeviceStatus(href=ed_href.device_status))

    device.PowerStatusLink = m.PowerStatusLink(href=ed_href.device_power_status)
    add_href(ed_href.device_power_status, m.PowerStatus(href=ed_href.device_power_status))

    return device


def update_active_der_event_started(event: m.Event):
    """Event triggered when a DERControl event starts
    
    Find the control and copy it to the ActiveDERControlList

    :param event: The control event
    :type event: m.Event
    """

    assert type(event) == m.DERControl

    href_parser = hrefs.HrefParser(event.href)

    program = adpt.DERProgramAdapter.fetch(href_parser.at(1))

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

    href_parser = hrefs.HrefParser(event.href)

    program = adpt.DERProgramAdapter.fetch(href_parser.at(1))

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

    der_with_description = {}
    # Add DERs to the ListAdapter under the key hrefs.DEFAULT_DER_ROOT.
    # Add individual DER items to the href structure for retrieval.
    for index, cfg_der in enumerate(config.ders):
        program = cfg_der.pop("program", None)
        description = cfg_der.pop("description")
        der_href = hrefs.DERHref(hrefs.SEP.join([hrefs.DEFAULT_DER_ROOT, str(index)]))
        der_obj = m.DER(href=der_href.root, **cfg_der)
        der_obj.DERAvailabilityLink = m.DERAvailabilityLink(der_href.der_availability)
        add_href(der_href.der_availability, m.DERAvailability(href=der_href.der_availability))
        der_obj.DERCapabilityLink = m.DERCapabilityLink(der_href.der_capability)
        add_href(der_href.der_capability, m.DERCapability(href=der_href.der_capability))
        der_obj.DERSettingsLink = m.DERSettingsLink(der_href.der_settings)
        add_href(der_href.der_settings, m.DERSettings(href=der_href.der_settings))
        der_obj.DERStatusLink = m.DERStatusLink(der_href.der_status)
        add_href(der_href.der_status, m.DERStatus(href=der_href.der_status))
        der_with_description[description] = der_obj
        adpt.ListAdapter.append(hrefs.DEFAULT_DER_ROOT, der_obj)
        cfg_der["program"] = program
        cfg_der["description"] = description
        add_href(der_obj.href, der_obj)

    # Add DERCurves to the ListAdapter under the key hrefs.DEFAULT_CURVE_ROOT.
    for index, curve_cfg in enumerate(config.curves):
        curve = m.DERCurve(href=hrefs.SEP.join([hrefs.DEFAULT_CURVE_ROOT,
                                                str(index)]),
                           **curve_cfg)
        adpt.ListAdapter.append(hrefs.DEFAULT_CURVE_ROOT, curve)

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
                end_device_fsa[ed_href.function_set_assignments] = cfg_device.fsas
            if cfg_device.ders:
                # TODO DERS HERE!
                raise ValueError("DERS not implemented")
                # Create references from the main der list to the ed specific list.
                for der_description in cfg_device.ders:
                    der_item = adpt.ListAdapter.get_item_by_prop(hrefs.DEFAULT_DER_ROOT,
                                                                 "description", der_description)
                    adpt.ListAdapter.append(ed_href.der_list, der_item)

                # add_href(
                #     ed_href.der_list
                #     m.DERList(href=ed_href.der_list,
                #               all=len(cfg_device.ders),
                #               DER=adpt.ListAdapter.get_list(ed_href.der_list))
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

    for index, program_cfg in enumerate(config.programs):
        program = adpt.DERProgramAdapter.fetch_by_href(hrefs.der_program_href(index))
        if program is not None:
            _log.warning(f"Updating existing program {hrefs.der_program_href(index)}")
        else:
            devices_cfg = program_cfg.pop("devices", [])
            default_der_control = program_cfg.pop("DefaultDERControl", None)
            der_controls = program_cfg.pop("DERControls", None)

            program = m.DERProgram(href=hrefs.der_program_href(index), **program_cfg)
            program = adpt.DERProgramAdapter.add(program)
            for der in config.ders:
                if der["program"] == program.description:
                    der_obj = adpt.ListAdapter.get_item_by_prop(hrefs.DEFAULT_DER_ROOT,
                                                                "description", der["description"])
                    der_obj.CurrentDERProgramLink = m.CurrentDERProgramLink(program.href)
                    add_href(der_obj.href, der_obj)

                    for index, ed in enumerate(config.devices):
                        # Need to update the add_href link to the updated der list.
                        for cfg_program in ed.programs:
                            if cfg_program == program.description:
                                ed_href = hrefs.EndDeviceHref(index)
                                add_href(
                                    ed_href.der_list,
                                    m.DERList(href=ed_href.der_list,
                                              all=len(cfg_device.ders),
                                              DER=adpt.ListAdapter.get_list(ed_href.der_list)))

            if default_der_control is not None:
                default_der_control_href = program.href + hrefs.SEP + "dderc"
                der_control_base = None
                if "DERControlBase" in default_der_control:
                    der_control_base = default_der_control.pop("DERControlBase")
                default_der_control = m.DefaultDERControl(href=default_der_control_href,
                                                          **default_der_control)
                if der_control_base:
                    default_der_control.DERControlBase = m.DERControlBase(**der_control_base)
                add_href(default_der_control_href, default_der_control)
                program.DefaultDERControlLink = m.DefaultDERControlLink(
                    href=default_der_control_href)

            der_control_list = m.DERControlList(
                href=program.href + hrefs.SEP + "derc",
                all=0 if der_controls is None else len(der_controls))
            if der_controls is not None:
                for derc_index, der_control in enumerate(der_controls):
                    derc_href = program.href + hrefs.SEP + "derc" + hrefs.SEP + str(derc_index)
                    der_control_list.DERControl.append(m.DERControl(href=derc_href, **der_control))

            add_href(der_control_list.href, der_control_list)
            program.DERControlListLink = m.DERControlListLink(href=der_control_list.href,
                                                              all=der_control_list.all)

            active_control_list_href = program.href + hrefs.SEP + "dera"
            active_control_list = m.DERControlList(href=active_control_list_href,
                                                   all=0,
                                                   DERControl=[])
            add_href(active_control_list_href, active_control_list)
            program.ActiveDERControlListLink = m.ActiveDERControlListLink(
                href=active_control_list_href, all=0)

            program.DERCurveListLink = m.DERCurveListLink(href=hrefs.curve_href(),
                                                          all=adpt.DERCurveAdapter.size())

            program.primacy = "0"

    for index, fsa in enumerate(config.fsa):
        fsa_obj = adpt.FunctionSetAssignmentsAdapter.fetch_by_href(hrefs.fsa_href(index))

        if fsa_obj is not None:
            _log.warning(f"Updating existing function set assignments {hrefs.fsa_href(index)}")
        else:
            programs_cfg = fsa.pop("programs", [])
            fsa_obj = m.FunctionSetAssignments(hrefs.fsa_href(index), **fsa)
            fsa_programs = []
            for prg in program_cfg.values():
                program = adpt.DERProgramAdapter.fetch_by_property("description", prg)
                if program:
                    fsa_programs.append(program)
            fsa_obj = adpt.FunctionSetAssignmentsAdapter.add(fsa_obj)

            if fsa_programs:
                fsa_der_href = end_device.href + hrefs.SEP + "fsa" + hrefs.SEP + str(index)
                fsa_obj.DERProgramListLink = m.DERProgramListLink(href=fsa_der_href,
                                                                  all=len(fsa_programs))
                add_href(
                    fsa_der_href,
                    m.DERProgramList(href=fsa_der_href,
                                     DERProgram=fsa_programs,
                                     all=len(fsa_programs)))

    for href, fsaptr in end_device_fsa.items():
        fsa_list = m.FunctionSetAssignmentsList(href)
        for ptr in fsaptr:
            fsa_obj = adpt.FunctionSetAssignmentsAdapter.fetch_by_property("description", ptr)
            fsa_list.FunctionSetAssignments.append(fsa_obj)
        fsa_list.all = len(fsa_list.FunctionSetAssignments)
        add_href(href, fsa_list)

    # for href, derptr in end_device_ders.items():
    #     for index, ptr in enumerate(config.ders):
    #         der_href = hrefs.DERHref(hrefs.SEP.join([href, str(index)]))

    #         der_obj = adpt.DERAdapter.fetch_by_property("description", ptr)
    #         if der_obj is None:
    #             der_obj = m.DER(href=der_href.root)

    #         if 'program' in ptr:
    #             program = adpt.DERProgramAdapter.fetch_by_property("description", ptr['program'])
    #             if program is not None:
    #                 der_obj.CurrentDERProgramLink = m.CurrentDERProgramLink(program.href)

    #         der_obj.DERAvailabilityLink = m.DERAvailabilityLink(der_href.der_availability)
    #         der_obj.DERCapabilityLink = m.DERCapabilityLink(der_href.der_capability)
    #         der_obj.DERSettingsLink = m.DERSettingsLink(der_href.der_settings)
    #         der_obj.DERStatusLink = m.DERStatusLink(der_href.der_status)
