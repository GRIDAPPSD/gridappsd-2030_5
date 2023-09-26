from __future__ import annotations

import logging

# from ieee_2030_5.adapters import BaseAdapter
from ieee_2030_5.certs import TLSRepository, lfdi_from_fingerprint
from ieee_2030_5.config import ServerConfiguration
from ieee_2030_5.data.indexer import add_href
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
    device_capability.DERProgramListLink = m.DERProgramListLink(href=hrefs.DEFAULT_DERP_ROOT, all=0)
    device_capability.MirrorUsagePointListLink = m.MirrorUsagePointListLink(href=hrefs.DEFAULT_MUP_ROOT, all=0)
    device_capability.TimeLink = m.TimeLink(href=hrefs.DEFAULT_TIME_ROOT)
    device_capability.UsagePointListLink = m.UsagePointListLink(href=hrefs.DEFAULT_UPT_ROOT, all=0)
    
    adpt.DeviceCapabilityAdapter.add(device_capability)
    return device_capability
    

def add_enddevice(device: m.EndDevice) -> m.EndDevice:
    """ Add an enddevice to the enddevice adapter and the device capability adapter.
    
    All links are filled out to the end device.
    """
    device = adpt.EndDeviceAdapter.add(device)
    device = update_enddevice_links(device)
    # Retrieve the index
    index = int(device.href.split(hrefs.SEP)[1])
    
    
    _log.debug(f"Added {device.href}")
    

def update_enddevice_links(device: m.EndDevice) -> m.EndDevice:
    index = int(device.href.split(hrefs.SEP)[1])
    ed_href = hrefs.EndDeviceHref(index)
    device.DERListLink = m.DERListLink(href=ed_href.der_list)
    device.ConfigurationLink = m.ConfigurationLink(href=ed_href.configuration)
    add_href(ed_href.configuration, m.Configuration(href=ed_href.configuration))
    device.DeviceInformationLink = m.DeviceInformationLink(href=ed_href.device_information)
    add_href(ed_href.device_information, m.DeviceInformation(href=ed_href.device_information))
    device.DeviceStatusLink = m.DeviceStatusLink(href=ed_href.device_status)
    add_href(ed_href.device_status, m.DeviceStatus(href=ed_href.device_status))
    device.FunctionSetAssignmentsListLink = m.FunctionSetAssignmentsListLink(href=ed_href.function_set_assignments)
    device.PowerStatusLink = m.PowerStatusLink(href=ed_href.device_power_status)
    add_href(ed_href.device_power_status, m.PowerStatus(href=ed_href.device_power_status))
    device.LogEventListLink = m.LogEventListLink(href=ed_href.log_event_list)
    add_href(ed_href.log_event_list, m.LogEventList(href=ed_href.log_event_list))
    device.RegistrationLink = m.RegistrationLink(href=ed_href.registration)
    adpt.EndDeviceAdapter.put(index, device)
    return device

    



def initialize_2030_5(config: ServerConfiguration, tlsrepo: TLSRepository):
    """Initialize the 2030.5 server.  
    
    This method initializes the adapters from the configuration objects into
    the persistence adapters.
    """
    _log.debug("Initializing 2030.5")
    _log.debug("Adding server level urls to cache")
    
    end_device_fsa = {}
    end_device_ders = {}
    
    if config.cleanse_storage:
        adpt.clear_all_adapters()
    
    for index, cfg_device in enumerate(config.devices):
        
        create_device_capability(index)
        ed_href = hrefs.EndDeviceHref(index)
        end_device = adpt.EndDeviceAdapter.fetch_by_href(str(ed_href))
        if end_device is not None:
            _log.warning(f"End device {cfg_device.id} already exists.  Updating lfdi, sfdi, and postRate.")
            end_device.lFDI = tlsrepo.lfdi(cfg_device.id)
            end_device.sFDI = tlsrepo.sfdi(cfg_device.id)
            end_device.postRate = cfg_device.post_rate
            adpt.EndDeviceAdapter.put(index, end_device)
        else:
            _log.debug(f"Adding end device {cfg_device.id} to server")
            end_device = m.EndDevice(lFDI=tlsrepo.lfdi(cfg_device.id),
                                    sFDI=tlsrepo.sfdi(cfg_device.id),
                                    postRate=cfg_device.post_rate,
                                    enabled=True)
            add_enddevice(end_device)
            reg = m.Registration(href=end_device.RegistrationLink.href, 
                                                        pIN=cfg_device.pin, 
                                                        pollRate=cfg_device.poll_rate)
            adpt.RegistrationAdapter.add(reg)
            add_href(reg.href, reg)
            if cfg_device.fsas is not None:
                end_device_fsa[ed_href.function_set_assignments] = cfg_device.fsas
            if cfg_device.ders is not None:
                end_device_ders[ed_href.der_list] = cfg_device.ders
    
    
    for index, curve_cfg in enumerate(config.curves):
        curve = adpt.DERCurveAdapter.fetch_by_href(hrefs.curve_href(index))
        if curve is not None:
            _log.warning(f"Updating existing curve {hrefs.curve_href(index)}.")
        else:
            curve = m.DERCurve(href=m.DERCurveLink(hrefs.curve_href(index)), **curve_cfg)
            adpt.DERCurveAdapter.add(curve)
            
        add_href(hrefs.curve_href(), adpt.DERCurveAdapter.fetch_all(m.DERCurveList(href=hrefs.curve_href(), all=adpt.DERCurveAdapter.size())))
        

    for index, program_cfg in enumerate(config.programs):
        program = adpt.DERProgramAdapter.fetch_by_href(hrefs.der_program_href(index))
        if program is not None:
            _log.warning(f"Updating existing program {hrefs.der_program_href(index)}")
        else:
            devices_cfg = program_cfg.pop("devices", [])
            default_der_control = program_cfg.pop("DefaultDERControl", None)
            der_controls = program_cfg.pop("DERControls", None)
            
            program = m.DERProgram(href=hrefs.der_program_href(index),
                                   **program_cfg)
            program = adpt.DERProgramAdapter.add(program)
            
            if default_der_control is not None:
                default_der_control_href = program.href + hrefs.SEP + "dderc"
                default_der_control = m.DefaultDERControl(href=default_der_control_href, **default_der_control)
                add_href(default_der_control_href, default_der_control)
                program.DefaultDERControlLink = m.DefaultDERControlLink(href=default_der_control_href)
            
            if der_controls is not None:
                der_control_list = m.DERControlList(href=program.href + hrefs.SEP + "derc", all=len(der_controls))
                for derc_index, der_control in enumerate(der_controls):
                    derc_href = program.href + hrefs.SEP + "derc" + hrefs.SEP + str(derc_index)
                    der_control_list.DERControl.append(m.DERControl(href=derc_href, **der_control))
                
                add_href(der_control_list.href, der_control_list)
                program.DERControlListLink = m.DERControlListLink(href=der_control_list.href, all=der_control_list.all)

            active_control_list_href = program.href + hrefs.SEP + "dera"
            active_control_list = m.DERControlList(href=active_control_list_href, all=0, DERControl=[])
            add_href(active_control_list_href, active_control_list)
            program.ActiveDERControlListLink = m.ActiveDERControlListLink(href=active_control_list_href, all=0)
            
            program.DERCurveListLink = m.DERCurveListLink(href=hrefs.curve_href(), all=adpt.DERCurveAdapter.size())
            
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
                fsa_obj.DERProgramListLink = m.DERProgramListLink(href=fsa_der_href, all=len(fsa_programs))
                add_href(fsa_der_href, m.DERProgramList(href=fsa_der_href, DERProgram=fsa_programs, all=len(fsa_programs)))
                
            
            
            
    for href, fsaptr in end_device_fsa.items():
        fsa_list = m.FunctionSetAssignmentsList(href)
        for ptr in fsaptr:
            fsa_obj = adpt.FunctionSetAssignmentsAdapter.fetch_by_property("description", ptr)
            fsa_list.FunctionSetAssignments.append(fsa_obj)
        fsa_list.all = len(fsa_list.FunctionSetAssignments)
        add_href(href, fsa_list)
    
    for href, derptr in end_device_ders.items():
        der_list = m.DERList(href)
        for index, ptr in enumerate(config.ders):
            der_href = hrefs.DERHref(hrefs.SEP.join([href, str(index)]))
            
            der_obj = adpt.DERAdapter.fetch_by_property("description", ptr)
            if der_obj is None:
                der_obj = m.DER(href=der_href.root)
            
            if 'program' in ptr:
                program = adpt.DERProgramAdapter.fetch_by_property("description", ptr['program'])
                if program is not None:
                    der_obj.CurrentDERProgramLink = m.CurrentDERProgramLink(program.href)
            #der_obj.CurrentDERProgramLink = m.CurrentDERProgramLink(der_href.der_current_program)
            der_obj.DERAvailabilityLink = m.DERAvailabilityLink(der_href.der_availability)
            der_obj.DERCapabilityLink = m.DERCapabilityLink(der_href.der_capability)
            der_obj.DERSettingsLink = m.DERSettingsLink(der_href.der_settings)
            der_obj.DERStatusLink = m.DERStatusLink(der_href.der_status)
            der_list.DER.append(der_obj)
        der_list.all = len(der_list.DER)
        add_href(href, der_list)
    
